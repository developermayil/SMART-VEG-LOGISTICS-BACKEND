from beanie import Document, Link
from pydantic import Field
from typing import Optional
from datetime import datetime
from bson import ObjectId


class Stock(Document):
    vegetable: str
    quantity: float
    unit: str = "kg"
    price_per_unit: float
    farmer_id: Optional[str] = None   # stored as string ObjectId ref
    purchase_date: datetime = Field(default_factory=datetime.utcnow)
    notes: str = ""
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "stocks"
