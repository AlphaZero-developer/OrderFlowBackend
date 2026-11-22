import jwt
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.schemas.user import UserOut, AutorizationToken
from app.repositories.users import UsersRepository
from app.core.security import hash_password, verify_password
from app.jwt_token.user_token import create_token, decode_token
from app.exceptions.exceptions import ConflictError, UnauthorizedError


class UsersService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.user_repository = UsersRepository(db)

    def register_user(self, name: str, email: str, password: str) -> UserOut:

        email = email.lower()

        if self.user_repository.get_user_by_email(email) is not None:
            raise ConflictError("Email уже зарегистрирован")

        user = self.user_repository.register(name, email, hash_password(password))

        try:
            self.db.commit()
        except IntegrityError:
            self.db.rollback()
            raise ConflictError("Email уже зарегистрирован")

        self.db.refresh(user)
        return UserOut.model_validate(user)

    def login_user(self, email: str, password: str) -> AutorizationToken:

        user = self.user_repository.get_user_by_email(email.lower())

        if user is None or not verify_password(
            password=password, hashed=user.password_hash
        ):
            raise UnauthorizedError("Неверная почта или пароль")

        return AutorizationToken(access_token=create_token(user.id))

    def get_me_user(self, access_token: str) -> UserOut:

        user = self.user_repository.get_user_by_id(decode_token(access_token))

        if user is None:
            raise UnauthorizedError()

        return UserOut.model_validate(user)
