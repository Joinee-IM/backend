from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from app.config import service_config, smtp_config
from app.persistence.email import smtp_handler


async def send(to: str, code: str, subject='Jöinee reset password verification'):
    message = MIMEMultipart()
    message['From'] = 'Jöinee'
    message['To'] = to
    message['Subject'] = subject
    body = f"""
            <html>
                <body>
                    <p style="color: black;">Hello,</p>
                    <p style="color: black;">Please click on the following link to reset your password.</p>
                    <a href="{service_config.url}/auth/forget-password/reset-password?code={code}">Click here to reset password.</a>
                </body>
            </html>
            """
    # link to FE reset password page, not BE
    message.attach(MIMEText(body, 'html'))
    await smtp_handler.send_message(message)
