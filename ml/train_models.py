#!/usr/bin/env python
"""
Train all ML models for Smart Veg Logistics
Run: python backend/ml/train_models.py
"""

import asyncio
import pandas as pd
import numpy as np
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
import os

load_dotenv()

from demand_forecast import DemandForecastModel
from price_prediction import PricePredictionModel
from delivery_time_prediction import DeliveryTimePredictor

async def fetch_training_data():
    """Fetch historical data from MongoDB"""
    client = AsyncIOMotorClient(os.getenv("MONGODB_URI"))
    db = client.get_default_database()
    
    # Fetch stocks
    stocks_cursor = db.stocks.find()
    stocks = await stocks_cursor.to_list(length=10000)
    
    # Fetch deliveries
    deliveries_cursor = db.deliveries.find()
    deliveries = await deliveries_cursor.to_list(length=10000)
    
    return pd.DataFrame(stocks), pd.DataFrame(deliveries)

def train_demand_model(stocks_df):
    """Train demand forecasting model"""
    print("🔄 Training Demand Forecast Model...")
    
    # Prepare data by vegetable
    vegetables = stocks_df['vegetable'].unique()
    results = {}
    
    for veg in vegetables[:5]:  # Train on top 5 vegetables
        veg_data = stocks_df[stocks_df['vegetable'] == veg].copy()
        veg_data['date'] = pd.to_datetime(veg_data['purchase_date'])
        veg_data = veg_data.sort_values('date')
        
        if len(veg_data) < 60:
            continue
        
        # Aggregate daily demand
        daily_demand = veg_data.groupby(veg_data['date'].dt.date)['quantity'].sum().reset_index()
        daily_demand.columns = ['date', 'quantity']
        
        # Train model
        model = DemandForecastModel(lookback_days=30, forecast_days=7)
        
        # Prepare sequences
        X, y = model.prepare_data(daily_demand)
        
        if len(X) > 10:
            # Split data
            split = int(len(X) * 0.8)
            X_train, X_val = X[:split], X[split:]
            y_train, y_val = y[:split], y[split:]
            
            # Train
            model.train(X_train, y_train, X_val, y_val, epochs=50)
            
            # Evaluate
            metrics = model.evaluate(X_val, y_val)
            print(f"  ✅ {veg}: R²={metrics['r2']:.3f}, RMSE={metrics['rmse']:.2f}")
            
            # Save model
            model.save_model(f'models/demand_{veg}.h5')
            results[veg] = metrics
    
    return results

def train_price_model(stocks_df):
    """Train price prediction model"""
    print("\n🔄 Training Price Prediction Model...")
    
    vegetables = stocks_df['vegetable'].unique()
    results = {}
    
    for veg in vegetables[:5]:
        veg_data = stocks_df[stocks_df['vegetable'] == veg].copy()
        veg_data['date'] = pd.to_datetime(veg_data['purchase_date'])
        veg_data = veg_data.sort_values('date')
        
        if len(veg_data) < 90:
            continue
        
        # Prepare data
        veg_data['price'] = veg_data['price_per_unit']
        
        model = PricePredictionModel(sequence_length=30)
        
        # Add features
        veg_data = model.add_external_features(veg_data)
        
        # Prepare sequences
        feature_cols = [col for col in veg_data.columns if col not in ['date', '_id']]
        scaled_data = model.scaler.fit_transform(veg_data[feature_cols])
        
        X, y = model.prepare_sequences(scaled_data)
        
        if len(X) > 10:
            split = int(len(X) * 0.8)
            X_train, X_val = X[:split], X[split:]
            y_train, y_val = y[:split], y[split:]
            
            model.build_model(X_train.shape[2])
            model.train(X_train, y_train, X_val, y_val, epochs=50)
            
            # Evaluate
            predictions = model.model.predict(X_val)
            mae = np.mean(np.abs(predictions.flatten() - y_val))
            print(f"  ✅ {veg}: MAE=₹{mae:.2f}")
            
            model.save_model(f'models/price_{veg}.h5')
            results[veg] = {'mae': mae}
    
    return results

def train_delivery_model(deliveries_df):
    """Train delivery time prediction model"""
    print("\n🔄 Training Delivery Time Prediction Model...")
    
    if len(deliveries_df) < 100:
        print("  ⚠️ Insufficient delivery data for training")
        return {}
    
    deliveries_df['scheduled_time'] = pd.to_datetime(deliveries_df['scheduled_date'])
    deliveries_df['actual_delivery_time'] = pd.to_datetime(deliveries_df['delivered_date'])
    deliveries_df['delivery_minutes'] = (
        deliveries_df['actual_delivery_time'] - deliveries_df['scheduled_time']
    ).dt.total_seconds() / 60
    
    # Remove outliers
    deliveries_df = deliveries_df[deliveries_df['delivery_minutes'].between(30, 480)]
    
    model = DeliveryTimePredictor()
    processed_df = model.preprocess_features(deliveries_df)
    
    # Prepare features and target
    X = processed_df[model.feature_columns]
    y = processed_df['delivery_minutes']
    
    # Split
    from sklearn.model_selection import train_test_split
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    # Train
    model.build_neural_network(X_train.shape[1])
    model.train(X_train.values, y_train.values, X_test.values, y_test.values, epochs=100)
    
    # Evaluate
    predictions = model.model.predict(X_test.values)
    mae = np.mean(np.abs(predictions.flatten() - y_test.values))
    print(f"  ✅ Delivery Time Model: MAE={mae:.1f} minutes")
    
    model.save_model('models/delivery_time_model.pkl')
    
    return {'mae': mae}

async def main():
    print("=" * 60)
    print("🧠 SmartVeg ML Model Training")
    print("=" * 60)
    
    # Fetch data
    print("\n📊 Fetching training data from database...")
    stocks_df, deliveries_df = await fetch_training_data()
    print(f"  ✅ Loaded {len(stocks_df)} stock records")
    print(f"  ✅ Loaded {len(deliveries_df)} delivery records")
    
    # Train models
    demand_results = train_demand_model(stocks_df)
    price_results = train_price_model(stocks_df)
    delivery_results = train_delivery_model(deliveries_df)
    
    # Summary
    print("\n" + "=" * 60)
    print("📈 Training Summary")
    print("=" * 60)
    print(f"Demand Models Trained: {len(demand_results)}")
    print(f"Price Models Trained: {len(price_results)}")
    print(f"Delivery Model Trained: {len(delivery_results) > 0}")
    
    print("\n✅ All models trained successfully!")
    print("   Models saved in 'backend/ml/models/' directory")

if __name__ == "__main__":
    asyncio.run(main())