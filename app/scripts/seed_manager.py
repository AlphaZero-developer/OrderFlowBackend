import os
from sqlalchemy import select

from app.models.user import UserORM
from app.db.sessions import sessionlocal
from app.core.security import hash_password


def seed_manager() -> None:
    email = os.environ["MANAGER_EMAIL"]
    password = os.environ["MANAGER_PASSWORD"]

    with sessionlocal() as db:
        existing_user = db.scalar(select(UserORM).where(UserORM.email == email))

        if existing_user:
            if existing_user.role != "manager":
                raise RuntimeError("Email already belongs to a client")
            return

        manager = UserORM(
            name="Administator",
            email=email,
            password_hash=hash_password(password),
            role="manager",
        )
        db.add(manager)
        db.commit()


if __name__ == "__main__":
    seed_manager()
