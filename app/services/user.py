import jwt
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.schemas.user import UserOut, AutorizationToken
from app.repositories.users import UsersRepository
from app.core.security import hash_password, verify_password
from app.jwt_token.user_token import create_token, decode_token
from fastapi import HTTPException, status


class UsersService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.user_repository = UsersRepository(db)

    def register_user(self, name: str, email: str, password: str) -> UserOut:

        email = email.lower()

        if self.db is None:
            print("БД, не создана, либо не зарегистрирована")
            return

        if self.user_repository.get_user_by_email(email) is not None:
            raise HTTPException(status.HTTP_409_CONFLICT, "Email already registered")

        user = self.user_repository.register(name, email, hash_password(password))

        try:
            self.db.commit()
        except IntegrityError:
            self.db.rollback()
            raise HTTPException(status.HTTP_409_CONFLICT, "Email already registered")

        self.db.refresh(user)
        return UserOut.model_validate(user)

    def login_user(self, email: str, password: str) -> AutorizationToken:

        email = email.lower()

        user = self.user_repository.get_user_by_email(email)

        if user is None or not verify_password(
            password=password, hashed=user.password_hash
        ):
            raise HTTPException(
                status.HTTP_401_UNAUTHORIZED, "Неверная почта или пароль"
            )

        token = create_token(user.id)

        return AutorizationToken(access_token=token)

    def get_me_user(self, access_token: str) -> UserOut:

        try:
            user = self.user_repository.get_user_by_id(decode_token(access_token))
        except jwt.InvalidTokenError:
            raise HTTPException(status_code=401)

        if user is None:
            raise HTTPException(status_code=401)

        result = UserOut.model_validate(user)

        return result
