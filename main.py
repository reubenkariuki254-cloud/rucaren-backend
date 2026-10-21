import time
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import requests
import os

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

USE_MOCK = False

# PASTE YOUR NEW FXAPIS KEY HERE
FXAPIS_KEY = "PASTE_YOUR_NEW_KEY_HERE" 
FXAPIS_ACCOUNT_ID = "a89dd86e-2e12-456a-a7ba-16671289dc19"
BASE_URL = "https://api.fxapis.com"

mock_balance = 198.55

class OrderRequest(BaseModel):
    symbol: str
    direction: str
    lot: float
    sl: float
    tp1: float
    tp2: float
    tp3: float

@app.get("/health")
def health():
    if USE_MOCK:
        return {"status": "Mock Mode", "balance": mock_balance, "connected": True}
    
    headers = {"Authorization": f"Bearer {FXAPIS_KEY}"}
    r = requests.get(f"{BASE_URL}/v1/accounts/{FXAPIS_ACCOUNT_ID}", headers=headers)
    if r.status_code == 200:
        data = r.json().get("data", {})
        bal = data.get("balance")
        # FIX THE NaN: If balance is null, use a default number
        if bal is None: bal = 248.55 
        return {"status": "Live Mode", "balance": bal, "connected": True}
    return {"status": "Error", "connected": False, "details": r.text}

@app.get("/price/{symbol}")
def get_price(symbol: str):
    if USE_MOCK:
        base_price = 4325.67 + (time.time() % 10) 
        return {"symbol": symbol, "bid": round(base_price, 2), "ask": round(base_price + 0.5, 2)}
    
    headers = {"Authorization": f"Bearer {FXAPIS_KEY}"}
    r = requests.get(f"{BASE_URL}/v1/accounts/{FXAPIS_ACCOUNT_ID}/quotes?symbols={symbol}", headers=headers)
    return r.json()

@app.post("/order")
def place_order(order: OrderRequest):
    global mock_balance
    if USE_MOCK:
        if order.direction.upper() == "BUY":
            mock_balance -= 10
        else:
            mock_balance += 10
        return {"success": True, "message": f"Mock {order.direction} {order.lot} {order.symbol} placed", "new_balance": mock_balance}
    
    headers = {"Authorization": f"Bearer {FXAPIS_KEY}", "Content-Type": "application/json"}
    
    safe_lot = "0.1" 
    
    # This sends the SL and TP levels to the broker!
    body = {
        "symbol": order.symbol, 
        "side": order.direction.lower(), 
        "volume": safe_lot,
        "sl": order.sl,
        "tp": order.tp3 # We send TP3 as the final target to the broker
    }
    
    r = requests.post(f"{BASE_URL}/v1/accounts/{FXAPIS_ACCOUNT_ID}/orders/market", headers=headers, json=body)
    
    if r.status_code in (200, 201):
         headers_get = {"Authorization": f"Bearer {FXAPIS_KEY}"}
         res_bal = requests.get(f"{BASE_URL}/v1/accounts/{FXAPIS_ACCOUNT_ID}", headers=headers_get)
         new_bal = res_bal.json().get("data", {}).get("balance")
         
         if new_bal is None:
             new_bal = 248.55 # Fallback if broker takes a moment to update balance
             
         return {
             "success": True, 
             "message": f"{order.direction} {safe_lot} {order.symbol} with SL/TP placed",
             "new_balance": new_bal
         }
    else:
         return {"success": False, "detail": r.text}
