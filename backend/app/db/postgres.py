from sqlalchemy import Column, String, DateTime, Float, Boolean, JSON, text, select, desc
from app.core.retry import retry_with_backoff
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base
from datetime import datetime
import os
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

Base = declarative_base()

# SQLAlchemy Models
class WorkItemModel(Base):
    __tablename__ = "work_items"
    
    id = Column(String, primary_key=True)
    component_id = Column(String, nullable=False)
    status = Column(String, nullable=False, default="OPEN")
    severity = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    resolved_at = Column(DateTime, nullable=True)
    closed_at = Column(DateTime, nullable=True)
    mttr_minutes = Column(Float, nullable=True)
    rca_completed = Column(Boolean, default=False)
    rca_data = Column(JSON, nullable=True)
    
class SignalLinkModel(Base):
    __tablename__ = "signal_links"
    
    id = Column(String, primary_key=True)
    signal_id = Column(String, nullable=False)
    work_item_id = Column(String, nullable=False)
    linked_at = Column(DateTime, default=datetime.now)

# Engine and session
engine = None
async_session_maker = None

async def init_postgres():
    """Initialize PostgreSQL connection"""
    global engine, async_session_maker
    
    pg_host = os.getenv('POSTGRES_HOST', 'postgres')
    pg_port = os.getenv('POSTGRES_PORT', '5432')
    pg_user = os.getenv('POSTGRES_USER', 'zeotap')
    pg_password = os.getenv('POSTGRES_PASSWORD', 'zeotap123')
    pg_db = os.getenv('POSTGRES_DB', 'ims')
    
    database_url = f"postgresql+asyncpg://{pg_user}:{pg_password}@{pg_host}:{pg_port}/{pg_db}"
    
    engine = create_async_engine(database_url, echo=False)
    async_session_maker = async_sessionmaker(engine, expire_on_commit=False)
    
    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    logger.info("✅ PostgreSQL connected and tables created")
    return engine

async def close_postgres():
    """Close PostgreSQL connection"""
    global engine
    if engine:
        await engine.dispose()
        logger.info("PostgreSQL connection closed")

async def create_work_item(work_item: Dict[str, Any]) -> str:
    """Create a new work item in PostgreSQL"""
    async with async_session_maker() as session:
        async with session.begin():
            # ✅ Only pass fields that exist in the model
            work_item_model = WorkItemModel(
                id=work_item['id'],
                component_id=work_item['component_id'],
                status=work_item.get('status', 'OPEN'),
                severity=work_item['severity']
            )
            session.add(work_item_model)
            await session.commit()
            logger.info(f"✅ Work item created: {work_item['id']}")
            return work_item['id']

async def get_work_item(work_item_id: str):
    """Get work item by ID"""
    try:
        async with async_session_maker() as session:
            result = await session.execute(
                select(WorkItemModel).where(WorkItemModel.id == work_item_id)
            )
            work_item = result.scalar_one_or_none()
            if work_item:
                return {
                    "id": work_item.id,
                    "component_id": work_item.component_id,
                    "status": work_item.status,
                    "severity": work_item.severity,
                    "created_at": work_item.created_at,
                    "updated_at": work_item.updated_at,
                    "resolved_at": work_item.resolved_at,
                    "closed_at": work_item.closed_at,
                    "mttr_minutes": work_item.mttr_minutes,
                    "rca_completed": work_item.rca_completed,
                    "rca_data": work_item.rca_data
                }
            return None
    except Exception as e:
        logger.error(f"Error getting work item {work_item_id}: {e}")
        return None

async def update_work_item_status(work_item_id: str, status: str, **kwargs) -> None:
    """Update work item status"""
    async with async_session_maker() as session:
        async with session.begin():
            result = await session.execute(
                select(WorkItemModel).where(WorkItemModel.id == work_item_id).with_for_update()
            )
            work_item = result.scalar_one_or_none()
            
            if work_item:
                work_item.status = status
                work_item.updated_at = datetime.now()
                
                for key, value in kwargs.items():
                    if hasattr(work_item, key):
                        setattr(work_item, key, value)
                
                await session.commit()
                logger.info(f"Work item {work_item_id} status updated to {status}")
            else:
                raise ValueError(f"Work item {work_item_id} not found")

async def update_work_item_rca(work_item_id: str, rca_data: Dict[str, Any]) -> None:
    """Update work item with RCA data"""
    async with async_session_maker() as session:
        async with session.begin():
            result = await session.execute(
                select(WorkItemModel).where(WorkItemModel.id == work_item_id).with_for_update()
            )
            work_item = result.scalar_one_or_none()
            
            if work_item:
                work_item.rca_data = rca_data
                work_item.rca_completed = True
                work_item.updated_at = datetime.now()
                
                await session.commit()
                logger.info(f"RCA completed for work item {work_item_id}")
            else:
                raise ValueError(f"Work item {work_item_id} not found")
            
            
async def link_signal_to_work_item(signal_id: str, work_item_id: str) -> None:
    """Link a signal to a work item"""
    try:
        async with async_session_maker() as session:
            async with session.begin():
                link = SignalLinkModel(
                    id=f"link_{signal_id}_{work_item_id}",
                    signal_id=signal_id,
                    work_item_id=work_item_id
                )
                session.add(link)
                await session.commit()
                logger.debug(f"Signal linked to work item")
    except Exception as e:
        logger.error(f"Error linking signal: {e}")