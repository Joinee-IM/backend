from fastapi import APIRouter, responses

router = APIRouter(
    tags=['Reservation'],
    default_response_class=responses.JSONResponse,
)
