import fastapi
from fastapi.openapi.utils import get_openapi
from fastapi.responses import HTMLResponse


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

    # noinspection PyUnresolvedReferences
    @app.get("/api/openapi.json", include_in_schema=False)
    async def access_openapi():
        openapi = get_openapi(
            title=app.title,
            version=app.version,
            description=app.description,
            routes=app.routes,
            tags=app.openapi_tags,
        )
        openapi["servers"] = [{"url": app.root_path}]
        return openapi

    @app.get('/', include_in_schema=False, response_class=HTMLResponse)
    async def health_check():
        return '<a href="/api/docs">/api/docs</a>'

    app.include_router(public.router, prefix='/api')
    app.include_router(account.router, prefix='/api')
    app.include_router(google.router)  # no api prefix since google login can't allow /api for some unknown reason
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
