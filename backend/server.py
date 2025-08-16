from fastapi import FastAPI, APIRouter, UploadFile, File, Form, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from motor.motor_asyncio import AsyncIOMotorGridFSBucket
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional
import uuid
from datetime import datetime, timedelta
from passlib.context import CryptContext
from jose import jwt, JWTError

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Auth setup
JWT_SECRET = os.environ.get('JWT_SECRET', 'dev_insecure_secret_change_me')
JWT_ALG = 'HS256'
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 days for MVP
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Models
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class UserPublic(BaseModel):
    id: str
    email: EmailStr
    name: Optional[str] = None
    created_at: datetime

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    name: Optional[str] = None

class RFQCreate(BaseModel):
    material: str
    quantity: int
    tolerance: Optional[str] = None
    roughness: Optional[str] = None
    part_marking: Optional[bool] = False
    certification: Optional[str] = None
    notes: Optional[str] = None

class RFQ(BaseModel):
    id: str
    user_id: str
    material: str
    quantity: int
    tolerance: Optional[str] = None
    roughness: Optional[str] = None
    part_marking: Optional[bool] = False
    certification: Optional[str] = None
    notes: Optional[str] = None
    cad_filename: Optional[str] = None
    cad_file_id: Optional[str] = None
    created_at: datetime

class Quote(BaseModel):
    id: str
    rfq_id: str
    supplier_name: str
    price: float
    currency: str = "EUR"
    lead_time_days: int
    notes: Optional[str] = None
    created_at: datetime

class Order(BaseModel):
    id: str
    rfq_id: str
    quote_id: str
    status: str  # created, pending_payment, paid, in_production, shipped
    created_at: datetime

class Payment(BaseModel):
    id: str
    order_id: str
    amount: float
    currency: str = "EUR"
    status: str  # pending, paid
    created_at: datetime

# Utility functions
async def get_user_by_email(email: str):
    return await db.users.find_one({"email": email})

async def get_user(user_id: str):
    return await db.users.find_one({"id": user_id})

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALG)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(status_code=401, detail="Could not validate credentials")
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALG])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = await get_user(user_id)
    if not user:
        raise credentials_exception
    return user

# Basic endpoints
@api_router.get("/")
async def root():
    return {"message": "OK", "service": "milling-aggregator"}

# Auth endpoints
@api_router.post("/auth/register", response_model=UserPublic)
async def register(user: UserCreate):
    existing = await get_user_by_email(user.email)
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    user_id = str(uuid.uuid4())
    hashed = get_password_hash(user.password)
    user_doc = {
        "id": user_id,
        "email": user.email,
        "name": user.name,
        "password_hash": hashed,
        "created_at": datetime.utcnow(),
    }
    await db.users.insert_one(user_doc)
    return UserPublic(id=user_id, email=user.email, name=user.name, created_at=user_doc["created_at"])

@api_router.post("/auth/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = await get_user_by_email(form_data.username)
    if not user or not verify_password(form_data.password, user.get("password_hash", "")):
        raise HTTPException(status_code=400, detail="Incorrect email or password")
    token = create_access_token({"sub": user["id"]})
    return Token(access_token=token)

@api_router.get("/me", response_model=UserPublic)
async def me(current_user=Depends(get_current_user)):
    return UserPublic(id=current_user["id"], email=current_user["email"], name=current_user.get("name"), created_at=current_user["created_at"])

# RFQ endpoints
ALLOWED_EXTS = {"dxf", "dwg", "step", "stp", "iges", "igs", "stl", "zip"}

@api_router.post("/rfqs", response_model=RFQ)
async def create_rfq(
    material: str = Form(...),
    quantity: int = Form(...),
    tolerance: Optional[str] = Form(None),
    roughness: Optional[str] = Form(None),
    part_marking: Optional[bool] = Form(False),
    certification: Optional[str] = Form(None),
    notes: Optional[str] = Form(None),
    cad_file: Optional[UploadFile] = File(None),
    current_user=Depends(get_current_user),
):
    cad_filename = None
    cad_file_id = None
    if cad_file:
        ext = cad_file.filename.split('.')[-1].lower()
        if ext not in ALLOWED_EXTS:
            raise HTTPException(status_code=400, detail="Unsupported file type")
        # Save to GridFS
        try:
            bucket = AsyncIOMotorGridFSBucket(db)
            data = await cad_file.read()
            file_id = await bucket.upload_from_stream(cad_file.filename, data)
            cad_filename = cad_file.filename
            cad_file_id = str(file_id)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"File upload failed: {str(e)}")

    rfq_id = str(uuid.uuid4())
    rfq_doc = {
        "id": rfq_id,
        "user_id": current_user["id"],
        "material": material,
        "quantity": int(quantity),
        "tolerance": tolerance,
        "roughness": roughness,
        "part_marking": bool(part_marking),
        "certification": certification,
        "notes": notes,
        "cad_filename": cad_filename,
        "cad_file_id": cad_file_id,
        "created_at": datetime.utcnow(),
    }
    await db.rfqs.insert_one(rfq_doc)

    # Auto-generate mock quotes for MVP aha
    await generate_mock_quotes(rfq_id)

    return RFQ(**rfq_doc)

