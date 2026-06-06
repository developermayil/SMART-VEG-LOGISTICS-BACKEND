from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from app.models.customer import Customer
from app.middleware.auth import get_current_user

router = APIRouter(prefix="/api/customers", tags=["Customers"])


class CustomerBody(BaseModel):
    name: str
    phone: str
    email: Optional[str] = None
    address: Optional[str] = None
    village: Optional[str] = None


@router.get("")
async def get_all_customers(_=Depends(get_current_user)):
    customers = await Customer.find_all().sort("-created_at").to_list()
    data = [c.model_dump() | {"id": str(c.id)} for c in customers]
    return {"success": True, "data": data}


@router.get("/{customer_id}")
async def get_customer(customer_id: str, _=Depends(get_current_user)):
    customer = await Customer.get(customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    cd = customer.model_dump()
    cd["id"] = str(customer.id)
    return {"success": True, "data": cd}


@router.post("", status_code=201)
async def create_customer(body: CustomerBody, _=Depends(get_current_user)):
    customer = await Customer(**body.model_dump()).insert()
    cd = customer.model_dump()
    cd["id"] = str(customer.id)
    return {"success": True, "data": cd}


@router.put("/{customer_id}")
async def update_customer(customer_id: str, body: CustomerBody, _=Depends(get_current_user)):
    customer = await Customer.get(customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    update = body.model_dump()
    update["updated_at"] = datetime.utcnow()
    await customer.set(update)
    cd = customer.model_dump()
    cd["id"] = str(customer.id)
    return {"success": True, "data": cd}


@router.delete("/{customer_id}")
async def delete_customer(customer_id: str, _=Depends(get_current_user)):
    customer = await Customer.get(customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    await customer.delete()
    return {"success": True, "message": "Customer deleted successfully"}
