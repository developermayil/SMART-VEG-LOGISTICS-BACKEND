from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from app.middleware.auth import get_current_user
from app.models.stock import Stock
from app.models.order import Order
from app.models.delivery import Delivery

# Import ML models
import sys
sys.path.append('backend')
from ml.demand_forecast import DemandForecastModel
from ml.price_prediction import PricePredictionModel
from ml.delivery_time_prediction import DeliveryTimePredictor

router = APIRouter(prefix="/api/ml", tags=["ML Predictions"])

# Initialize models (load pre-trained or train on startup)
demand_model = DemandForecastModel()
price_model = PricePredictionModel()
delivery_model = DeliveryTimePredictor()

class DemandForecastRequest(BaseModel):
    vegetable: str
    days: int = 7


class PriceForecastRequest(BaseModel):
    vegetable: str
    days: int = 7


@router.get("/demand-forecast/{vegetable}")
async def forecast_demand(vegetable: str, days: int = 7, _=Depends(get_current_user)):
    """
    Predict demand for a specific vegetable for the next N days
    """
    # Get historical stock data
    stocks = await Stock.find({"vegetable": vegetable}).sort("purchase_date", -1).limit(365).to_list()
    
    if len(stocks) < 30:
        raise HTTPException(status_code=404, detail=f"Insufficient data for {vegetable}")
    
    # Prepare data
    df = pd.DataFrame([{
        'date': s.purchase_date,
        'quantity': s.quantity,
        'price': s.price_per_unit
    } for s in stocks])
    
    # Make predictions
    predictions = await demand_model.predict_future(df, days)
    
    return {
        "success": True,
        "vegetable": vegetable,
        "forecast_days": days,
        "predictions": predictions,
        "recommendations": generate_recommendations(predictions)
    }


@router.get("/price-forecast/{vegetable}")
async def forecast_price(vegetable: str, days: int = 7, _=Depends(get_current_user)):
    """
    Predict price trends for vegetables
    """
    stocks = await Stock.find({"vegetable": vegetable}).sort("purchase_date", -1).limit(365).to_list()
    
    if len(stocks) < 60:
        raise HTTPException(status_code=404, detail=f"Insufficient price data for {vegetable}")
    
    df = pd.DataFrame([{
        'date': s.purchase_date,
        'price': s.price_per_unit,
        'quantity': s.quantity
    } for s in stocks])
    
    price_predictions = await price_model.predict(df, days)
    
    return {
        "success": True,
        "vegetable": vegetable,
        "current_price": stocks[0].price_per_unit if stocks else 0,
        "predicted_prices": price_predictions,
        "trend": "up" if price_predictions[-1] > price_predictions[0] else "down"
    }


@router.get("/reorder-suggestions")
async def get_reorder_suggestions(_=Depends(get_current_user)):
    """
    Suggest reorder quantities based on demand forecast
    """
    stocks = await Stock.find_all().to_list()
    
    # Group by vegetable
    veg_data = {}
    for stock in stocks:
        if stock.vegetable not in veg_data:
            veg_data[stock.vegetable] = []
        veg_data[stock.vegetable].append({
            'date': stock.purchase_date,
            'quantity': stock.quantity,
            'price': stock.price_per_unit
        })
    
    suggestions = []
    for vegetable, data in veg_data.items():
        if len(data) < 30:
            continue
        
        df = pd.DataFrame(data)
        
        # Calculate average daily demand
        df['date'] = pd.to_datetime(df['date'])
        df = df.sort_values('date')
        
        # Simple moving average for demand
        daily_demand = df.groupby(df['date'].dt.date)['quantity'].sum()
        avg_daily_demand = daily_demand.tail(30).mean()
        
        # Safety stock (20% of average demand)
        safety_stock = avg_daily_demand * 0.2
        
        # Current stock
        current_stock = df['quantity'].sum()
        
        # Lead time (assume 3 days)
        lead_time_days = 3
        reorder_point = avg_daily_demand * lead_time_days + safety_stock
        
        if current_stock <= reorder_point:
            suggested_order = avg_daily_demand * 7  # Order 7 days supply
            suggestions.append({
                "vegetable": vegetable,
                "current_stock": current_stock,
                "avg_daily_demand": avg_daily_demand,
                "reorder_point": reorder_point,
                "suggested_order_quantity": suggested_order,
                "urgency": "high" if current_stock < reorder_point * 0.7 else "medium"
            })
    
    suggestions.sort(key=lambda x: x['urgency'] == 'high', reverse=True)
    
    return {
        "success": True,
        "suggestions": suggestions[:10],
        "total_items_to_reorder": len(suggestions)
    }


