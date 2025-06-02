import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout
import warnings
warnings.filterwarnings("ignore")

# Simulate training data from past signals
def prepare_lstm_data(signal_df):
    features = ['MACD', 'RSI', 'EMA_8', 'EMA_20', 'EMA_200', 'Close']
    df = signal_df[features].dropna()

    scaler = MinMaxScaler()
    scaled_data = scaler.fit_transform(df)

    X = []
    y = []

    for i in range(15, len(scaled_data)):
        X.append(scaled_data[i-15:i])
        y.append(scaled_data[i][-1])  # Predicting Close price

    return np.array(X), np.array(y), scaler

# Build LSTM model
def build_model(input_shape):
    model = Sequential()
    model.add(LSTM(units=50, return_sequences=True, input_shape=input_shape))
    model.add(Dropout(0.2))
    model.add(LSTM(units=50))
    model.add(Dropout(0.2))
    model.add(Dense(1))  # Output: predicted price or score
    model.compile(optimizer='adam', loss='mse')
    return model

# Train model and predict
def train_and_predict(signal_df):
    X, y, scaler = prepare_lstm_data(signal_df)

    if X.shape[0] < 10:
        print("⚠️ Not enough data for LSTM training.")
        return None

    model = build_model((X.shape[1], X.shape[2]))
    model.fit(X, y, epochs=20, batch_size=16, verbose=0)

    # Predict last 15-candle sequence
    last_sequence = X[-1].reshape(1, X.shape[1], X.shape[2])
    prediction = model.predict(last_sequence)[0][0]

    # Inverse scale to get actual value
    predicted_close = scaler.inverse_transform(
        np.hstack([np.zeros((1, X.shape[2] - 1)), [[prediction]]])
    )[:, -1][0]

    return round(predicted_close, 2)

# Example usage
if __name__ == "__main__":
    print("🔬 Running LSTM Optimizer Test...")
    from strategies import calculate_indicators
    import yfinance as yf

    df = yf.download("RELIANCE.NS", period="6mo", interval="1d", progress=False)
    df = calculate_indicators(df)
    predicted_close = train_and_predict(df)

    if predicted_close:
        print(f"📈 Predicted Close Price: ₹{predicted_close}")
