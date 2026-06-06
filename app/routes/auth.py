from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, EmailStr
from passlib.context import CryptContext
from jose import jwt
from datetime import datetime, timedelta
from app.models.user import User
from app.middleware.auth import get_current_user
import os

router = APIRouter(prefix="/api/auth", tags=["Auth"])
pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")


def _make_token(user: User) -> str:
    secret = os.getenv("JWT_SECRET", "secret")
    expires_days = int(os.getenv("JWT_EXPIRES_DAYS", "7"))
    payload = {
        "id": str(user.id),
        "username": user.username,
        "role": user.role,
        "exp": datetime.utcnow() + timedelta(days=expires_days),
    }
    return jwt.encode(payload, secret, algorithm="HS256")


# ---------- schemas ----------
class LoginBody(BaseModel):
    username: str
    password: str


class RegisterBody(BaseModel):
    username: str
    email: EmailStr
    password: str


# ---------- endpoints ----------
@router.post("/login")
async def login(body: LoginBody):
    user = await User.find_one(
        {"$or": [{"username": body.username}, {"email": body.username}]}
    )
    if not user or not pwd_ctx.verify(body.password, user.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = _make_token(user)
    return {
        "success": True,
        "message": "Login successful",
        "token": token,
        "user": {
            "id": str(user.id),
            "username": user.username,
            "email": user.email,
            "role": user.role,
        },
    }


@router.post("/register", status_code=201)
async def register(body: RegisterBody):
    existing = await User.find_one(
        {"$or": [{"username": body.username}, {"email": body.email}]}
    )
    if existing:
        raise HTTPException(status_code=409, detail="Username or email already exists")

    hashed = pwd_ctx.hash(body.password)
    await User(username=body.username, email=body.email, password=hashed).insert()
    return {"success": True, "message": "Admin account created successfully"}


@router.get("/profile")
async def get_profile(current_user=Depends(get_current_user)):
    user = await User.get(current_user["id"])
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    data = user.model_dump(exclude={"password"})
    data["id"] = str(user.id)
    return {"success": True, "data": data}
