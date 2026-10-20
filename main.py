import time
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

mock_balance = 198.55

class OrderRequest(BaseModel):
    symbol: str
    direction: str
    lot: float

@app.get("/health")
def health():
    return {"status": "Mock Mode", "balance": mock_balance, "connected": True}

@app.get("/price/{symbol}")
def get_price(symbol: str):
    return {"symbol": symbol, "bid": 4325.67, "ask": 4325.89}

@app.post("/order")
def place_order(order: OrderRequest):
    global mock_balance
    if order.direction.upper() == "BUY":
        mock_balance -= 10
    else:
        mock_balance += 10
    return {"success": True, "message": f"Mock {order.direction} {order.lot} {order.symbol}", "new_balance": mock_balance}
