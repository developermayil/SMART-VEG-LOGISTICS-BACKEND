from beanie import Document
from pydantic import Field
from typing import Optional
from datetime import datetime


class Farmer(Document):
    name: str
    village: str
    district: str = "Tamil Nadu"
    phone: str
    alternate_phone: str = ""
    email: str = ""
    bank_account: str = ""
    ifsc_code: str = ""
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "farmers"
