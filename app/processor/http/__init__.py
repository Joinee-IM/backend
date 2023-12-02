import fastapi


def register_routers(app: fastapi.FastAPI):
    from . import (
        account,
        album,
        business_hour,
        city,
        court,
        district,
        google,
        public,
        reservation,
        sport,
        stadium,
        venue,
        view,
    )

    app.include_router(public.router)
    app.include_router(account.router)
    app.include_router(google.router)
    app.include_router(stadium.router)
    app.include_router(city.router)
    app.include_router(venue.router)
    app.include_router(district.router)
    app.include_router(album.router)
    app.include_router(sport.router)
    app.include_router(reservation.router)
    app.include_router(court.router)
    app.include_router(business_hour.router)
    app.include_router(view.router)
