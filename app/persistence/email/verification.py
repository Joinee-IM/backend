from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from app.config import service_config, smtp_config
from app.persistence.email import smtp_handler


async def send(to: str, code: str, subject='Joinee Email Verification'):
    message = MIMEMultipart()
    message['From'] = f'{smtp_config.username}@{smtp_config.host}'
    message['To'] = to
    message['Subject'] = subject
    body = f"""
                <html>
                    <body>
                        <p style="color: black;">Hello, {to}</p>
                        <p style="color: black;">Thanks for registering for our application.</p>
                        <p style="color: black;">Please click on the following link to verify!</p>
                        <a href="{service_config.url}/auth/login?code={code}">Click here to verify</a>
                    </body>
                </html>
            """
    message.attach(MIMEText(body, 'html'))
    await smtp_handler.send_message(message)
