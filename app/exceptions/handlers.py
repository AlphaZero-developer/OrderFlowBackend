import jwt
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.exceptions.exceptions import AppError


async def app_error_handler(request: Request, exception: AppError) -> JSONResponse:
    if not isinstance(exception, AppError):
        raise exception
    return JSONResponse(
        status_code=exception.status_code, content={"detail": exception.detail}
    )


async def unvalid_token(
    request: Request, exception: jwt.InvalidTokenError
) -> JSONResponse:
    if not isinstance(exception, jwt.InvalidTokenError):
        raise exception
    return JSONResponse(status_code=401, content={"detail": "Недействительный токен"})


def register_exception_token(app: FastAPI) -> None:
    app.add_exception_handler(AppError, app_error_handler)
    app.add_exception_handler(jwt.InvalidTokenError, unvalid_token)
