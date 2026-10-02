"""
Mock Trade Order API
---------------------
A small FastAPI service that mimics the shape of a trading platform backend:
- login/session
- market data lookup
- order entry
- order status (trade lifecycle)

This is intentionally simple. The point of this project isn't the app itself —
it's everything we wrap around it: containers, CI/CD, cloud deploy, monitoring.
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from datetime import datetime
import uuid
import random

app = FastAPI(
    title="Mock Trade Order API",
    description="A toy trading API used to practice DevOps end-to-end.",
    version="0.1.0",
)

# --- In-memory "databases" (resets every restart — that's fine for this project) ---
SESSIONS: dict[str, dict] = {}
ORDERS: dict[str, dict] = {}

FAKE_PRICES = {
    "AAPL": 232.15,
    "TD": 85.40,
    "MSFT": 512.30,
    "SHOP": 118.75,
}


# ---------- Schemas ----------
class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    session_id: str
    username: str
    issued_at: datetime


class OrderRequest(BaseModel):
    session_id: str
    symbol: str
    side: str  # "buy" or "sell"
    quantity: int


class OrderResponse(BaseModel):
    order_id: str
    status: str
    symbol: str
    side: str
    quantity: int
    fill_price: float | None
    created_at: datetime


# ---------- Health & root ----------
@app.get("/")
def root():
    return {"service": "mock-trade-api", "status": "ok"}


@app.get("/health")
def health():
    """Used by load balancers / uptime checks / container orchestrators."""
    return {"status": "healthy", "time": datetime.utcnow()}


# ---------- Login ----------
@app.post("/login", response_model=LoginResponse)
def login(req: LoginRequest):
    if not req.username or not req.password:
        raise HTTPException(status_code=400, detail="username and password required")

    session_id = str(uuid.uuid4())
    SESSIONS[session_id] = {"username": req.username, "issued_at": datetime.utcnow()}
    return LoginResponse(
        session_id=session_id, username=req.username, issued_at=SESSIONS[session_id]["issued_at"]
    )


# ---------- Market data ----------
@app.get("/market-data/{symbol}")
def market_data(symbol: str):
    symbol = symbol.upper()
    if symbol not in FAKE_PRICES:
        raise HTTPException(status_code=404, detail=f"No market data for symbol '{symbol}'")

    # small random jitter to simulate a live feed
    price = round(FAKE_PRICES[symbol] * random.uniform(0.995, 1.005), 2)
    return {"symbol": symbol, "price": price, "as_of": datetime.utcnow()}


# ---------- Order entry ----------
@app.post("/orders", response_model=OrderResponse)
def create_order(req: OrderRequest):
    if req.session_id not in SESSIONS:
        raise HTTPException(status_code=401, detail="invalid or expired session")

    symbol = req.symbol.upper()
    if symbol not in FAKE_PRICES:
        raise HTTPException(status_code=404, detail=f"Unknown symbol '{symbol}'")

    if req.side.lower() not in ("buy", "sell"):
        raise HTTPException(status_code=400, detail="side must be 'buy' or 'sell'")

    if req.quantity <= 0:
        raise HTTPException(status_code=400, detail="quantity must be positive")

    order_id = str(uuid.uuid4())
    fill_price = round(FAKE_PRICES[symbol] * random.uniform(0.995, 1.005), 2)

    order = {
        "order_id": order_id,
        "status": "filled",  # keep it simple: instant fill
        "symbol": symbol,
        "side": req.side.lower(),
        "quantity": req.quantity,
        "fill_price": fill_price,
        "created_at": datetime.utcnow(),
    }
    ORDERS[order_id] = order
    return OrderResponse(**order)


# ---------- Trade lifecycle / order status ----------
@app.get("/orders/{order_id}", response_model=OrderResponse)
def get_order(order_id: str):
    order = ORDERS.get(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="order not found")
    return OrderResponse(**order)


@app.get("/orders")
def list_orders():
    return {"count": len(ORDERS), "orders": list(ORDERS.values())}
