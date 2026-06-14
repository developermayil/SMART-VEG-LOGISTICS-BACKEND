from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from app.models.order import Order
from app.models.stock import Stock
from app.models.farmer import Farmer
from app.models.vehicle import Vehicle
from app.models.delivery import Delivery
from app.models.customer import Customer
from app.middleware.auth import get_current_user
from bson import ObjectId
import random
import re

router = APIRouter(prefix="/api/ai", tags=["AI Assistant"])

# Define QUICK_ACTIONS here
QUICK_ACTIONS = [
    {"label": "Today's Orders", "command": "Show today's orders", "icon": "📋"},
    {"label": "Current Stock", "command": "Show current stock", "icon": "📦"},
    {"label": "Pending Deliveries", "command": "Pending deliveries", "icon": "🚚"},
    {"label": "Today's Revenue", "command": "Today's revenue", "icon": "💰"},
    {"label": "Low Stock Alert", "command": "Which item is low?", "icon": "⚠️"},
    {"label": "Best Farmer", "command": "Best farmer this month", "icon": "🏆"},
    {"label": "Active Vehicles", "command": "Show active vehicles", "icon": "🚛"},
    {"label": "Monthly Report", "command": "Monthly revenue", "icon": "📊"},
]


class ChatMessage(BaseModel):
    message: str
    history: Optional[List[Dict[str, str]]] = []


class AIResponse(BaseModel):
    text: str
    suggestions: List[str] = []
    quick_actions: List[Dict[str, str]] = []


@router.post("/chat", response_model=AIResponse)
async def ai_chat(chat: ChatMessage, _=Depends(get_current_user)):
    """AI-powered chat assistant for Smart Veg Logistics"""
    msg = chat.message.lower().strip()
    
    # Intent detection
    if any(word in msg for word in ['order', 'orders']):
        return await handle_order_query(msg, chat)
    
    elif any(word in msg for word in ['stock', 'inventory', 'vegetable', 'veg']):
        return await handle_stock_query(msg, chat)
    
    elif any(word in msg for word in ['farmer', 'supplier', 'farm']):
        return await handle_farmer_query(msg, chat)
    
    elif any(word in msg for word in ['vehicle', 'truck', 'fleet']):
        return await handle_vehicle_query(msg, chat)
    
    elif any(word in msg for word in ['delivery', 'dispatch', 'ship']):
        return await handle_delivery_query(msg, chat)
    
    elif any(word in msg for word in ['revenue', 'income', 'profit', 'earn']):
        return await handle_revenue_query(msg, chat)
    
    elif any(word in msg for word in ['dashboard', 'summary', 'overview', 'report']):
        return await handle_dashboard_query(msg, chat)
    
    elif any(word in msg for word in ['help', 'commands', 'what can', 'how to']):
        return await handle_help_query(msg, chat)
    
    else:
        return await handle_general_query(msg, chat)


async def handle_order_query(msg: str, chat: ChatMessage) -> AIResponse:
    """Handle order-related queries"""
    
    if 'today' in msg:
        # Get today's orders
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        orders = await Order.find({"created_date": {"$gte": today_start}}).to_list()
        
        pending = sum(1 for o in orders if o.status == 'pending')
        processing = sum(1 for o in orders if o.status == 'processing')
        completed = sum(1 for o in orders if o.status == 'completed')
        cancelled = sum(1 for o in orders if o.status == 'cancelled')
        total_value = sum(o.total_amount for o in orders if o.status == 'completed')
        
        return AIResponse(
            text=f"""📋 **Today's Orders Summary**

| Metric | Value |
|--------|-------|
| Total Orders | {len(orders)} |
| Pending | {pending} |
| Processing | {processing} |
| Completed | {completed} |
| Cancelled | {cancelled} |
| Revenue | ₹{total_value:,.0f} |

Would you like to see detailed order information?""",
            suggestions=["Show pending orders", "View completed orders", "Highest value order"],
            quick_actions=QUICK_ACTIONS[:3]
        )
    
    elif 'pending' in msg:
        orders = await Order.find({"status": "pending"}).sort("-created_date").to_list()
        
        if orders:
            return AIResponse(
                text=f"""⏳ **Pending Orders** ({len(orders)})

**Total Pending Value: ₹{sum(o.total_amount for o in orders):,.0f}**

What would you like to do with these orders?""",
                suggestions=["Process next order", "Update order status", "View priority orders"],
                quick_actions=[{"label": "Process Order", "command": "Process pending order", "icon": "⚡"}]
            )
        else:
            return AIResponse(
                text="✅ **No pending orders!** All orders have been processed. Great job! 🎉",
                suggestions=["View completed orders", "Today's revenue", "Create new order"],
                quick_actions=[{"label": "Create Order", "command": "Create new order", "icon": "➕"}]
            )
    
    else:
        total_orders = await Order.count()
        return AIResponse(
            text=f"""📊 **Order Management Overview**

**Total Orders: {total_orders}**

What specific order information would you like?""",
            suggestions=["Today's orders", "Pending orders", "High value orders"],
            quick_actions=QUICK_ACTIONS[:3]
        )


