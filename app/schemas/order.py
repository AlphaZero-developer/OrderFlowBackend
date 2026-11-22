from typing import Literal

from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime


class Order(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    owner_id: str
    title: str = Field(min_length=5, max_length=120)
    description: str = Field(min_length=20, max_length=2000)
    budget_rub: int = Field(ge=1000, le=500000)
    status: Literal["new", "in_progress", "ready", "completed", "canceled"]
    created_at: datetime
    updated_at: datetime


class OrderCreateSchema(BaseModel):
    title: str = Field(min_length=5, max_length=120)
    description: str = Field(min_length=20, max_length=2000)
    budget_rub: int = Field(ge=1000, le=500000)


class OrderUpgradeSchema(BaseModel):
    status: Literal["new", "in_progress", "ready", "completed", "canceled"]
