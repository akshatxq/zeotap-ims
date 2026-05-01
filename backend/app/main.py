from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from contextlib import asynccontextmanager
import asyncio
import logging
from datetime import datetime

from app.api import signals, incidents
from app.core.queue import process_queue_worker, get_queue_metrics
from app.core.redis_client import init_redis, close_redis
from app.db.mongo import init_mongo, close_mongo
from app.db.postgres import init_postgres, close_postgres

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configure rate limiter
limiter = Limiter(key_func=get_remote_address)

# Track startup time for uptime
startup_time = datetime.now()

@asynccontextmanager
async def lifespan(app: FastAPI):
    global startup_time
    startup_time = datetime.now()
    
    # Startup
    logger.info("🚀 Starting up the IMS backend...")
    
    # Initialize all databases
    await init_redis()
    await init_mongo()
    await init_postgres()
    
    # Start the queue worker
    worker_task = asyncio.create_task(process_queue_worker())
    
    # Start metrics reporter
    metrics_task = asyncio.create_task(metrics_reporter())
    
    yield
    
    # Shutdown
    logger.info("👋 Shutting down...")
    worker_task.cancel()
    metrics_task.cancel()
    await close_redis()
    await close_mongo()
    await close_postgres()

async def metrics_reporter():
    """Print throughput metrics every 5 seconds"""
    prev_processed = 0
    while True:
        await asyncio.sleep(5)
        metrics = await get_queue_metrics()
        
        current_processed = metrics["total_signals_processed"]
        rate = (current_processed - prev_processed) / 5
        
        print(f"[METRICS] 📊 Signals/sec: {rate:.1f} | Queue: {metrics['queue_depth']} | "
              f"Dropped: {metrics['dropped_signals']} | "
              f"Work Items: {metrics['work_items_created']} | "
              f"Debounced: {metrics['signals_debounced']} | "
              f"Total: {metrics['total_signals_received']}")
        
        prev_processed = current_processed

app = FastAPI(
    title="Zeotap Incident Management System",
    description="Mission-critical IMS for SRE internship assignment",
    version="1.0.0",
    lifespan=lifespan
)

# Add rate limiter exception handler
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(signals.router)
app.include_router(incidents.router)

@app.get("/")
async def root():
    return {
        "message": "Zeotap IMS is running!",
        "status": "healthy",
        "endpoints": {
            "POST /signals": "Ingest a signal (rate limited: 1000/min)",
            "GET /signals/metrics": "View queue metrics",
            "GET /signals/recent": "Get recent signals for live feed",
            "GET /work-items": "List all work items",
            "GET /health": "Health check with per-component status"
        }
    }


