from fastapi.routing import APIRouter
from fastapi import Depends, status, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from app.schemas.user import UserRegister, UserOut, UserAutorization, AutorizationToken
from app.services.user import UsersService
from app.api.dependencies import get_user_service

router = APIRouter(prefix="/api/v1")

security = HTTPBearer(auto_error=False)


@router.post("/auth/register", status_code=status.HTTP_201_CREATED)
def register_user(
    payload: UserRegister, user_service: UsersService = Depends(get_user_service)
) -> UserOut:
    return user_service.register_user(
        name=payload.name, email=payload.email, password=payload.password
    )


@router.post("/auth/login", status_code=status.HTTP_200_OK)
def login_user(
    payload: UserAutorization, user_service: UsersService = Depends(get_user_service)
) -> AutorizationToken:
    return user_service.login_user(email=payload.email, password=payload.password)


@router.get("/auth/me", status_code=status.HTTP_200_OK)
def get_user_me(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    user_service: UsersService = Depends(get_user_service),
) -> UserOut:
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Токен отсутствует"
        )
    return user_service.get_me_user(credentials.credentials)
