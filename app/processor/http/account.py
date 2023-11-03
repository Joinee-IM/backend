from fastapi import APIRouter, Depends, responses

from app.middleware.headers import get_auth_token

router = APIRouter(
    tags=['Account'],
    default_response_class=responses.JSONResponse,
    dependencies=[Depends(get_auth_token)]
)
