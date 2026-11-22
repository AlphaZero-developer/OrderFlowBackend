from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime


class Order(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    owner_id: str
    title: str = Field(min_length=5, max_length=120)
    description: str = Field(min_length=20, max_length=2000)
    budget_rub: int
    status: str
    created_at: datetime
    updated_at: datetime


class OrderCreateSchema(BaseModel):
    title: str = Field(min_length=5, max_length=120)
    description: str = Field(min_length=20, max_length=2000)
    budget_rub: int


class OrderUpgradeSchema(BaseModel):
    status: str
