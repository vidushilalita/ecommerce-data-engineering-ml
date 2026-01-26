from pydantic import BaseModel, Field, EmailStr
from typing import Optional, Literal
from datetime import datetime

class UserCreate(BaseModel):
    user_id: int
    age: int = Field(..., gt=0)
    gender: Literal['M', 'F']
    device: Literal['Mobile', 'Desktop', 'Tablet']

class TransactionCreate(BaseModel):
    user_id: int
    item_id: int
    view_mode: Literal['view', 'add_to_cart', 'purchase']
    rating: Optional[int] = Field(None, ge=1, le=5)
    timestamp: Optional[datetime] = Field(default_factory=datetime.now)
