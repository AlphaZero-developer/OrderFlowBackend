from pydantic import BaseModel, ConfigDict, EmailStr, Field
from datetime import datetime


class UserRegister(BaseModel):
    name: str = Field(min_length=2, max_length=50)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class UserAutorization(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class AutorizationToken(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    name: str
    email: str
    role: str
    created_at: datetime
