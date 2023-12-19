from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from app.config import service_config, smtp_config
from app.persistence.email import smtp_handler


async def send(meet_code: str, to: str | None = None, subject='Invitation from Jöinee', bcc: str | None = None):
    message = MIMEMultipart()
    message['From'] = 'Jöinee'
    message['Subject'] = subject
    if to is not None:
        message["To"] = to
    if bcc is not None:
        message["Bcc"] = bcc
    body = f"""
        <html>
            <body>
                <p style="color: black;">Hello,</p>
                <p style="color: black;">You are invited to the reservation on Jöinee.</p>
                <p style="color: black;">Click the link to join the reservation!</p>
                <a href="{service_config.url}/reservation/{meet_code}">Click here to join the reservation!</a>
            </body>
        </html>
        """
    message.attach(MIMEText(body, 'html'))
    await smtp_handler.send_message(message)
