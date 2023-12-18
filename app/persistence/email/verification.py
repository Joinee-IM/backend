from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from app.config import service_config, smtp_config
from app.persistence.email import smtp_handler


async def send(to: str, code: str, subject='Jöinee 帳號驗證'):
    message = MIMEMultipart()
    message['From'] = f'Jöinee'
    message['To'] = to
    message['Subject'] = subject
    body = f"""
                <html>
                    <body>
                        <p style="color: black;">您好，{to}</p>
                        <p style="color: black;">感謝您註冊我們的應用程式！</p>
                        <p style="color: black;">請點擊以下連結進行驗證。</p>
                        <a href="{service_config.url}/auth/signup/verified?code={code}">點擊這裡進行驗證</a>
                    </body>
                </html>
            """
    message.attach(MIMEText(body, 'html'))
    await smtp_handler.send_message(message)
