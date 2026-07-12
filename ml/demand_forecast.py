import numpy as np
import pandas as pd
from tensorflow.keras.models import Sequential, load_model
from tensorflow.keras.layers import LSTM, Dense, Dropout, GRU, Bidirectional
from tensorflow.keras.callbacks import EarlyStopping, ModelCheckpoint
from tensorflow.keras.optimizers import Adam
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import joblib
from datetime import datetime, timedelta
import os

class DemandForecastModel:
    """
    LSTM-based demand forecasting model for vegetable supply chain
    """
    
    def __init__(self, lookback_days=30, forecast_days=7):
        self.lookback_days = lookback_days
        self.forecast_days = forecast_days
        self.model = None
        self.scaler_X = MinMaxScaler()
        self.scaler_y = MinMaxScaler()
        self.is_trained = False
        
    def prepare_data(self, df, target_col='quantity'):
        """
        Prepare time series data for LSTM training
        
        Args:
            df: DataFrame with 'date' and target_col columns
            target_col: Column to forecast
        Returns:
            X, y arrays for training
        """
        # Sort by date
        df = df.sort_values('date')
        data = df[target_col].values.reshape(-1, 1)
        
        # Scale data
        scaled_data = self.scaler_X.fit_transform(data)
        
        # Create sequences
        X, y = [], []
        for i in range(self.lookback_days, len(scaled_data) - self.forecast_days + 1):
            X.append(scaled_data[i - self.lookback_days:i, 0])
            y.append(scaled_data[i:i + self.forecast_days, 0])
        
        return np.array(X), np.array(y)
    
    def build_lstm_model(self, input_shape):
        """
        Build LSTM model for demand forecasting
        """
        model = Sequential([
            # First LSTM layer
            LSTM(128, return_sequences=True, input_shape=input_shape),
            Dropout(0.2),
            
            # Second LSTM layer
            LSTM(64, return_sequences=True),
            Dropout(0.2),
            
            # Third LSTM layer
            LSTM(32),
            Dropout(0.2),
            
            # Output layer
            Dense(self.forecast_days)
        ])
        
        model.compile(
            optimizer=Adam(learning_rate=0.001),
            loss='huber',  # Robust to outliers
            metrics=['mae', 'mse']
        )
        
        return model
    
    def build_bilstm_model(self, input_shape):
        """
        Build Bidirectional LSTM for better sequence learning
        """
        model = Sequential([
            Bidirectional(LSTM(128, return_sequences=True), input_shape=input_shape),
            Dropout(0.2),
            Bidirectional(LSTM(64, return_sequences=True)),
            Dropout(0.2),
            Bidirectional(LSTM(32)),
            Dropout(0.2),
            Dense(self.forecast_days)
        ])
        
        model.compile(
            optimizer=Adam(learning_rate=0.001),
            loss='huber',
            metrics=['mae', 'mse']
        )
        
        return model
    
    def train(self, X_train, y_train, X_val=None, y_val=None, epochs=100, batch_size=32):
        """
        Train the forecasting model
        """
        # Reshape for LSTM: (samples, timesteps, features)
        X_train = X_train.reshape((X_train.shape[0], X_train.shape[1], 1))
        
        self.model = self.build_lstm_model((X_train.shape[1], 1))
        
        # Callbacks
        callbacks = [
            EarlyStopping(patience=15, restore_best_weights=True),
            ModelCheckpoint('models/best_demand_model.h5', save_best_only=True)
        ]
        
        # Train
        history = self.model.fit(
            X_train, y_train,
            validation_data=(X_val.reshape(X_val.shape[0], X_val.shape[1], 1), y_val) if X_val is not None else None,
            epochs=epochs,
            batch_size=batch_size,
            callbacks=callbacks,
            verbose=1
        )
        
        self.is_trained = True
        return history
    
    def predict(self, last_sequence):
        """
        Predict future demand
        """
        if not self.is_trained or self.model is None:
            raise ValueError("Model not trained yet")
        
        last_seq = last_sequence.reshape((1, len(last_sequence), 1))
        scaled_pred = self.model.predict(last_seq)
        
        # Inverse transform to original scale
        predictions = self.scaler_X.inverse_transform(scaled_pred.T).T
        
        return predictions.flatten()
    
    def evaluate(self, X_test, y_test):
        """
        Evaluate model performance
        """
        X_test_reshaped = X_test.reshape((X_test.shape[0], X_test.shape[1], 1))
        predictions = self.model.predict(X_test_reshaped)
        
        # Inverse transform
        y_actual = self.scaler_y.inverse_transform(y_test)
        y_pred = self.scaler_y.inverse_transform(predictions)
        
        mae = mean_absolute_error(y_actual.flatten(), y_pred.flatten())
        mse = mean_squared_error(y_actual.flatten(), y_pred.flatten())
        rmse = np.sqrt(mse)
        r2 = r2_score(y_actual.flatten(), y_pred.flatten())
        
        return {
            'mae': mae,
            'mse': mse,
            'rmse': rmse,
            'r2': r2
        }
    
    def save_model(self, path='models/demand_forecast_model.h5'):
        """Save model and scalers"""
        if self.model:
            self.model.save(path)
            joblib.dump(self.scaler_X, path.replace('.h5', '_scaler_X.pkl'))
            joblib.dump(self.scaler_y, path.replace('.h5', '_scaler_y.pkl'))
    
    def load_model(self, path='models/demand_forecast_model.h5'):
        """Load saved model"""
        self.model = load_model(path)
        self.scaler_X = joblib.load(path.replace('.h5', '_scaler_X.pkl'))
        self.scaler_y = joblib.load(path.replace('.h5', '_scaler_y.pkl'))
        self.is_trained = True