from fastapi import APIRouter, Depends
from app.models.stock import Stock
from app.models.farmer import Farmer
from app.models.vehicle import Vehicle
from app.models.delivery import Delivery
from app.middleware.auth import get_current_user
from bson import ObjectId

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])


@router.get("/status")
async def get_dashboard_stats(_=Depends(get_current_user)):
    stock_col = Stock.get_motor_collection()
    vehicle_col = Vehicle.get_motor_collection()
    delivery_col = Delivery.get_motor_collection()

    # Run all aggregations concurrently
    import asyncio

    stock_agg, total_farmers, vehicle_agg, delivery_agg, recent_deliveries, stock_by_veg = await asyncio.gather(
        stock_col.aggregate([
            {"$group": {
                "_id": None,
                "total_items": {"$sum": 1},
                "total_quantity": {"$sum": "$quantity"},
                "total_stock_value": {"$sum": {"$multiply": ["$quantity", "$price_per_unit"]}}
            }}
        ]).to_list(1),
        Farmer.count(),
        vehicle_col.aggregate([
            {"$group": {
                "_id": None,
                "total_vehicles": {"$sum": 1},
                "available": {"$sum": {"$cond": [{"$eq": ["$status", "available"]}, 1, 0]}},
                "in_transit": {"$sum": {"$cond": [{"$eq": ["$status", "in-transit"]}, 1, 0]}}
            }}
        ]).to_list(1),
        delivery_col.aggregate([
            {"$group": {
                "_id": None,
                "total_deliveries": {"$sum": 1},
                "completed": {"$sum": {"$cond": [{"$eq": ["$status", "delivered"]}, 1, 0]}},
                "active": {"$sum": {"$cond": [{"$eq": ["$status", "in-transit"]}, 1, 0]}},
                "revenue": {"$sum": {"$cond": [{"$eq": ["$status", "delivered"]}, "$total_value", 0]}}
            }}
        ]).to_list(1),
        delivery_col.aggregate([
            {"$sort": {"created_at": -1}},
            {"$limit": 5},
            {"$project": {"delivery_number": 1, "destination": 1, "status": 1, "total_value": 1, "scheduled_date": 1, "vehicle_id": 1}}
        ]).to_list(5),
        stock_col.aggregate([
            {"$group": {
                "_id": "$vegetable",
                "total_quantity": {"$sum": "$quantity"},
                "avg_price": {"$avg": "$price_per_unit"}
            }},
            {"$project": {"vegetable": "$_id", "total_quantity": 1, "avg_price": 1, "_id": 0}},
            {"$sort": {"total_quantity": -1}}
        ]).to_list(100),
    )

    def _str_ids(doc):
        if doc:
            doc.pop("_id", None)
        return doc or {}

    return {
        "success": True,
        "data": {
            "stocks": _str_ids(stock_agg[0]) if stock_agg else {"total_items": 0, "total_quantity": 0, "total_stock_value": 0},
            "farmers": {"total_farmers": total_farmers},
            "vehicles": _str_ids(vehicle_agg[0]) if vehicle_agg else {"total_vehicles": 0, "available": 0, "in_transit": 0},
            "deliveries": _str_ids(delivery_agg[0]) if delivery_agg else {"total_deliveries": 0, "completed": 0, "active": 0, "revenue": 0},
            "recent_deliveries": [_str_ids(d) for d in recent_deliveries],
            "stock_by_vegetable": stock_by_veg,
        },
    }
