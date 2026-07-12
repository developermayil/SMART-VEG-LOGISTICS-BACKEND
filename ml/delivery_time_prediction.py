import numpy as np
import pandas as pd
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, Dropout, LSTM, BatchNormalization
from sklearn.ensemble import RandomForestRegressor
import joblib

class DeliveryTimePredictor:
    """
    Predict delivery ETA based on historical data
    """
    
    def __init__(self):
        self.model = None
        self.feature_columns = [
            'distance_km', 'traffic_score', 'weather_condition',
            'vehicle_type_encoded', 'driver_experience_days',
            'hour_of_day', 'day_of_week', 'is_peak_hour'
        ]
        
    def preprocess_features(self, df):
        """
        Prepare features for delivery time prediction
        """
        df = df.copy()
        
        # Time features
        df['hour_of_day'] = pd.to_datetime(df['scheduled_time']).dt.hour
        df['day_of_week'] = pd.to_datetime(df['scheduled_time']).dt.dayofweek
        df['is_peak_hour'] = df['hour_of_day'].isin([8, 9, 17, 18, 19]).astype(int)
        
        # Traffic score based on time and day (0-1 scale)
        def calculate_traffic_score(hour, day):
            if day >= 5:  # Weekend
                return 0.3
            if hour in [8, 9, 17, 18]:
                return 0.9
            elif hour in [7, 10, 16, 19]:
                return 0.7
            else:
                return 0.4
        
        df['traffic_score'] = df.apply(
            lambda x: calculate_traffic_score(x['hour_of_day'], x['day_of_week']), 
            axis=1
        )
        
        return df
    
    def build_neural_network(self, input_dim):
        """
        Build neural network for ETA prediction
        """
        self.model = Sequential([
            Dense(128, activation='relu', input_dim=input_dim),
            BatchNormalization(),
            Dropout(0.3),
            
            Dense(64, activation='relu'),
            BatchNormalization(),
            Dropout(0.2),
            
            Dense(32, activation='relu'),
            
            Dense(1, activation='linear')  # Minutes
        ])
        
        self.model.compile(
            optimizer='adam',
            loss='huber',
            metrics=['mae']
        )
        
        return self.model
    
    def train(self, X_train, y_train, X_val, y_val, epochs=100):
        """
        Train the delivery time predictor
        """
        self.model.fit(
            X_train, y_train,
            validation_data=(X_val, y_val),
            epochs=epochs,
            batch_size=32,
            callbacks=[
                EarlyStopping(patience=10, restore_best_weights=True)
            ],
            verbose=1
        )
    
    def predict_eta(self, features):
        """
        Predict delivery ETA in minutes
        """
        pred_minutes = self.model.predict(features)
        return pred_minutes.flatten()