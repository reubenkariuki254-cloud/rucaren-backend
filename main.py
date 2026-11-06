from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from metaapi_cloud_sdk import MetaApi
import os

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# These are pulled securely from Render Environment Variables
META_API_TOKEN = os.getenv("META_API_TOKEN", "")
META_ACCOUNT_ID = os.getenv("META_ACCOUNT_ID", "")

api = MetaApi(META_API_TOKEN)

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

async def get_mt5_connection():
    account = await api.metatrader_account_api.get_account(META_ACCOUNT_ID)
    if account.state != 'DEPLOYED':
        await account.deploy()
    await account.wait_connected()
    connection = account.get_rpc_connection()
    await connection.connect()
    await connection.wait_synchronized()
    return connection

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.get("/balance")
async def get_balance():
    try:
        connection = await get_mt5_connection()
        info = await connection.get_account_information()
        return {"balance": info['balance'], "equity": info['equity']}
    except Exception as e:
        return {"balance": 0, "error": str(e)}

@app.post("/order")
async def place_order(order: OrderRequest):
    try:
        connection = await get_mt5_connection()
        
        if order.direction == "BUY":
            result = await connection.create_market_buy_order(
                order.symbol, order.lot, order.sl, order.tp3
            )
        else:
            result = await connection.create_market_sell_order(
                order.symbol, order.lot, order.sl, order.tp3
            )
            
        return {"success": True, "position_id": str(result['orderId'])}
    except Exception as e:
        return {"success": False, "detail": str(e)}

@app.post("/close")
async def close_position(req: CloseRequest):
    try:
        connection = await get_mt5_connection()
        await connection.close_position(req.position_id)
        return {"success": True}
    except Exception as e:
        return {"success": False, "detail": str(e)}