from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from dotenv import load_dotenv
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from datetime import datetime
import os


# Add this import at the top with other routes
# from app.routes import ai

# Add this with other router includes


load_dotenv()

from app.db.database import connect_db
from app.routes import auth, dashboard, farmers, stocks, vehicles, deliveries, customers, orders,ai,ml_predictions


@asynccontextmanager
async def lifespan(app: FastAPI):
    await connect_db()
    yield


# Rate limiter
limiter = Limiter(key_func=get_remote_address, default_limits=["200/15minutes"])

app = FastAPI(
    title="Smart Veg Logistics API",
    description="Backend API for Smart Veg Logistics – vegetable supply chain management",
    version="1.0.0",
    lifespan=lifespan,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS
frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[frontend_url],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routes
app.include_router(ml_predictions.router)
app.include_router(ai.router)
app.include_router(auth.router)
app.include_router(dashboard.router)
app.include_router(farmers.router)
app.include_router(stocks.router)
app.include_router(vehicles.router)
app.include_router(deliveries.router)
app.include_router(customers.router)
app.include_router(orders.router)


# Health check
@app.get("/health")
async def health():
    return {
        "success": True,
        "message": "Smart Veg Logistics API is running 🚛🌱",
        "timestamp": datetime.utcnow(),
    }


# Global error handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"success": False, "message": "Internal server error"},
    )