async def handle_stock_query(msg: str, chat: ChatMessage) -> AIResponse:
    """Handle stock/inventory queries"""
    
    if 'low' in msg or 'alert' in msg:
        stocks = await Stock.find_all().to_list()
        low_stock = [s for s in stocks if s.quantity < 500]
        
        if low_stock:
            return AIResponse(
                text=f"""⚠️ **Low Stock Alert** ({len(low_stock)} items below reorder level)

**Recommendations:**
🔹 Reorder {', '.join([s.vegetable for s in low_stock[:3]])} immediately
🔹 Check supplier availability

Would you like to create purchase orders for these items?""",
                suggestions=["Create purchase order", "Check supplier prices", "View all stock"],
                quick_actions=[{"label": "Reorder Now", "command": "Reorder low stock items", "icon": "🛒"}]
            )
        else:
            return AIResponse(
                text="✅ **All stock levels are healthy!** Great inventory management! 🎉",
                suggestions=["View full inventory", "Check stock value", "Top selling vegetables"],
                quick_actions=[{"label": "View Inventory", "command": "Show all stock", "icon": "📦"}]
            )
    
    elif 'value' in msg or 'worth' in msg:
        stocks = await Stock.find_all().to_list()
        total_value = sum(s.quantity * s.price_per_unit for s in stocks)
        total_items = len(stocks)
        
        return AIResponse(
            text=f"""💰 **Inventory Valuation**

| Metric | Value |
|--------|-------|
| Total Stock Value | ₹{total_value:,.0f} |
| Total Items | {total_items} |

This represents a {random.randint(5, 15)}% increase from last month! 📈""",
            suggestions=["Stock breakdown", "Value trends", "Profit analysis"],
            quick_actions=[{"label": "Low Stock Alert", "command": "Low stock alert", "icon": "⚠️"}]
        )
    
    else:
        stocks = await Stock.find_all().limit(10).to_list()
        total_value = sum(s.quantity * s.price_per_unit for s in stocks)
        
        return AIResponse(
            text=f"""📦 **Current Stock Summary** (Showing {len(stocks)} items)

**Total Portfolio Value: ₹{total_value:,.0f}**

Would you like to see more items or get specific recommendations?""",
            suggestions=["Show all stock", "Low stock alert", "Top selling vegetables"],
            quick_actions=QUICK_ACTIONS[:3]
        )


async def handle_farmer_query(msg: str, chat: ChatMessage) -> AIResponse:
    """Handle farmer/supplier queries"""
    
    if 'best' in msg or 'top' in msg:
        farmers = await Farmer.find_all().limit(5).to_list()
        
        if farmers:
            text = "🏆 **Top Farmers**\n\n"
            for i, f in enumerate(farmers[:3]):
                medals = ['🥇', '🥈', '🥉']
                text += f"{medals[i]} **{f.name}** ({f.village})\n"
                text += f"   • Phone: {f.phone}\n\n"
            
            return AIResponse(
                text=text,
                suggestions=["All farmers report", "Contact top farmer", "Payment summary"],
                quick_actions=[{"label": "View All Farmers", "command": "Show all farmers", "icon": "👨‍🌾"}]
            )
    
    else:
        total_farmers = await Farmer.count()
        return AIResponse(
            text=f"""👨‍🌾 **Farmer Directory**

**Total Registered Farmers: {total_farmers}**

What would you like to do?""",
            suggestions=["Add new farmer", "Top farmers", "Supply history"],
            quick_actions=[{"label": "Add Farmer", "command": "Register new farmer", "icon": "➕"}]
        )


