from fastapi import APIRouter, Request
from slowapi import Limiter
from slowapi.util import get_remote_address
from app.models.signal import Signal
from app.core.queue import enqueue_signal, get_queue_metrics
from app.db.mongo import get_recent_signals, signals_collection
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/signals", tags=["signals"])

# Create rate limiter instance
limiter = Limiter(key_func=get_remote_address)

@router.post("", status_code=202)
@limiter.limit("1000/minute")
async def ingest_signal(request: Request, signal: Signal):
    """
    Ingest a signal into the system.
    
    Rate Limit: 1000 requests per minute per IP address.
    Returns 202 Accepted immediately - processing happens async.
    """
    signal_dict = signal.dict()
    
    # Enqueue the signal (non-blocking)
    enqueued = await enqueue_signal(signal_dict)
    
    if not enqueued:
        logger.warning(f"Signal dropped due to backpressure: {signal.component_id}")
        return {
            "status": "accepted",
            "message": "Signal accepted but dropped due to high load",
            "dropped": True,
            "component_id": signal.component_id
        }
    
    return {
        "status": "accepted",
        "message": "Signal enqueued for processing",
        "component_id": signal.component_id
    }

@router.get("/metrics")
async def get_signal_metrics():
    """Get metrics about signal processing and queue health"""
    return await get_queue_metrics()

@router.get("/recent")
async def get_recent_signals_endpoint(limit: int = 50):
    """Get recent signals for live feed"""
    return await get_recent_signals(limit)