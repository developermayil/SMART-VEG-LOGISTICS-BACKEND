from beanie import Document
from pydantic import BaseModel, Field
from typing import Optional, List, Literal
from datetime import datetime


OrderStatus = Literal["pending", "processing", "completed", "cancelled"]


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

    class Settings:
        name = "orders"
