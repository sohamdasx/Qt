from fastapi import FastAPI, HTTPException
import yfinance as yf
import pandas as pd
from pydantic import BaseModel

# 1. Initialize the FastAPI application
app = FastAPI(title="BSE Quant Sifter")

# 2. Define the expected shape of incoming requests
class TickerRequest(BaseModel):
    symbol: str 

@app.post("/sift_single")
async def sift_single_stock(request: TickerRequest):
    try:
        # 3. Fetch historical data (1 year needed to calculate a 200-day metric)
        stock = yf.Ticker(request.symbol)
        df = stock.history(period="1y")

        # 4. Guardrail: Ensure we have enough data to do the math
        if len(df) < 200:
            return {"symbol": request.symbol, "is_candidate": False, "reason": "Insufficient data"}

        # 5. Calculate the 200-day Exponential Moving Average (EMA)
        df['EMA_200'] = df['Close'].ewm(span=200, adjust=False).mean()

        # 6. Calculate Volume Z-Score (Using a 20-day rolling window)
        df['Vol_Mean_20'] = df['Volume'].rolling(window=20).mean()
        df['Vol_Std_20'] = df['Volume'].rolling(window=20).std()
        df['Vol_Z_Score'] = (df['Volume'] - df['Vol_Mean_20']) / df['Vol_Std_20']

        # 7. Isolate the most recent trading day's data
        latest = df.iloc[-1]

        # 8. Apply the High-Pass Filter Logic
        price_above_ema = latest['Close'] > latest['EMA_200']
        high_volume_spike = latest['Vol_Z_Score'] > 2.0

        is_candidate = bool(price_above_ema and high_volume_spike)

        # 9. Return the structured JSON response
        return {
            "symbol": request.symbol,
            "is_candidate": is_candidate,
            "metrics": {
                "close": float(latest['Close']),
                "ema_200": float(latest['EMA_200']),
                "vol_z_score": float(latest['Vol_Z_Score'])
            }
        }

    except Exception as e:
         # Instead of crashing the whole app, we gracefully reject the stock
         # and pass the error message back so we can see what went wrong!
         return {
             "symbol": request.symbol, 
             "is_candidate": False, 
             "reason": f"Sifter Error: {str(e)}"
         }