@api_router.get("/rfqs", response_model=List[RFQ])
async def list_rfqs(current_user=Depends(get_current_user)):
    rfqs = await db.rfqs.find({"user_id": current_user["id"]}).sort("created_at", -1).to_list(100)
    return [RFQ(**r) for r in rfqs]

@api_router.get("/rfqs/{rfq_id}", response_model=RFQ)
async def get_rfq(rfq_id: str, current_user=Depends(get_current_user)):
    rfq = await db.rfqs.find_one({"id": rfq_id, "user_id": current_user["id"]})
    if not rfq:
        raise HTTPException(status_code=404, detail="RFQ not found")
    return RFQ(**rfq)

# Quotes
async def generate_mock_quotes(rfq_id: str):
    import random
    suppliers = [
        ("CNCWorks GmbH", 1.0),
        ("PrecisionMills AG", 1.05),
        ("Alpha Machining", 0.95),
    ]
    base = random.uniform(120.0, 380.0)
    for name, factor in suppliers:
        q = {
            "id": str(uuid.uuid4()),
            "rfq_id": rfq_id,
            "supplier_name": name,
            "price": round(base * factor, 2),
            "currency": "EUR",
            "lead_time_days": random.randint(5, 21),
            "notes": "Includes standard QA, EXW terms.",
            "created_at": datetime.utcnow(),
        }
        await db.quotes.insert_one(q)

@api_router.get("/quotes", response_model=List[Quote])
async def list_quotes(rfq_id: Optional[str] = None, current_user=Depends(get_current_user)):
    # Only return quotes for user's RFQs
    rfq_filter = {"user_id": current_user["id"]}
    rfqs = await db.rfqs.find(rfq_filter, {"id": 1}).to_list(1000)
    rfq_ids = {r["id"] for r in rfqs}
    q_filter = {}
    if rfq_id:
        if rfq_id not in rfq_ids:
            return []
        q_filter["rfq_id"] = rfq_id
    else:
        q_filter["rfq_id"] = {"$in": list(rfq_ids)}
    quotes = await db.quotes.find(q_filter).sort("price", 1).to_list(1000)
    return [Quote(**q) for q in quotes]

# Orders
@api_router.post("/quotes/{quote_id}/accept", response_model=Order)
async def accept_quote(quote_id: str, current_user=Depends(get_current_user)):
    quote = await db.quotes.find_one({"id": quote_id})
    if not quote:
        raise HTTPException(status_code=404, detail="Quote not found")
    rfq = await db.rfqs.find_one({"id": quote["rfq_id"], "user_id": current_user["id"]})
    if not rfq:
        raise HTTPException(status_code=403, detail="Not authorized for this RFQ")
    order = {
        "id": str(uuid.uuid4()),
        "rfq_id": rfq["id"],
        "quote_id": quote_id,
        "status": "pending_payment",
        "created_at": datetime.utcnow(),
    }
    await db.orders.insert_one(order)
    return Order(**order)

@api_router.get("/orders", response_model=List[Order])
async def list_orders(current_user=Depends(get_current_user)):
    rfqs = await db.rfqs.find({"user_id": current_user["id"]}, {"id": 1}).to_list(1000)
    rfq_ids = {r["id"] for r in rfqs}
    orders = await db.orders.find({"rfq_id": {"$in": list(rfq_ids)}}).sort("created_at", -1).to_list(1000)
    return [Order(**o) for o in orders]

# Payments
@api_router.post("/orders/{order_id}/pay", response_model=Payment)
async def pay_order(order_id: str, current_user=Depends(get_current_user)):
    order = await db.orders.find_one({"id": order_id})
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    rfq = await db.rfqs.find_one({"id": order["rfq_id"], "user_id": current_user["id"]})
    if not rfq:
        raise HTTPException(status_code=403, detail="Not authorized for this order")
    # Mock payment = create payment record and set order status
    quote = await db.quotes.find_one({"id": order["quote_id"]})
    amount = float(quote.get("price", 0.0)) if quote else 0.0
    payment = {
        "id": str(uuid.uuid4()),
        "order_id": order_id,
        "amount": amount,
        "currency": "EUR",
        "status": "paid",
        "created_at": datetime.utcnow(),
    }
    await db.payments.insert_one(payment)
    await db.orders.update_one({"id": order_id}, {"$set": {"status": "paid"}})
    return Payment(**payment)

@api_router.get("/payments", response_model=List[Payment])
async def list_payments(current_user=Depends(get_current_user)):
    rfqs = await db.rfqs.find({"user_id": current_user["id"]}, {"id": 1}).to_list(1000)
    rfq_ids = {r["id"] for r in rfqs}
    orders = await db.orders.find({"rfq_id": {"$in": list(rfq_ids)}}, {"id": 1}).to_list(1000)
    order_ids = {o["id"] for o in orders}
    payments = await db.payments.find({"order_id": {"$in": list(order_ids)}}).sort("created_at", -1).to_list(1000)
    return [Payment(**p) for p in payments]

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()