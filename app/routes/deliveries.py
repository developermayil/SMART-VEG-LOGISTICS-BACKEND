from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, List, Literal
from datetime import datetime, date
from app.models.delivery import Delivery, DeliveryItem
from app.models.vehicle import Vehicle
from app.middleware.auth import get_current_user
import random

router = APIRouter(prefix="/api/deliveries", tags=["Deliveries"])


def _gen_delivery_number() -> str:
    d = datetime.utcnow()
    date_str = d.strftime("%Y%m%d")
    rand = str(random.randint(0, 999)).zfill(3)
    return f"SVL-{date_str}-{rand}"


class DeliveryItemBody(BaseModel):
    stock_id: str
    quantity: float
    price_per_unit: float
    selling_price: Optional[float] = None


class CreateDeliveryBody(BaseModel):
    vehicle_id: str
    destination: str
    destination_market: Optional[str] = ""
    scheduled_date: Optional[datetime] = None
    driver_notes: Optional[str] = ""
    items: Optional[List[DeliveryItemBody]] = []


class UpdateStatusBody(BaseModel):
    status: Literal["pending", "in-transit", "delivered", "cancelled"]
    delivered_date: Optional[datetime] = None
    driver_notes: Optional[str] = ""


@router.get("")
async def get_all_deliveries(_=Depends(get_current_user)):
    deliveries = await Delivery.find_all().sort("-created_at").to_list()
    data = []
    for d in deliveries:
        dd = d.model_dump()
        dd["id"] = str(d.id)
        # Populate vehicle
        vehicle = await Vehicle.get(d.vehicle_id)
        if vehicle:
            dd["vehicle"] = {"vehicle_number": vehicle.vehicle_number, "driver_name": vehicle.driver_name, "driver_phone": vehicle.driver_phone}
        data.append(dd)
    return {"success": True, "data": data, "count": len(data)}


@router.get("/{delivery_id}")
async def get_delivery_by_id(delivery_id: str, _=Depends(get_current_user)):
    delivery = await Delivery.get(delivery_id)
    if not delivery:
        raise HTTPException(status_code=404, detail="Delivery not found")
    dd = delivery.model_dump()
    dd["id"] = str(delivery.id)
    vehicle = await Vehicle.get(delivery.vehicle_id)
    if vehicle:
        dd["vehicle"] = vehicle.model_dump() | {"id": str(vehicle.id)}
    return {"success": True, "data": dd}


@router.post("", status_code=201)
async def create_delivery(body: CreateDeliveryBody, _=Depends(get_current_user)):
    total_quantity = sum(i.quantity for i in body.items)
    total_value = sum(i.quantity * i.price_per_unit for i in body.items)

    delivery_items = [
        DeliveryItem(
            stock_id=i.stock_id,
            quantity=i.quantity,
            price_per_unit=i.price_per_unit,
            selling_price=i.selling_price or i.price_per_unit,
        )
        for i in body.items
    ]

    delivery = await Delivery(
        delivery_number=_gen_delivery_number(),
        vehicle_id=body.vehicle_id,
        destination=body.destination,
        destination_market=body.destination_market or "",
        total_quantity=total_quantity,
        total_value=total_value,
        scheduled_date=body.scheduled_date or datetime.utcnow(),
        driver_notes=body.driver_notes or "",
        items=delivery_items,
    ).insert()

    # Mark vehicle as in-transit
    vehicle = await Vehicle.get(body.vehicle_id)
    if vehicle:
        await vehicle.set({"status": "in-transit"})

    dd = delivery.model_dump()
    dd["id"] = str(delivery.id)
    return {"success": True, "message": "Delivery created successfully", "data": dd}


@router.patch("/{delivery_id}/status")
async def update_delivery_status(delivery_id: str, body: UpdateStatusBody, _=Depends(get_current_user)):
    delivery = await Delivery.get(delivery_id)
    if not delivery:
        raise HTTPException(status_code=404, detail="Delivery not found")

    update = {"status": body.status, "driver_notes": body.driver_notes or "", "updated_at": datetime.utcnow()}
    if body.status == "delivered":
        update["delivered_date"] = body.delivered_date or datetime.utcnow()

    await delivery.set(update)

    if body.status in ("delivered", "cancelled"):
        vehicle = await Vehicle.get(delivery.vehicle_id)
        if vehicle:
            await vehicle.set({"status": "available"})

    dd = delivery.model_dump()
    dd["id"] = str(delivery.id)
    return {"success": True, "message": "Delivery status updated", "data": dd}


@router.delete("/{delivery_id}")
async def delete_delivery(delivery_id: str, _=Depends(get_current_user)):
    delivery = await Delivery.get(delivery_id)
    if not delivery:
        raise HTTPException(status_code=404, detail="Delivery not found")
    await delivery.delete()
    return {"success": True, "message": "Delivery deleted successfully"}