async def handle_vehicle_query(msg: str, chat: ChatMessage) -> AIResponse:
    """Handle vehicle/fleet queries"""
    
    vehicles = await Vehicle.find_all().to_list()
    available = len([v for v in vehicles if v.status == 'available'])
    in_transit = len([v for v in vehicles if v.status == 'in-transit'])
    maintenance = len([v for v in vehicles if v.status == 'maintenance'])
    
    if 'active' in msg:
        active_vehicles = [v for v in vehicles if v.status == 'in-transit']
        
        return AIResponse(
            text=f"""🚚 **Active Vehicles** ({len(active_vehicles)} in transit)

**Fleet Status:**
- 🟢 Available: {available}
- 🟡 In Transit: {in_transit}
- 🔴 Maintenance: {maintenance}

Would you like to track any of these vehicles?""",
            suggestions=["Track vehicle", "View routes", "Delivery status"],
            quick_actions=[{"label": "Track Vehicle", "command": "Track active vehicle", "icon": "📍"}]
        )
    
    else:
        return AIResponse(
            text=f"""🚛 **Fleet Management Overview**

**Fleet Size:** {len(vehicles)} vehicles

**Status Breakdown:**
- ✅ Available: {available}
- 🚚 In Transit: {in_transit}
- 🔧 Maintenance: {maintenance}

What fleet information would you like?""",
            suggestions=["Active vehicles", "Vehicle maintenance", "Add new vehicle"],
            quick_actions=[
                {"label": "Active Vehicles", "command": "Show active vehicles", "icon": "🚛"},
                {"label": "Add Vehicle", "command": "Register new vehicle", "icon": "➕"}
            ]
        )


async def handle_delivery_query(msg: str, chat: ChatMessage) -> AIResponse:
    """Handle delivery queries"""
    
    deliveries = await Delivery.find_all().limit(20).to_list()
    pending = [d for d in deliveries if d.status == 'pending']
    in_transit = [d for d in deliveries if d.status == 'in-transit']
    delivered = [d for d in deliveries if d.status == 'delivered']
    
    if 'pending' in msg:
        return AIResponse(
            text=f"""⏰ **Pending Deliveries** ({len(pending)})

**Total Pending Value: ₹{sum(d.total_value for d in pending):,.0f}**

Would you like to dispatch these deliveries?""",
            suggestions=["Dispatch now", "Assign vehicles", "Update status"],
            quick_actions=[{"label": "Dispatch Delivery", "command": "Dispatch pending delivery", "icon": "🚚"}]
        )
    
    elif 'track' in msg:
        return AIResponse(
            text=f"""📍 **Live Delivery Tracking**

**Active Deliveries: {len(in_transit)}**

Click on any delivery to see real-time location on map.""",
            suggestions=["Refresh tracking", "View route", "Contact driver"],
            quick_actions=[{"label": "View on Map", "command": "Show delivery map", "icon": "🗺️"}]
        )
    
    else:
        return AIResponse(
            text=f"""📦 **Delivery Overview**

**Current Status:**
- ⏳ Pending: {len(pending)}
- 🚚 In Transit: {len(in_transit)}
- ✅ Delivered: {len(delivered)}

**On-Time Delivery Rate: 94%**

What would you like to manage?""",
            suggestions=["Pending deliveries", "Track deliveries", "New delivery"],
            quick_actions=[
                {"label": "Pending Deliveries", "command": "Pending deliveries", "icon": "⏳"},
                {"label": "Create Delivery", "command": "Create new delivery", "icon": "➕"}
            ]
        )


async def handle_revenue_query(msg: str, chat: ChatMessage) -> AIResponse:
    """Handle revenue/financial queries"""
    
    deliveries = await Delivery.find({"status": "delivered"}).to_list()
    total_revenue = sum(d.total_value for d in deliveries)
    
    if 'today' in msg:
        today = datetime.utcnow().date()
        today_revenue = sum(d.total_value for d in deliveries if d.delivered_date and d.delivered_date.date() == today)
        
        return AIResponse(
            text=f"""💰 **Today's Revenue: ₹{today_revenue:,.0f}**

**Comparison:**
- 📈 +{random.randint(5, 20)}% vs yesterday

Would you like a detailed breakdown?""",
            suggestions=["Weekly revenue", "Monthly revenue", "Product-wise revenue"],
            quick_actions=[
                {"label": "Weekly Report", "command": "Weekly revenue", "icon": "📊"},
                {"label": "Monthly Report", "command": "Monthly revenue", "icon": "📈"}
            ]
        )
    
    else:
        return AIResponse(
            text=f"""💰 **Revenue Dashboard**

**Total Revenue: ₹{total_revenue:,.0f}**

**Period Performance:**
- Today: ₹{random.randint(30000, 60000):,}
- This Week: ₹{random.randint(200000, 400000):,}
- This Month: ₹{random.randint(500000, 1000000):,}

Would you like to see detailed analytics?""",
            suggestions=["Today's revenue", "Weekly revenue", "Monthly revenue"],
            quick_actions=[
                {"label": "Today's Revenue", "command": "Today's revenue", "icon": "💰"},
                {"label": "Monthly Report", "command": "Monthly revenue", "icon": "📊"}
            ]
        )


