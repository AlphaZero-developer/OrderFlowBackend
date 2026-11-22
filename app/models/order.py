from uuid import uuid4
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime
from sqlalchemy import DateTime, func
from app.models.base import Base


class OrderORM(Base):
    __tablename__ = "orders"

    id: Mapped[str] = mapped_column(
        "id_order", primary_key=True, default=lambda: str(uuid4())
    )
    owner_id: Mapped[str] = mapped_column()
    title: Mapped[str] = mapped_column()
    description: Mapped[str] = mapped_column()
    budget_rub: Mapped[int] = mapped_column()
    status: Mapped[str] = mapped_column(default="new")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
