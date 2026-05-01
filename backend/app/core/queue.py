import asyncio
import logging
from typing import Dict, Any, Set
from app.core.debouncer import get_or_create_work_item
from datetime import datetime

logger = logging.getLogger(__name__)

# Bounded queue
signal_queue: asyncio.Queue = asyncio.Queue(maxsize=50000)

# Track created work items
_created_work_items: Set[str] = set()

# Metrics
metrics = {
    "total_signals_received": 0,
    "total_signals_processed": 0,
    "dropped_signals": 0,
    "queue_overflow_count": 0,
    "work_items_created": 0,
    "signals_debounced": 0
}

async def enqueue_signal(signal: Dict[str, Any]) -> bool:
    metrics["total_signals_received"] += 1
    try:
        signal_queue.put_nowait(signal)
        return True
    except asyncio.QueueFull:
        metrics["dropped_signals"] += 1
        metrics["queue_overflow_count"] += 1
        logger.warning(f"Queue full! Signal dropped. Total dropped: {metrics['dropped_signals']}")
        return False

async def process_queue_worker():
    logger.info("🚀 Queue worker started - waiting for signals...")
    
    while True:
        try:
            signal = await signal_queue.get()
            
            component_id = signal.get('component_id', 'unknown')
            severity = signal.get('severity', 'P1')
            signal_id = f"sig_{component_id}_{int(datetime.now().timestamp())}"
            
            logger.info(f"📨 Processing signal from: {component_id}")
            
            # Store in MongoDB
            try:
                from app.db.mongo import store_raw_signal
                await store_raw_signal(signal, None)
            except Exception as mongo_error:
                logger.error(f"MongoDB storage failed: {mongo_error}")
            
            # Apply debouncing logic
            work_item_id = await get_or_create_work_item(component_id, signal_id, severity)
            
            # Track work items
            if work_item_id not in _created_work_items:
                _created_work_items.add(work_item_id)
                try:
                    from app.db.postgres import create_work_item
                    # ✅ Create work item WITHOUT signal_ids
                    work_item_data = {
                        "id": work_item_id,
                        "component_id": component_id,
                        "severity": severity,
                        "status": "OPEN"
                    }
                    await create_work_item(work_item_data)
                    metrics["work_items_created"] += 1
                    logger.info(f"✨ NEW work item created: {work_item_id}")
                except Exception as db_error:
                    logger.error(f"Failed to create work item: {db_error}")
            else:
                metrics["signals_debounced"] += 1
                logger.info(f"🔄 Signal DEBOUNCED to work item: {work_item_id}")
            
            signal_queue.task_done()
            metrics["total_signals_processed"] += 1
            
        except Exception as e:
            logger.error(f"Error processing signal: {e}", exc_info=True)
            signal_queue.task_done()

async def get_queue_metrics() -> Dict[str, Any]:
    return {
        "queue_depth": signal_queue.qsize(),
        "max_queue_size": signal_queue.maxsize,
        "queue_utilization_percent": (signal_queue.qsize() / signal_queue.maxsize) * 100 if signal_queue.maxsize > 0 else 0,
        **metrics
    }