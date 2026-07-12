from beanie import Document
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from datetime import datetime
from bson import ObjectId


OrderStatus = str


class OrderItem(BaseModel):
    product_name: str
    quantity: float
    price: float


class Order(Document):
    order_number: Optional[str] = None
    customer_id: str              # ObjectId ref as string
    items: List[OrderItem] = []
    total_amount: float
    status: OrderStatus = "pending"
    notes: str = ""
    created_date: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    @field_validator("customer_id", mode="before")
    @classmethod
    def convert_customer_id(cls, v):
        if isinstance(v, ObjectId):
            return str(v)
        return v

    class Settings:
        name = "orders"