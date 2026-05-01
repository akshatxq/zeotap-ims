from motor.motor_asyncio import AsyncIOMotorClient
from app.core.retry import retry_with_backoff
import os
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

# Global variables
mongo_client: Optional[AsyncIOMotorClient] = None
database = None
signals_collection = None

async def init_mongo():
    """Initialize MongoDB connection"""
    global mongo_client, database, signals_collection
    
    try:
        mongo_host = os.getenv('MONGO_HOST', 'mongodb')
        mongo_port = os.getenv('MONGO_PORT', '27017')
        mongo_user = os.getenv('MONGO_USER', 'zeotap')
        mongo_password = os.getenv('MONGO_PASSWORD', 'zeotap123')
        
        mongo_url = f"mongodb://{mongo_user}:{mongo_password}@{mongo_host}:{mongo_port}"
        logger.info(f"Connecting to MongoDB at {mongo_host}:{mongo_port}")
        
        mongo_client = AsyncIOMotorClient(mongo_url)
        database = mongo_client.ims
        signals_collection = database.signals
        
        # Test the connection
        await mongo_client.admin.command('ping')
        
        # Create indexes for better performance
        await signals_collection.create_index("component_id")
        await signals_collection.create_index("timestamp")
        await signals_collection.create_index("work_item_id")
        
        logger.info("✅ MongoDB connected successfully")
        return mongo_client
    except Exception as e:
        logger.error(f"❌ MongoDB connection failed: {e}")
        raise

async def close_mongo():
    """Close MongoDB connection"""
    global mongo_client
    if mongo_client:
        mongo_client.close()
        logger.info("MongoDB connection closed")

async def store_raw_signal(signal: Dict[str, Any], work_item_id: Optional[str] = None) -> str:
    """Store raw signal in MongoDB with retry logic"""
    from datetime import datetime
    import time
    
    global signals_collection
    
    if signals_collection is None:
        raise Exception("MongoDB not initialized")
    
    if 'timestamp' not in signal:
        signal['timestamp'] = time.time()
    
    signal_to_store = {
        **signal,
        "work_item_id": work_item_id,
        "stored_at": datetime.now(),
        "processed": True
    }
    
    async def _insert():
        result = await signals_collection.insert_one(signal_to_store)
        logger.info(f"✅ Signal stored in MongoDB with id: {result.inserted_id}")
        return str(result.inserted_id)
    
    return await retry_with_backoff(_insert, max_attempts=3, base_delay=0.5)


async def get_signals_by_work_item(work_item_id: str) -> list:
    """Retrieve all signals linked to a work item"""
    global signals_collection
    
    if signals_collection is None:
        logger.error("MongoDB signals_collection is not initialized!")
        return []
    
    try:
        cursor = signals_collection.find({"work_item_id": work_item_id})
        signals = await cursor.to_list(length=100)
        
        # Convert ObjectId to string for JSON serialization
        for signal in signals:
            if "_id" in signal:
                signal["_id"] = str(signal["_id"])
        
        return signals
    except Exception as e:
        logger.error(f"Error fetching signals: {e}")
        return []

async def get_recent_signals(limit: int = 50) -> list:
    """Get recent signals for live feed"""
    global signals_collection
    
    if signals_collection is None:
        logger.error("MongoDB signals_collection is not initialized!")
        return []
    
    try:
        signals = await signals_collection.find().sort("timestamp", -1).limit(limit).to_list(length=limit)
        # Convert ObjectId to string for JSON serialization
        for signal in signals:
            if "_id" in signal:
                signal["_id"] = str(signal["_id"])
        return signals
    except Exception as e:
        logger.error(f"Error fetching recent signals: {e}")
        return []