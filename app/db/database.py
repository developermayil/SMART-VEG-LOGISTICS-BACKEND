from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
from app.models.user import User
from app.models.farmer import Farmer
from app.models.customer import Customer
from app.models.order import Order
from app.models.stock import Stock
from app.models.delivery import Delivery
from app.models.vehicle import Vehicle
import os


async def connect_db():
    uri = os.getenv("MONGODB_URI")
    if not uri:
        raise ValueError("MONGODB_URI is not defined in environment variables")

    print("🔄 Connecting to MongoDB Atlas...")
    client = AsyncIOMotorClient(uri)
    await init_beanie(
        database=client.get_default_database(),
        document_models=[User, Farmer, Customer, Order, Stock, Delivery, Vehicle],
    )
    print("✅ MongoDB Atlas connected successfully!")
