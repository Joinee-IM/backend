import aiosmtplib
import aiosmtplib.smtp

from app.base import mcs
from app.config import SMTPConfig


class SMTPHandler(metaclass=mcs.Singleton):
    def __init__(self):
        self._client: aiosmtplib.SMTP = None  # Need to be init/closed manually # noqa

    async def initialize(self, smtp_config: SMTPConfig):
        if self._client is None:
            self._client = aiosmtplib.SMTP(
                hostname=smtp_config.host,
                port=smtp_config.port,
                username=smtp_config.username,
                password=smtp_config.password,
                use_tls=smtp_config.use_tls,
            )

    async def close(self):
        if self._client is not None:
            self._client.close()

    async def send_message(
            self,
            message: aiosmtplib.smtp.Union[
                aiosmtplib.smtp.email.message.EmailMessage,
                aiosmtplib.smtp.email.message.Message,
            ],
            sender: str | None = None,
            recipients: aiosmtplib.smtp.Union[str, aiosmtplib.smtp.Sequence[str]] | None = None,
            mail_options: aiosmtplib.smtp.Iterable[str] | None = None,
            rcpt_options: aiosmtplib.smtp.Iterable[str] | None = None,
            timeout: aiosmtplib.smtp.Union[float, aiosmtplib.smtp.Default] | None = aiosmtplib.smtp._default,  # noqa
    ):
        client = await self.get_client()
        responses, _ = await client.send_message(
            message, sender=sender, recipients=recipients,
            mail_options=mail_options, rcpt_options=rcpt_options,
            timeout=timeout,
        )
        for address, (code, resp) in responses.items():
            if code != 200:
                print(f'{address=} failed with {code=} {resp=}')  # experimental, info level only

    async def get_client(self):
        try:
            await self._client.noop()
        except aiosmtplib.errors.SMTPServerDisconnected as e:
            try:
                await self._client.connect()
            except Exception as e2:
                raise e2 from e

            try:
                await self._client.noop()  # verify
            except Exception as e2:
                raise e2 from e

        return self._client


smtp_handler = SMTPHandler()


from . import forget_password, invitation, verification
