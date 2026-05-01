import logging
from datetime import datetime
from typing import Optional
from app.core.redis_client import get_redis
from app.core.alert_strategy import send_alert_for_work_item
from app.models.work_item import WorkItem, WorkItemStatus

logger = logging.getLogger(__name__)

DEBOUNCE_WINDOW_SECONDS = 10  # 10 second window as per guide

async def get_or_create_work_item(component_id: str, signal_id: str, severity: str = "P1") -> str:
    """
    Implements the debounce logic from the guide:
    - 100 signals for same component in 10 seconds → only 1 work item
    
    Now integrates with alert strategy
    """
    redis = await get_redis()
    redis_key = f"debounce:{component_id}"
    
    # Check if there's already a work item for this component
    existing_work_item_id = await redis.get(redis_key)
    
    if existing_work_item_id:
        # Work item already exists within the 10s window
        logger.info(f"🔄 Debounced: Component {component_id} already has work item {existing_work_item_id}")
        return existing_work_item_id
    else:
        # First signal for this component in the window - create work item
        logger.info(f"✨ Creating new work item for component {component_id}")
        
        # Create work item ID
        work_item_id = f"wi_{component_id}_{int(datetime.now().timestamp())}"
        
        # Create work item object
        work_item = WorkItem(
            id=work_item_id,
            component_id=component_id,
            severity=severity,
            status=WorkItemStatus.OPEN,
            signal_ids=[signal_id]
        )
        
        # TODO: Save to PostgreSQL (we'll implement in Step 5)
        
        # Send alert based on strategy
        await send_alert_for_work_item(work_item.model_dump())
        
        # Set Redis key with 10 second expiration
        await redis.setex(redis_key, DEBOUNCE_WINDOW_SECONDS, work_item_id)
        logger.info(f"🔒 Debounce window started for {component_id} - expires in {DEBOUNCE_WINDOW_SECONDS}s")
        
        return work_item_id


async def get_debounce_stats(component_id: str) -> Optional[dict]:
    """Check if a component is currently in a debounce window"""
    redis = await get_redis()
    redis_key = f"debounce:{component_id}"
    
    work_item_id = await redis.get(redis_key)
    
    if work_item_id:
        ttl = await redis.ttl(redis_key)
        return {
            "component_id": component_id,
            "work_item_id": work_item_id,
            "ttl_seconds": ttl,
            "is_debouncing": True
        }
    return {
        "component_id": component_id,
        "is_debouncing": False
    }
    
    