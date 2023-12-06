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

    app.include_router(public.router, prefix='/api')
    app.include_router(account.router, prefix='/api')
    app.include_router(google.router)
    app.include_router(stadium.router, prefix='/api')
    app.include_router(city.router, prefix='/api')
    app.include_router(venue.router, prefix='/api')
    app.include_router(district.router, prefix='/api')
    app.include_router(album.router, prefix='/api')
    app.include_router(sport.router, prefix='/api')
    app.include_router(reservation.router, prefix='/api')
    app.include_router(court.router, prefix='/api')
    app.include_router(business_hour.router, prefix='/api')
    app.include_router(view.router, prefix='/api')
