from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
from app.models.farmer import Farmer
from app.models.stock import Stock
from app.middleware.auth import get_current_user
from datetime import datetime

router = APIRouter(prefix="/api/farmers", tags=["Farmers"])


class FarmerBody(BaseModel):
    name: str
    village: str
    district: Optional[str] = "Tamil Nadu"
    phone: str
    alternate_phone: Optional[str] = ""
    email: Optional[str] = ""
    bank_account: Optional[str] = ""
    ifsc_code: Optional[str] = ""


@router.get("")
async def get_all_farmers(_=Depends(get_current_user)):
    farmers = await Farmer.find_all().sort("-created_at").to_list()

    stock_col = Stock.get_motor_collection()
    stats = await stock_col.aggregate([
        {"$group": {
            "_id": "$farmer_id",
            "total_supplies": {"$sum": 1},
            "total_quantity_supplied": {"$sum": "$quantity"},
            "total_value": {"$sum": {"$multiply": ["$quantity", "$price_per_unit"]}}
        }}
    ]).to_list(None)
    stats_map = {str(s["_id"]): s for s in stats}

    data = []
    for f in farmers:
        fd = f.model_dump()
        fd["id"] = str(f.id)
        s = stats_map.get(str(f.id), {})
        fd["total_supplies"] = s.get("total_supplies", 0)
        fd["total_quantity_supplied"] = s.get("total_quantity_supplied", 0)
        fd["total_value"] = s.get("total_value", 0)
        data.append(fd)

    return {"success": True, "data": data, "count": len(data)}


@router.get("/{farmer_id}")
async def get_farmer_by_id(farmer_id: str, _=Depends(get_current_user)):
    farmer = await Farmer.get(farmer_id)
    if not farmer:
        raise HTTPException(status_code=404, detail="Farmer not found")

    supplies = await Stock.find({"farmer_id": farmer_id}).sort("-created_at").to_list()
    fd = farmer.model_dump()
    fd["id"] = str(farmer.id)
    fd["supplies"] = [s.model_dump() | {"id": str(s.id)} for s in supplies]
    return {"success": True, "data": fd}


@router.post("", status_code=201)
async def create_farmer(body: FarmerBody, _=Depends(get_current_user)):
    farmer = await Farmer(**body.model_dump()).insert()
    fd = farmer.model_dump()
    fd["id"] = str(farmer.id)
    return {"success": True, "message": "Farmer registered successfully", "data": fd}


@router.put("/{farmer_id}")
async def update_farmer(farmer_id: str, body: FarmerBody, _=Depends(get_current_user)):
    farmer = await Farmer.get(farmer_id)
    if not farmer:
        raise HTTPException(status_code=404, detail="Farmer not found")

    update_data = body.model_dump()
    update_data["updated_at"] = datetime.utcnow()
    await farmer.set(update_data)
    fd = farmer.model_dump()
    fd["id"] = str(farmer.id)
    return {"success": True, "message": "Farmer updated successfully", "data": fd}


@router.delete("/{farmer_id}")
async def delete_farmer(farmer_id: str, _=Depends(get_current_user)):
    farmer = await Farmer.get(farmer_id)
    if not farmer:
        raise HTTPException(status_code=404, detail="Farmer not found")
    await farmer.delete()
    return {"success": True, "message": "Farmer deleted successfully"}
