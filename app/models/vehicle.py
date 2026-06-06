from beanie import Document
from pydantic import Field
from typing import Literal
from datetime import datetime


VehicleStatus = Literal["available", "in-transit", "maintenance"]


class Vehicle(Document):
    vehicle_number: str
    vehicle_type: str = "Truck"
    driver_name: str
    driver_phone: str
    driver_license: str = ""
    capacity: float
    status: VehicleStatus = "available"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "vehicles"
