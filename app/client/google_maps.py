from typing import Tuple

import googlemaps

import app.exceptions as exc
from app.config import GoogleConfig, google_config


class GoogleMaps:
    def __init__(self, config: GoogleConfig):
        self.service = None
        self.config = config

    def build_connection(self) -> None:
        self.service = googlemaps.Client(key=self.config.API_KEY)

    def get_long_lat(self, address: str) -> Tuple[float, float]:
        if self.service is None:
            self.build_connection()

        geocode_result = self.service.geocode(address=address)

        try:
            if geocode_result[0]["geometry"]["location_type"] == "ROOFTOP":
                return geocode_result[0]["geometry"]["location"]["lng"], geocode_result[0]["geometry"]["location"]["lat"]
            else:
                raise exc.NotFound
        except (KeyError, IndexError):
            raise exc.NotFound


google_maps = GoogleMaps(config=google_config)
