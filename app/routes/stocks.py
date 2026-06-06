from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from app.models.stock import Stock
from app.models.farmer import Farmer
from app.middleware.auth import get_current_user

router = APIRouter(prefix="/api/stocks", tags=["Stocks"])


class StockBody(BaseModel):
    vegetable: str
    quantity: float
    unit: Optional[str] = "kg"
    price_per_unit: float
    farmer_id: Optional[str] = None
    purchase_date: Optional[datetime] = None
    notes: Optional[str] = ""


async def _enrich(stock: Stock) -> dict:
    obj = stock.model_dump()
    obj["id"] = str(stock.id)
    farmer_name = None
    farmer_village = None
    if stock.farmer_id:
        farmer = await Farmer.get(stock.farmer_id)
        if farmer:
            farmer_name = farmer.name
            farmer_village = farmer.village
    obj["farmer_name"] = farmer_name
    obj["farmer_village"] = farmer_village
    return obj


@router.get("")
async def get_all_stocks(_=Depends(get_current_user)):
    stocks = await Stock.find_all().sort("-created_at").to_list()
    data = [await _enrich(s) for s in stocks]
    return {"success": True, "data": data, "count": len(data)}


@router.get("/summary")
async def get_stock_summary(_=Depends(get_current_user)):
    col = Stock.get_motor_collection()
    result = await col.aggregate([
        {"$group": {
            "_id": None,
            "total_items": {"$sum": 1},
            "total_quantity": {"$sum": "$quantity"},
            "total_value": {"$sum": {"$multiply": ["$quantity", "$price_per_unit"]}},
            "unique_vegetables": {"$addToSet": "$vegetable"}
        }},
        {"$project": {
            "_id": 0, "total_items": 1, "total_quantity": 1, "total_value": 1,
            "unique_vegetables": {"$size": "$unique_vegetables"}
        }}
    ]).to_list(1)
    data = result[0] if result else {"total_items": 0, "total_quantity": 0, "total_value": 0, "unique_vegetables": 0}
    return {"success": True, "data": data}


@router.get("/{stock_id}")
async def get_stock_by_id(stock_id: str, _=Depends(get_current_user)):
    stock = await Stock.get(stock_id)
    if not stock:
        raise HTTPException(status_code=404, detail="Stock not found")
    return {"success": True, "data": await _enrich(stock)}


@router.post("", status_code=201)
async def create_stock(body: StockBody, _=Depends(get_current_user)):
    stock = await Stock(**body.model_dump()).insert()
    return {"success": True, "message": "Stock added successfully", "data": await _enrich(stock)}


@router.put("/{stock_id}")
async def update_stock(stock_id: str, body: StockBody, _=Depends(get_current_user)):
    stock = await Stock.get(stock_id)
    if not stock:
        raise HTTPException(status_code=404, detail="Stock not found")
    update = body.model_dump()
    update["updated_at"] = datetime.utcnow()
    await stock.set(update)
    return {"success": True, "message": "Stock updated successfully", "data": await _enrich(stock)}


@router.delete("/{stock_id}")
async def delete_stock(stock_id: str, _=Depends(get_current_user)):
    stock = await Stock.get(stock_id)
    if not stock:
        raise HTTPException(status_code=404, detail="Stock not found")
    await stock.delete()
    return {"success": True, "message": "Stock deleted successfully"}
