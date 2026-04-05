from pydantic import BaseModel, EmailStr
from typing import Optional

class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str
    role: str

class UserResponse(BaseModel):
    id: int
    name: str
    email: str
    role: str
    is_active: bool

    class Config:
        orm_mode = True

from pydantic import BaseModel
from datetime import date

class RecordCreate(BaseModel):
    amount: float
    type: str   # income / expense
    category: str
    date: date
    note: str | None = None


class RecordResponse(BaseModel):
    id: int
    amount: float
    type: str
    category: str
    date: date
    note: str | None

    class Config:
        orm_mode = True


class RecordUpdate(BaseModel):
    amount: Optional[float] = None
    type: Optional[str] = None
    category: Optional[str] = None
    date: Optional[date] = None
    note: Optional[str] = None