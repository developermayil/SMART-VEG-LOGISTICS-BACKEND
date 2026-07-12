import numpy as np
import pandas as pd
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, GRU, Attention, Concatenate, Input
from tensorflow.keras.models import Model
from sklearn.preprocessing import StandardScaler
import joblib

class PricePredictionModel:
    """
    Multi-variate price prediction for vegetables
    Uses historical prices, seasonality, and external factors
    """
    
    def __init__(self, sequence_length=60):
        self.sequence_length = sequence_length
        self.model = None
        self.scaler = StandardScaler()
        
    def build_model(self, n_features):
        """
        Build hybrid CNN-LSTM model for price prediction
        """
        # Input layer
        inputs = Input(shape=(self.sequence_length, n_features))
        
        # CNN layers for feature extraction
        from tensorflow.keras.layers import Conv1D, MaxPooling1D, Flatten
        
        # Temporal CNN
        cnn_out = Conv1D(filters=64, kernel_size=3, activation='relu')(inputs)
        cnn_out = MaxPooling1D(pool_size=2)(cnn_out)
        cnn_out = Conv1D(filters=32, kernel_size=3, activation='relu')(cnn_out)
        
        # LSTM for sequence learning
        lstm_out = LSTM(64, return_sequences=True)(cnn_out)
        lstm_out = LSTM(32)(lstm_out)
        
        # Output layer
        outputs = Dense(1, activation='linear')(lstm_out)
        
        self.model = Model(inputs=inputs, outputs=outputs)
        self.model.compile(
            optimizer='adam',
            loss='huber',
            metrics=['mae']
        )
        
        return self.model
    
    def add_external_features(self, df):
        """
        Add engineered features for better prediction
        """
        df = df.copy()
        
        # Temporal features
        df['day_of_week'] = pd.to_datetime(df['date']).dt.dayofweek
        df['month'] = pd.to_datetime(df['date']).dt.month
        df['quarter'] = pd.to_datetime(df['date']).dt.quarter
        df['is_weekend'] = df['day_of_week'].isin([5, 6]).astype(int)
        
        # Lag features
        for lag in [1, 3, 7, 14, 30]:
            df[f'price_lag_{lag}'] = df['price'].shift(lag)
        
        # Rolling statistics
        for window in [7, 14, 30]:
            df[f'price_ma_{window}'] = df['price'].rolling(window).mean()
            df[f'price_std_{window}'] = df['price'].rolling(window).std()
        
        # Price momentum
        df['price_momentum'] = df['price'].pct_change(periods=7)
        
        return df.dropna()

    def prepare_sequences(self, data):
        """
        Prepare sequences for training
        """
        X, y = [], []
        for i in range(self.sequence_length, len(data) - 1):
            X.append(data[i - self.sequence_length:i])
            y.append(data[i, 0])  # Predict price (first column)
        
        return np.array(X), np.array(y)