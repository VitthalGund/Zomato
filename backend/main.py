from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from contextlib import asynccontextmanager
import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file from backend directory
env_path = Path(__file__).parent / '.env'
load_dotenv(dotenv_path=env_path)

# MongoDB connection
mongo_client = None
db = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    global mongo_client, db
    mongo_uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
    mongo_client = AsyncIOMotorClient(mongo_uri)
    db = mongo_client.zomato_edgevision
    
    # Create indexes for VerificationLog collection
    await db.verification_logs.create_index([("merchant_id", 1), ("verified_timestamp", 1)])
    await db.verification_logs.create_index("order_id")
    await db.verification_logs.create_index("fraud_flag")
    
    # Create indexes for MerchantVelocityState collection
    await db.merchant_velocity_state.create_index("merchant_id", unique=True)
    await db.merchant_velocity_state.create_index("last_calculated")
    await db.merchant_velocity_state.create_index("active_kpt_penalty_minutes")
    
    # Create indexes for Order collection
    await db.orders.create_index("order_id", unique=True)
    await db.orders.create_index("merchant_id")
    await db.orders.create_index("order_creation_timestamp")
    
    # Create indexes for MenuItem collection
    await db.menu_items.create_index([("item_id", 1), ("merchant_id", 1)], unique=True)
    await db.menu_items.create_index("merchant_id")
    
    print("Connected to MongoDB")
    
    yield
    
    # Shutdown
    if mongo_client:
        mongo_client.close()
        print("Closed MongoDB connection")

app = FastAPI(
    title="Zomato EdgeVision API",
    description="Edge-computing system for AI-verified food package timestamps",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {
        "message": "Zomato EdgeVision API",
        "version": "1.0.0",
        "status": "running"
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

# Import and register routers
from backend.routers import verification

app.include_router(verification.router)