@app.get("/health")
async def health_check():
    """Enhanced health check with per-component status"""
    from app.core.redis_client import get_redis
    from app.db.mongo import signals_collection, database
    from app.db.postgres import async_session_maker
    from sqlalchemy import text
    
    # Check Redis
    redis_status = "down"
    try:
        redis = await get_redis()
        await redis.ping()
        redis_status = "ok"
    except Exception as e:
        logger.error(f"Redis health check failed: {e}")
    
    # Check MongoDB - FIX THIS
    mongo_status = "down"
    try:
        # Try a simple ping command
        await database.command("ping")
        mongo_status = "ok"
    except Exception as e:
        logger.error(f"MongoDB health check failed: {e}")
    
    # Check PostgreSQL
    postgres_status = "down"
    try:
        async with async_session_maker() as session:
            await session.execute(text("SELECT 1"))
            postgres_status = "ok"
    except Exception as e:
        logger.error(f"PostgreSQL health check failed: {e}")
    
    # Get queue metrics
    metrics = await get_queue_metrics()
    
    # Calculate uptime
    uptime_seconds = (datetime.now() - startup_time).total_seconds()
    
    return {
        "status": "ok" if all([redis_status == "ok", mongo_status == "ok", postgres_status == "ok"]) else "degraded",
        "service": "backend",
        "uptime_seconds": uptime_seconds,
        "components": {
            "redis": redis_status,
            "mongodb": mongo_status,
            "postgresql": postgres_status
        },
        "queue": {
            "depth": metrics["queue_depth"],
            "max_size": metrics["max_queue_size"],
            "utilization": round(metrics["queue_utilization_percent"], 2)
        },
        "metrics": {
            "total_signals_received": metrics["total_signals_received"],
            "total_signals_processed": metrics["total_signals_processed"],
            "dropped_signals": metrics["dropped_signals"],
            "work_items_created": metrics["work_items_created"],
            "signals_debounced": metrics["signals_debounced"]
        }
    }
    """Enhanced health check with per-component status"""
    from app.core.redis_client import get_redis
    from app.db.mongo import signals_collection, database
    from app.db.postgres import async_session_maker
    from sqlalchemy import text
    
    # Check Redis
    redis_status = "down"
    try:
        redis = await get_redis()
        await redis.ping()
        redis_status = "ok"
    except Exception as e:
        logger.error(f"Redis health check failed: {e}")
    
    # Check MongoDB - FIX THIS
    mongo_status = "down"
    try:
        # Try a simple ping command
        await database.command("ping")
        mongo_status = "ok"
    except Exception as e:
        logger.error(f"MongoDB health check failed: {e}")
    
    # Check PostgreSQL
    postgres_status = "down"
    try:
        async with async_session_maker() as session:
            await session.execute(text("SELECT 1"))
            postgres_status = "ok"
    except Exception as e:
        logger.error(f"PostgreSQL health check failed: {e}")
    
    # Get queue metrics
    metrics = await get_queue_metrics()
    
    # Calculate uptime
    uptime_seconds = (datetime.now() - startup_time).total_seconds()
    
    return {
        "status": "ok" if all([redis_status == "ok", mongo_status == "ok", postgres_status == "ok"]) else "degraded",
        "service": "backend",
        "uptime_seconds": uptime_seconds,
        "components": {
            "redis": redis_status,
            "mongodb": mongo_status,
            "postgresql": postgres_status
        },
        "queue": {
            "depth": metrics["queue_depth"],
            "max_size": metrics["max_queue_size"],
            "utilization": round(metrics["queue_utilization_percent"], 2)
        },
        "metrics": {
            "total_signals_received": metrics["total_signals_received"],
            "total_signals_processed": metrics["total_signals_processed"],
            "dropped_signals": metrics["dropped_signals"],
            "work_items_created": metrics["work_items_created"],
            "signals_debounced": metrics["signals_debounced"]
        }
    }
    """Enhanced health check with per-component status"""
    from app.core.redis_client import get_redis
    from app.db.mongo import signals_collection
    from app.db.postgres import async_session_maker
    from sqlalchemy import text
    
    # Check Redis
    redis_status = "down"
    try:
        redis = await get_redis()
        await redis.ping()
        redis_status = "ok"
    except Exception as e:
        logger.error(f"Redis health check failed: {e}")
    
    # Check MongoDB
    mongo_status = "down"
    try:
        if signals_collection:
            await signals_collection.find_one()
            mongo_status = "ok"
    except Exception as e:
        logger.error(f"MongoDB health check failed: {e}")
    
    # Check PostgreSQL
    postgres_status = "down"
    try:
        async with async_session_maker() as session:
            await session.execute(text("SELECT 1"))
            postgres_status = "ok"
    except Exception as e:
        logger.error(f"PostgreSQL health check failed: {e}")
    
    # Get queue metrics
    metrics = await get_queue_metrics()
    
    # Calculate uptime
    uptime_seconds = (datetime.now() - startup_time).total_seconds()
    
    return {
        "status": "ok" if all([redis_status == "ok", mongo_status == "ok", postgres_status == "ok"]) else "degraded",
        "service": "backend",
        "uptime_seconds": uptime_seconds,
        "components": {
            "redis": redis_status,
            "mongodb": mongo_status,
            "postgresql": postgres_status
        },
        "queue": {
            "depth": metrics["queue_depth"],
            "max_size": metrics["max_queue_size"],
            "utilization": round(metrics["queue_utilization_percent"], 2)
        },
        "metrics": {
            "total_signals_received": metrics["total_signals_received"],
            "total_signals_processed": metrics["total_signals_processed"],
            "dropped_signals": metrics["dropped_signals"],
            "work_items_created": metrics["work_items_created"],
            "signals_debounced": metrics["signals_debounced"]
        }
    }