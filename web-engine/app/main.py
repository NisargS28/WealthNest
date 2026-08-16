import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# Configure logging FIRST so background tasks always print their errors
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()
# Fallbacks for different local dev setups
load_dotenv(dotenv_path="../frontend/.env.local")
load_dotenv(dotenv_path="../.env.local")
load_dotenv(dotenv_path=".env")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Ensure data directory exists
    os.makedirs("data", exist_ok=True)
    os.makedirs("uploads", exist_ok=True)
    yield
    # Shutdown

app = FastAPI(
    title="WealthNest API",
    description="Backend API for WealthNest family mutual fund portfolio management",
    version="0.4.0",
    lifespan=lifespan
)

# CORS configuration
allowed_origins_str = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000")
allowed_origins = [origin.strip() for origin in allowed_origins_str.split(",")]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routes will be imported here
from app.api import members, portfolios, imports, dashboard, holdings

app.include_router(members.router, prefix="/api", tags=["members"])
app.include_router(portfolios.router, prefix="/api", tags=["portfolios"])
app.include_router(imports.router, prefix="/api", tags=["imports"])
app.include_router(dashboard.router, prefix="/api", tags=["dashboard"])
app.include_router(holdings.router, prefix="/api", tags=["holdings"])

@app.get("/api/health")
def health_check():
    return {"status": "ok", "version": "0.4.0"}