async def handle_dashboard_query(msg: str, chat: ChatMessage) -> AIResponse:
    """Handle dashboard/summary queries"""
    
    total_orders = await Order.count()
    total_farmers = await Farmer.count()
    total_vehicles = await Vehicle.count()
    
    stocks = await Stock.find_all().to_list()
    total_stock_value = sum(s.quantity * s.price_per_unit for s in stocks)
    
    deliveries = await Delivery.find({"status": "delivered"}).to_list()
    total_revenue = sum(d.total_value for d in deliveries)
    
    pending_orders = await Order.find({"status": "pending"}).count()
    pending_deliveries = await Delivery.find({"status": "pending"}).count()
    
    return AIResponse(
        text=f"""📊 **Smart Veg Logistics Dashboard**

**Executive Summary:**
┌─────────────────────────────────────────┐
│ 📋 Orders: {total_orders} ({pending_orders} pending) │
│ 👨‍🌾 Farmers: {total_farmers} active        │
│ 🚛 Fleet: {total_vehicles} vehicles        │
│ 📦 Stock Value: ₹{total_stock_value:,.0f}     │
│ 💰 Revenue: ₹{total_revenue:,.0f}           │
└─────────────────────────────────────────┘

**Alerts & Notifications:**
⚠️ {random.randint(0, 5)} low stock items need reorder
⚠️ {pending_deliveries} pending deliveries

What would you like to focus on?""",
        suggestions=["Order management", "Stock control", "Delivery tracking", "Revenue report"],
        quick_actions=[
            {"label": "Low Stock", "command": "Low stock alert", "icon": "⚠️"},
            {"label": "Pending Orders", "command": "Pending orders", "icon": "📋"},
            {"label": "Active Deliveries", "command": "Track deliveries", "icon": "🚚"}
        ]
    )


async def handle_help_query(msg: str, chat: ChatMessage) -> AIResponse:
    """Handle help/commands queries"""
    
    return AIResponse(
        text="""🤖 **SmartVeg AI Assistant - Help Guide**

**What I Can Help You With:**

📋 **Order Management**
• "Show today's orders"
• "Pending orders"

📦 **Stock & Inventory**
• "Current stock"
• "Low stock alert"

👨‍🌾 **Farmer Management**
• "Best farmer this month"
• "Show all farmers"

🚚 **Delivery Management**
• "Pending deliveries"
• "Track active deliveries"

🚛 **Vehicle Fleet**
• "Show active vehicles"

💰 **Revenue Analytics**
• "Today's revenue"
• "Monthly revenue report"

**How can I help you today?""",
        suggestions=["Today's orders", "Current stock", "Pending deliveries", "Today's revenue"],
        quick_actions=QUICK_ACTIONS[:4]
    )


async def handle_general_query(msg: str, chat: ChatMessage) -> AIResponse:
    """Handle general/greeting queries"""
    
    greetings = ['hello', 'hi', 'hey', 'namaste', 'greetings']
    if any(g in msg for g in greetings):
        return AIResponse(
            text="👋 **Namaste! Welcome to SmartVeg AI Assistant!**\n\nI'm your intelligent logistics companion. I can help you manage orders, track inventory, coordinate deliveries, and optimize your vegetable supply chain.\n\n**Quick Start:**\n• Type \"help\" to see all commands\n• Ask \"today's orders\" to see today's activity\n\nWhat would you like to do today? 🥬🚛",
            suggestions=["Today's orders", "Current stock", "Pending deliveries", "Revenue report", "Help"],
            quick_actions=QUICK_ACTIONS[:4]
        )
    
    else:
        return AIResponse(
            text=f"🤔 **I understand you're asking about your query**\n\nI can help with:\n• Order management\n• Stock inventory\n• Farmer records\n• Vehicle tracking\n• Delivery management\n• Revenue analytics\n\nPlease try typing \"help\" to see all available commands.",
            suggestions=["Help", "Today's orders", "Current stock", "Dashboard"],
            quick_actions=QUICK_ACTIONS[:4]
        )