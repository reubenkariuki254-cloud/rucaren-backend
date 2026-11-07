from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
import random

try:
    from metaapi_cloud_sdk import MetaApi
except ImportError:
    MetaApi = None

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

META_API_TOKEN = os.getenv("META_API_TOKEN", "")
META_ACCOUNT_ID_SYNTX = os.getenv("META_ACCOUNT_ID", "") 
META_ACCOUNT_ID_FOREX = os.getenv("META_ACCOUNT_ID_FOREX", "")

api = MetaApi(META_API_TOKEN) if MetaApi and META_API_TOKEN else None

class OrderRequest(BaseModel):
    symbol: str
    direction: str
    lot: float
    sl: float
    tp1: float
    tp2: float
    tp3: float
    accountType: str = "syntx"

class CloseRequest(BaseModel):
    position_id: str

@app.get("/health")
def health_check():
    return {"status": "ok", "message": "Server is running perfectly"}

@app.get("/balance")
async def get_balance(type: str = "syntx"):
    target_account = META_ACCOUNT_ID_SYNTX if type == "syntx" else META_ACCOUNT_ID_FOREX
    
    if not api or not target_account:
        if type == "syntx":
            return {"balance": 168.55, "equity": 168.55, "status": "Simulation"}
        else:
            return {"balance": 2500.00, "equity": 2500.00, "status": "Simulation"}
        
    try:
        account = await api.metatrader_account_api.get_account(target_account)
        if account.state != 'DEPLOYED':
            await account.deploy()
        await account.wait_connected()
        connection = account.get_rpc_connection()
        await connection.connect()
        await connection.wait_synchronized()
        info = await connection.get_account_information()
        return {"balance": info['balance'], "equity": info['equity']}
    except Exception as e:
        return {"balance": 0, "equity": 0, "error": str(e)}

@app.post("/order")
async def place_order(order: OrderRequest):
    target_account = META_ACCOUNT_ID_SYNTX if order.accountType == "syntx" else META_ACCOUNT_ID_FOREX
    
    if not api or not target_account:
        return {"success": True, "position_id": "SIM-" + str(random.randint(100000, 999999))}

    try:
        account = await api.metatrader_account_api.get_account(target_account)
        if account.state != 'DEPLOYED':
            await account.deploy()
        await account.wait_connected()
        connection = account.get_rpc_connection()
        await connection.connect()
        await connection.wait_synchronized()

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
    if not api:
        return {"success": True}
    try:
        account = await api.metatrader_account_api.get_account(META_ACCOUNT_ID_SYNTX)
        connection = account.get_rpc_connection()
        await connection.connect()
        await connection.wait_synchronized()
        await connection.close_position(req.position_id)
        return {"success": True}
    except Exception:
        try:
            account = await api.metatrader_account_api.get_account(META_ACCOUNT_ID_FOREX)
            connection = account.get_rpc_connection()
            await connection.connect()
            await connection.wait_synchronized()
            await connection.close_position(req.position_id)
            return {"success": True}
        except Exception as e:
            return {"success": False, "detail": str(e)}