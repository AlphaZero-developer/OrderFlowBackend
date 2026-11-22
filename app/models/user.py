from uuid import uuid4
from datetime import datetime
from app.models.base import Base
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import DateTime, func


class UserORM(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(
        "id_user", primary_key=True, default=lambda: str(uuid4())
    )
    name: Mapped[str] = mapped_column(default="")
    email: Mapped[str] = mapped_column(unique=True, index=True)
    password_hash: Mapped[str] = mapped_column()
    role: Mapped[str] = mapped_column(default="client")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
