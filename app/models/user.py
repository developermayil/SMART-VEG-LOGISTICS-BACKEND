from beanie import Document
from pydantic import EmailStr, Field
from typing import Optional
from datetime import datetime


class User(Document):
    username: str
    email: EmailStr
    password: str
    role: str = "admin"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "users"
