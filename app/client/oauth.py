from authlib.integrations.starlette_client import OAuth

from app.base import mcs
from app.config import GoogleConfig


class OAuthHandler(metaclass=mcs.Singleton):
    def __init__(self):
        self.oauth = None
        self.login_redirect_url = None

    def initialize(self, google_config: GoogleConfig):
        self.oauth = OAuth()
        self.oauth.register(
            name='google',
            server_metadata_url=google_config.SERVER_URL,
            client_id=google_config.CLIENT_ID,
            client_secret=google_config.CLIENT_SECRET,
            client_kwargs={
                'scope': google_config.CLIENT_KWARGS,
            },
        )
        self.login_redirect_url = google_config.LOGIN_REDIRECT_URI

    async def login(self, request, access_type: str = 'offline', prompt: str = 'consent'):
        return await self.oauth.google.authorize_redirect(
            request, self.login_redirect_url,
            access_type=access_type, prompt=prompt,
        )

    async def authorize_access_token(self, request):
        return await self.oauth.google.authorize_access_token(request)


oauth_handler = OAuthHandler()