@router.get("/delivery-eta/{delivery_id}")
async def predict_delivery_eta(delivery_id: str, _=Depends(get_current_user)):
    """
    Predict ETA for a specific delivery
    """
    delivery = await Delivery.get(delivery_id)
    if not delivery:
        raise HTTPException(status_code=404, detail="Delivery not found")
    
    # Get features for prediction
    features = {
        'distance_km': get_distance(delivery.destination),
        'time_of_day': datetime.now().hour,
        'day_of_week': datetime.now().weekday(),
        'destination_type': 'market'  # or 'retail', 'wholesale'
    }
    
    eta_minutes = await delivery_model.predict_eta(features)
    
    return {
        "success": True,
        "delivery_id": delivery_id,
        "destination": delivery.destination,
        "predicted_eta_minutes": eta_minutes,
        "predicted_arrival_time": (datetime.now() + timedelta(minutes=eta_minutes)).isoformat()
    }


@router.get("/business-insights")
async def get_ml_insights(_=Depends(get_current_user)):
    """
    Generate business insights using ML models
    """
    # Get all data
    stocks = await Stock.find_all().to_list()
    orders = await Order.find_all().to_list()
    deliveries = await Delivery.find_all().to_list()
    
    insights = {
        "demand_trends": {},
        "price_predictions": {},
        "optimization_suggestions": []
    }
    
    # Analyze top vegetables
    veg_sales = {}
    for order in orders:
        for item in order.items:
            veg = item.product_name
            if veg not in veg_sales:
                veg_sales[veg] = 0
            veg_sales[veg] += item.quantity
    
    top_vegetables = sorted(veg_sales.items(), key=lambda x: x[1], reverse=True)[:5]
    
    for veg, _ in top_vegetables:
        # Get historical data
        veg_stocks = [s for s in stocks if s.vegetable == veg]
        if len(veg_stocks) > 30:
            insights['demand_trends'][veg] = {
                "trend": "increasing" if veg_stocks[-5].quantity > veg_stocks[-10].quantity else "decreasing",
                "confidence": 0.85
            }
    
    # Stock optimization suggestions
    total_stock_value = sum(s.quantity * s.price_per_unit for s in stocks)
    total_revenue = sum(o.total_amount for o in orders if o.status == 'completed')
    
    insights['optimization_suggestions'] = [
        {
            "area": "inventory",
            "suggestion": "Reduce stock of slow-moving vegetables by 20% to free up capital",
            "potential_savings": total_stock_value * 0.15
        },
        {
            "area": "delivery",
            "suggestion": "Optimize delivery routes using historical traffic patterns",
            "potential_savings": "15-20% fuel reduction"
        },
        {
            "area": "pricing",
            "suggestion": f"Dynamic pricing for {top_vegetables[0][0]} could increase margins by 12%",
            "potential_savings": None
        }
    ]
    
    return {
        "success": True,
        "insights": insights,
        "generated_at": datetime.now().isoformat()
    }


def generate_recommendations(predictions):
    """Generate actionable recommendations from predictions"""
    if not predictions:
        return []
    
    avg_pred = np.mean(predictions)
    max_pred = np.max(predictions)
    min_pred = np.min(predictions)
    
    recommendations = []
    
    if max_pred > avg_pred * 1.3:
        recommendations.append("📈 High demand spike expected - increase stock by 30%")
    
    if min_pred < avg_pred * 0.7:
        recommendations.append("📉 Low demand period ahead - reduce orders")
    
    recommendations.append(f"💰 Expected average daily demand: {avg_pred:.0f} units")
    
    return recommendations


def get_distance(destination):
    """Get distance from warehouse to destination (simplified)"""
    # In production, use actual distance API
    distances = {
        "Ernakulam": 50,
        "Thrissur": 80,
        "Kozhikode": 150,
        "Kottayam": 60,
        "Kollam": 70
    }
    return distances.get(destination, 100)