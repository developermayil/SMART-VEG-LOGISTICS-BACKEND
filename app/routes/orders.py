from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, List, Literal
from datetime import datetime
from app.models.order import Order, OrderItem
from app.models.customer import Customer
from app.middleware.auth import get_current_user

router = APIRouter(prefix="/api/orders", tags=["Orders"])


class OrderItemBody(BaseModel):
    product_name: str
    quantity: float
    price: float


class OrderBody(BaseModel):
    customer_id: str
    items: List[OrderItemBody]
    total_amount: float
    status: Optional[Literal["pending", "processing", "completed", "cancelled"]] = "pending"
    notes: Optional[str] = ""
    created_date: Optional[datetime] = None


class StatusBody(BaseModel):
    status: Literal["pending", "processing", "completed", "cancelled"]


async def _count_orders() -> int:
    return await Order.count()


@router.get("")
async def get_all_orders(_=Depends(get_current_user)):
    orders = await Order.find_all().sort("-created_date").to_list()
    data = []
    for o in orders:
        customer = await Customer.get(o.customer_id)
        od = o.model_dump()
        od["id"] = str(o.id)
        od["customer_name"] = customer.name if customer else None
        od["customer_phone"] = customer.phone if customer else None
        data.append(od)
    return {"success": True, "data": data}


@router.get("/customer/{customer_id}")
async def get_orders_by_customer(customer_id: str, _=Depends(get_current_user)):
    orders = await Order.find({"customer_id": customer_id}).sort("-created_date").to_list()
    data = [o.model_dump() | {"id": str(o.id)} for o in orders]
    return {"success": True, "data": data}


@router.get("/{order_id}")
async def get_order(order_id: str, _=Depends(get_current_user)):
    order = await Order.get(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    od = order.model_dump()
    od["id"] = str(order.id)
    customer = await Customer.get(order.customer_id)
    if customer:
        od["customer_name"] = customer.name
        od["customer_phone"] = customer.phone
    return {"success": True, "data": od}


@router.post("", status_code=201)
async def create_order(body: OrderBody, _=Depends(get_current_user)):
    customer = await Customer.get(body.customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")

    count = await _count_orders()
    order_number = f"ORD-{str(count + 1).zfill(5)}"

    items = [OrderItem(**i.model_dump()) for i in body.items]
    order = await Order(
        order_number=order_number,
        customer_id=body.customer_id,
        items=items,
        total_amount=body.total_amount,
        status=body.status or "pending",
        notes=body.notes or "",
        created_date=body.created_date or datetime.utcnow(),
    ).insert()

    od = order.model_dump()
    od["id"] = str(order.id)
    od["customer_name"] = customer.name
    od["customer_phone"] = customer.phone
    return {"success": True, "data": od}


@router.put("/{order_id}")
async def update_order(order_id: str, body: OrderBody, _=Depends(get_current_user)):
    order = await Order.get(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    update = {
        "customer_id": body.customer_id,
        "items": [OrderItem(**i.model_dump()) for i in body.items],
        "total_amount": body.total_amount,
        "status": body.status,
        "notes": body.notes,
        "updated_at": datetime.utcnow(),
    }
    if body.created_date:
        update["created_date"] = body.created_date

    await order.set(update)
    od = order.model_dump()
    od["id"] = str(order.id)
    return {"success": True, "data": od}


@router.patch("/{order_id}/status")
async def update_order_status(order_id: str, body: StatusBody, _=Depends(get_current_user)):
    order = await Order.get(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    await order.set({"status": body.status, "updated_at": datetime.utcnow()})
    od = order.model_dump()
    od["id"] = str(order.id)
    return {"success": True, "data": od}


@router.delete("/{order_id}")
async def delete_order(order_id: str, _=Depends(get_current_user)):
    order = await Order.get(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    await order.delete()
    return {"success": True, "message": "Order deleted successfully"}
