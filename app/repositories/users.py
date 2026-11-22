from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models.user import UserORM


class UsersRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def register(self, name: str, email: str, password_hash: str) -> UserORM:
        new_user = UserORM(name=name, email=email, password_hash=password_hash)
        self.db.add(new_user)
        return new_user

    def get_user_by_id(self, id: str) -> UserORM | None:
        return self.db.scalar(select(UserORM).where(UserORM.id == id))

    def get_user_by_email(self, email: str) -> UserORM | None:
        return self.db.scalar(select(UserORM).where(UserORM.email == email))
