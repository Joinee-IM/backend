from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from app.config import service_config, smtp_config
from app.persistence.email import smtp_handler


async def send(to: str, meet_code: str, subject='Invitation from Joinee'):
    message = MIMEMultipart()
    message['From'] = f'{smtp_config.username}@{smtp_config.host}'
    message['To'] = to
    message['Subject'] = subject
    body = f"""
        <html>
            <body>
                <p style="color: black;">Hello,</p>
                <p style="color: black;">You are invited to the reservation on Joinee.</p>
                <p style="color: black;">Click the link to join the reservation!</p>
                <a href="{service_config.url}/reservation/{meet_code}">Click here to join the reservation!</a>
            </body>
        </html>
        """
    message.attach(MIMEText(body, 'html'))
    await smtp_handler.send_message(message)
