from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

import app.persistence.database as db
from app.config import GoogleConfig


class GoogleCalendar:
    def __init__(self, account_id):
        self.id = account_id
        self.service = None

    async def build_connection(self):
        access_token, refresh_token = await db.account.get_google_token(self.id)
        token_dict = {'access_token': access_token, 'refresh_token': refresh_token,
                      'client_id': GoogleConfig.GOOGLE_CLIENT_ID, 'client_secret': GoogleConfig.GOOGLE_CLIENT_SECRET}
        scopes = ["https://www.googleapis.com/auth/calendar"]
        creds = Credentials.from_authorized_user_info(token_dict, scopes)
        if not creds.valid:
            creds.refresh(Request())
        self.service = build('calendar', 'v3', credentials=creds)

    async def add_google_event(self, data):
        event = {
            'summary': data.summary,
            'location': data.stadium_name,
            'start': {
                'dateTime': data.start_time,
                'timeZone': 'Asia/Taipei',
            },
            'end': {
                'dateTime': data.end_time,
                'timeZone': 'Asia/Taipei',
            },
            'attendees': data.member_emails,
            'reminders': {
                'useDefault': False,
                'overrides': [
                    {'method': 'email', 'minutes': 24 * 60},
                    {'method': 'popup', 'minutes': 30},
                ],
            },
        }

        event = self.service.events().insert(calendarId='primary', body=event, sendUpdates="all").execute()
        print('Event created: %s' % (event.get('htmlLink')))
