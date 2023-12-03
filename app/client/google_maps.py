import googlemaps
from app.config import GoogleConfig, google_config


class GoogleMaps:
    def __init__(self, config: GoogleConfig):
        self.service = None
        self.config = config

    def build_connection(self):
        self.service = googlemaps.Client(client_id=self.config.CLIENT_ID, client_secret=self.config.CLIENT_SECRET)

    def get_long_lat(self, address: str):
        geocode_result = self.service.geocode(address=address)
        return geocode_result["geometry"]["location"]["lng"], geocode_result["geometry"]["location"]["lat"]


google_maps = GoogleMaps(config=google_config)
