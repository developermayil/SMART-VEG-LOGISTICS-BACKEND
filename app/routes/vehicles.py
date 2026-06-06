from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, Literal
from datetime import datetime
from app.models.vehicle import Vehicle
from app.models.delivery import Delivery
from app.middleware.auth import get_current_user

router = APIRouter(prefix="/api/vehicles", tags=["Vehicles"])


class VehicleBody(BaseModel):
    vehicle_number: str
    vehicle_type: Optional[str] = "Truck"
    driver_name: str
    driver_phone: str
    driver_license: Optional[str] = ""
    capacity: float
    status: Optional[Literal["available", "in-transit", "maintenance"]] = "available"


@router.get("")
async def get_all_vehicles(_=Depends(get_current_user)):
    vehicles = await Vehicle.find_all().sort("-created_at").to_list()

    delivery_col = Delivery.get_motor_collection()
    stats = await delivery_col.aggregate([
        {"$group": {
            "_id": "$vehicle_id",
            "total_deliveries": {"$sum": 1},
            "completed_deliveries": {"$sum": {"$cond": [{"$eq": ["$status", "delivered"]}, 1, 0]}}
        }}
    ]).to_list(None)
    stats_map = {str(s["_id"]): s for s in stats}

    data = []
    for v in vehicles:
        vd = v.model_dump()
        vd["id"] = str(v.id)
        s = stats_map.get(str(v.id), {})
        vd["total_deliveries"] = s.get("total_deliveries", 0)
        vd["completed_deliveries"] = s.get("completed_deliveries", 0)
        data.append(vd)

    return {"success": True, "data": data, "count": len(data)}


@router.get("/available")
async def get_available_vehicles(_=Depends(get_current_user)):
    vehicles = await Vehicle.find({"status": "available"}).sort("-capacity").to_list()
    data = [v.model_dump() | {"id": str(v.id)} for v in vehicles]
    return {"success": True, "data": data}


@router.get("/{vehicle_id}")
async def get_vehicle_by_id(vehicle_id: str, _=Depends(get_current_user)):
    vehicle = await Vehicle.get(vehicle_id)
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    vd = vehicle.model_dump()
    vd["id"] = str(vehicle.id)
    return {"success": True, "data": vd}


@router.post("", status_code=201)
async def create_vehicle(body: VehicleBody, _=Depends(get_current_user)):
    existing = await Vehicle.find_one({"vehicle_number": body.vehicle_number})
    if existing:
        raise HTTPException(status_code=409, detail="Vehicle number already exists")
    vehicle = await Vehicle(**body.model_dump()).insert()
    vd = vehicle.model_dump()
    vd["id"] = str(vehicle.id)
    return {"success": True, "message": "Vehicle added successfully", "data": vd}


@router.put("/{vehicle_id}")
async def update_vehicle(vehicle_id: str, body: VehicleBody, _=Depends(get_current_user)):
    vehicle = await Vehicle.get(vehicle_id)
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    update = body.model_dump()
    update["updated_at"] = datetime.utcnow()
    await vehicle.set(update)
    vd = vehicle.model_dump()
    vd["id"] = str(vehicle.id)
    return {"success": True, "message": "Vehicle updated successfully", "data": vd}


@router.delete("/{vehicle_id}")
async def delete_vehicle(vehicle_id: str, _=Depends(get_current_user)):
    vehicle = await Vehicle.get(vehicle_id)
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    await vehicle.delete()
    return {"success": True, "message": "Vehicle deleted successfully"}
