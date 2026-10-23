from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import random

app = FastAPI()

# This allows your Netlify/phone app to talk to this server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

open_trades = {}

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

@app.get("/")
def read_root():
    return {"status": "Rucaren Backend is Awake!"}

@app.get("/health")
def health_check():
    return {"status": "ok", "message": "Server is running perfectly"}

@app.get("/balance")
def get_balance():
    return {"balance": 168.55, "equity": 168.55, "currency": "USD"}

@app.post("/order")
def place_order(order: OrderRequest):
    position_id = str(random.randint(10000000, 99999999))
    open_trades[position_id] = order.dict()
    return {
        "success": True, 
        "message": "Order opened successfully", 
        "position_id": position_id
    }

@app.post("/close")
def close_order(req: CloseRequest):
    if req.position_id in open_trades:
        del open_trades[req.position_id]
    return {"success": True, "message": "Position closed successfully"}
