from beanie import Document
from pydantic import Field
from typing import Optional
from datetime import datetime


class Customer(Document):
    name: str
    phone: str
    email: Optional[str] = None
    address: Optional[str] = None
    village: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "customers"
