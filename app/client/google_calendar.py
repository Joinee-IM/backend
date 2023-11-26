from typing import Sequence

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from pydantic import BaseModel, NaiveDatetime

import app.persistence.database as db
from app.config import GoogleConfig


class GoogleCalendar:
    def __init__(self, account_id):
        self.id = account_id
        self.service = None

    async def build_connection(self):
        access_token, refresh_token = await db.account.get_google_token(account_id=self.id)
        token_dict = {'access_token': access_token, 'refresh_token': refresh_token,
                      'client_id': GoogleConfig.CLIENT_ID, 'client_secret': GoogleConfig.CLIENT_SECRET, }
        scopes = ["https://www.googleapis.com/auth/calendar"]
        creds = Credentials.from_authorized_user_info(token_dict, scopes)
        if not creds.valid:
            creds.refresh(Request())
        self.service = build('calendar', 'v3', credentials=creds)

    async def add_calendar_event(self, data):
        event = {
            'summary': data.summary,
            'location': data.stadium_name,
            'start': {
                'dateTime': str(data.start_time),
                'timeZone': 'Asia/Taipei',
            },
            'end': {
                'dateTime': str(data.end_time),
                'timeZone': 'Asia/Taipei',
            },
            'attendees': [email.dict() for email in data.member_emails],
            'reminders': {
                'useDefault': False,
                'overrides': [
                    {'method': 'email', 'minutes': 24 * 60},
                    {'method': 'popup', 'minutes': 30},
                ],
            },
        }

        event = self.service.events().insert(calendarId='primary', body=event, sendUpdates="all").execute()
        # print('Event created: %s' % (event.get('htmlLink')))


class Email(BaseModel):
    email: str


class AddEventInput(BaseModel):
    start_time: NaiveDatetime
    end_time: NaiveDatetime
    member_emails: Sequence[Email]
    stadium_name: str
    summary: str


async def add_google_calendar_event(start_time: NaiveDatetime, end_time: NaiveDatetime, account_id: int, stadium_id: int, member_ids: Sequence[int] = []):
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

    calendar = GoogleCalendar(account_id=account_id)
    await calendar.build_connection()
    await calendar.add_calendar_event(data=event)
