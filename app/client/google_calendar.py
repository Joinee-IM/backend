from typing import Sequence

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from pydantic import BaseModel, NaiveDatetime

import app.persistence.database as db
from app.config import GoogleConfig, google_config


class Email(BaseModel):
    email: str


class AddEventInput(BaseModel):
    start_time: NaiveDatetime
    end_time: NaiveDatetime
    member_emails: Sequence[Email]
    stadium_name: str
    summary: str


class UpdateEventInput(BaseModel):
    event_id: str
    member_email: Email


class GoogleCalendar:
    def __init__(self, account_id: int, config: GoogleConfig):
        self.id = account_id
        self.service = None
        self.config = config

    async def build_connection(self):
        access_token, refresh_token = await db.account.get_google_token(account_id=self.id)
        token_dict = {
            'access_token': access_token, 'refresh_token': refresh_token,
            'client_id': self.config.CLIENT_ID, 'client_secret': self.config.CLIENT_SECRET,
        }
        scopes = ["https://www.googleapis.com/auth/calendar"]
        creds = Credentials.from_authorized_user_info(token_dict, scopes)
        if not creds.valid:
            creds.refresh(Request())
        self.service = build('calendar', 'v3', credentials=creds)

    def add_calendar_event(self, data: AddEventInput) -> dict:
        event = {
            'summary': data.summary,
            'location': data.stadium_name,
            'start': {
                'dateTime': data.start_time.isoformat(),
                'timeZone': 'Asia/Taipei',
            },
            'end': {
                'dateTime': data.end_time.isoformat(),
                'timeZone': 'Asia/Taipei',
            },
            'attendees': [email.model_dump() for email in data.member_emails],
            'reminders': {
                'useDefault': False,
                'overrides': [
                    {'method': 'email', 'minutes': 24 * 60},
                    {'method': 'popup', 'minutes': 30},
                ],
            },
        }

        event = self.service.events().insert(calendarId='primary', body=event, sendUpdates="all").execute()

        return event

    def update_calendar_event(self, data: UpdateEventInput) -> None:
        event = self.service.events().get(calendarId='primary', eventId=data.event_id).execute()

        attendees = event.get("attendees", [])
        attendees.append(data.member_email.model_dump())
        event['attendees'] = attendees

        self.service.events().update(calendarId='primary', eventId=data.event_id, body=event).execute()


async def add_google_calendar_event(
    reservation_id: int, start_time: NaiveDatetime, end_time: NaiveDatetime,
    account_id: int, stadium_id: int, member_ids: Sequence[int] = None,
):
    if not member_ids:
        member_ids = []

    # get stadium name
    stadium = await db.stadium.read(stadium_id=stadium_id)

    # get member emails
    member_emails = []
    for account_id in [*member_ids, account_id]:
        user = await db.account.read(account_id=account_id)
        member_emails.append(Email(email=user.email))

    event = AddEventInput(
        start_time=start_time, end_time=end_time,
        member_emails=member_emails, stadium_name=stadium.name,
        summary="[Joinee Reservation] Exercise",
    )

    calendar = GoogleCalendar(account_id=account_id, config=google_config)
    await calendar.build_connection()
    result = calendar.add_calendar_event(data=event)

    await db.reservation.add_event_id(reservation_id=reservation_id, event_id=result['id'])


async def update_google_calendar_event(
    reservation_id: int, member_id: int,
):
    reservation = await db.reservation.read(reservation_id=reservation_id)
    manager_id = await db.reservation.get_manager_id(reservation_id=reservation_id)
    member = await db.account.read(account_id=member_id)

    if reservation.google_event_id:
        calendar = GoogleCalendar(account_id=manager_id, config=google_config)
        await calendar.build_connection()
        calendar.update_calendar_event(
            data=UpdateEventInput(
                event_id=reservation.google_event_id,
                member_email=Email(email=member.email),
            ),
        )
