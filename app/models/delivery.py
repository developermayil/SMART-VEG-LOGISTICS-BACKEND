from beanie import Document
from pydantic import BaseModel, Field
from typing import Optional, List, Literal
from datetime import datetime


DeliveryStatus = Literal["pending", "in-transit", "delivered", "cancelled"]


class DeliveryItem(BaseModel):
    stock_id: str
    quantity: float
    price_per_unit: float
    selling_price: Optional[float] = None


class Delivery(Document):
    delivery_number: str
    vehicle_id: str               # ObjectId ref as string
    destination: str
    destination_market: str = ""
    total_quantity: float = 0
    total_value: float = 0
    status: DeliveryStatus = "pending"
    scheduled_date: Optional[datetime] = None
    delivered_date: Optional[datetime] = None
    driver_notes: str = ""
    items: List[DeliveryItem] = []
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "deliveries"
