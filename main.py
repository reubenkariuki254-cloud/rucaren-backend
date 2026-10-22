import time
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import requests

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

USE_MOCK = False
FXAPIS_KEY = "fx_test_ee32748c_nZCVJqT38TXsj__lveSz4_Ohl2VjWWC97eUVY_fkPGw" # <--- CHECK YOUR KEY
FXAPIS_ACCOUNT_ID = "a89dd86e-2e12-456a-a7ba-16671289dc19"
BASE_URL = "https://api.fxapis.com"

class OrderRequest(BaseModel):
    symbol: str
    direction: str
    lot: float
    sl: float
    tp1: float
    tp2: float
    tp3: float

class CloseRequest(BaseModel):
    position_id: str

@app.get("/health")
def health():
    headers = {"Authorization": f"Bearer {FXAPIS_KEY}"}
    r = requests.get(f"{BASE_URL}/v1/accounts/{FXAPIS_ACCOUNT_ID}", headers=headers)
    if r.status_code == 200:
        data = r.json().get("data", {})
        bal = data.get("balance")
        if bal is None: bal = 0.0
        return {"status": "Live Mode", "balance": bal, "connected": True}
    return {"status": "Error", "connected": False, "details": r.text}

@app.post("/order")
def place_order(order: OrderRequest):
    headers = {"Authorization": f"Bearer {FXAPIS_KEY}", "Content-Type": "application/json"}
    
    body = {
        "symbol": order.symbol, 
        "side": order.direction.lower(), 
        "volume": "0.1",
        "sl": order.sl,
        "tp": order.tp3 
    }
    
    r = requests.post(f"{BASE_URL}/v1/accounts/{FXAPIS_ACCOUNT_ID}/orders/market", headers=headers, json=body)
    
    if r.status_code in (200, 201):
         res_data = r.json()
         position_id = res_data.get("data", {}).get("positionId") or res_data.get("positionId")
         
         return {"success": True, "message": f"{order.direction} placed", "position_id": position_id}
    else:
         return {"success": False, "detail": r.text}

@app.post("/close")
def close_trade(req: CloseRequest):
    headers = {"Authorization": f"Bearer {FXAPIS_KEY}", "Content-Type": "application/json"}
    body = {"positionId": req.position_id}
    r = requests.post(f"{BASE_URL}/v1/accounts/{FXAPIS_ACCOUNT_ID}/positions/close", headers=headers, json=body)
    
    if r.status_code in (200, 201):
        return {"success": True, "message": "Trade closed on MT5"}
    else:
        return {"success": False, "detail": r.text}
