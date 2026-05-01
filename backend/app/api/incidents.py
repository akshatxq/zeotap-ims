from fastapi import APIRouter, HTTPException
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy import select, desc, text
from sqlalchemy.orm import declarative_base
from sqlalchemy import Column, String, DateTime, Float, Boolean, JSON
from datetime import datetime
import os
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/work-items", tags=["work-items"])

# Create database connection directly in this file
DATABASE_URL = f"postgresql+asyncpg://zeotap:zeotap123@postgres:5432/ims"
engine = create_async_engine(DATABASE_URL, echo=False)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)

# Define model locally
Base = declarative_base()

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

@router.get("")
async def list_work_items():
    """List all work items"""
    try:
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(WorkItemModel).order_by(desc(WorkItemModel.created_at))
            )
            work_items = result.scalars().all()
            
            incidents = []
            for wi in work_items:
                incidents.append({
                    "id": wi.id,
                    "component_id": wi.component_id,
                    "status": wi.status,
                    "severity": wi.severity,
                    "created_at": wi.created_at.isoformat() if wi.created_at else None,
                    "updated_at": wi.updated_at.isoformat() if wi.updated_at else None,
                    "mttr_minutes": wi.mttr_minutes,
                    "rca_completed": wi.rca_completed
                })
            
            logger.info(f"✅ Returning {len(incidents)} work items")
            return incidents
    except Exception as e:
        logger.error(f"Error listing work items: {e}", exc_info=True)
        return []

@router.get("/{work_item_id}")
async def get_work_item_detail(work_item_id: str):
    """Get work item details with linked signals"""
    try:
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(WorkItemModel).where(WorkItemModel.id == work_item_id)
            )
            work_item = result.scalar_one_or_none()
            
            if not work_item:
                raise HTTPException(status_code=404, detail="Work item not found")
            
            # Get signals from MongoDB
            from app.db.mongo import get_signals_by_work_item
            signals = await get_signals_by_work_item(work_item_id)
            
            return {
                "id": work_item.id,
                "component_id": work_item.component_id,
                "status": work_item.status,
                "severity": work_item.severity,
                "created_at": work_item.created_at.isoformat() if work_item.created_at else None,
                "updated_at": work_item.updated_at.isoformat() if work_item.updated_at else None,
                "resolved_at": work_item.resolved_at.isoformat() if work_item.resolved_at else None,
                "closed_at": work_item.closed_at.isoformat() if work_item.closed_at else None,
                "mttr_minutes": work_item.mttr_minutes,
                "rca_completed": work_item.rca_completed,
                "rca_data": work_item.rca_data,
                "signals": signals,
                "signal_count": len(signals)
            }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting work item detail: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{work_item_id}/transition")
async def transition_state(work_item_id: str, event: str):
    """Transition work item state"""
    try:
        async with AsyncSessionLocal() as session:
            async with session.begin():
                result = await session.execute(
                    select(WorkItemModel).where(WorkItemModel.id == work_item_id)
                )
                work_item = result.scalar_one_or_none()
                
                if not work_item:
                    raise HTTPException(status_code=404, detail="Work item not found")
                
                # Simple state mapping
                if event == "start_investigation":
                    work_item.status = "INVESTIGATING"
                elif event == "resolve":
                    work_item.status = "RESOLVED"
                    work_item.resolved_at = datetime.now()
                elif event == "close":
                    work_item.status = "CLOSED"
                    work_item.closed_at = datetime.now()
                elif event == "reopen":
                    work_item.status = "OPEN"
                elif event == "escalate":
                    pass
                else:
                    raise HTTPException(status_code=400, detail=f"Unknown event: {event}")
                
                await session.commit()
                
                return {"status": "success", "new_state": work_item.status}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in transition: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{work_item_id}/rca")
async def submit_rca(work_item_id: str, rca: dict):
    """Submit RCA for a work item"""
    try:
        async with AsyncSessionLocal() as session:
            async with session.begin():
                result = await session.execute(
                    select(WorkItemModel).where(WorkItemModel.id == work_item_id)
                )
                work_item = result.scalar_one_or_none()
                
                if not work_item:
                    raise HTTPException(status_code=404, detail="Work item not found")
                
                if work_item.status != "RESOLVED":
                    raise HTTPException(status_code=400, detail="RCA can only be submitted for RESOLVED incidents")
                
                # Calculate MTTR
                from datetime import datetime as dt
                start = dt.fromisoformat(rca.get("incident_start", ""))
                end = dt.fromisoformat(rca.get("incident_end", ""))
                mttr = (end - start).total_seconds() / 60
                
                work_item.rca_data = rca
                work_item.rca_completed = True
                work_item.status = "CLOSED"
                work_item.mttr_minutes = mttr
                work_item.closed_at = datetime.now()
                
                await session.commit()
                
                return {
                    "status": "success",
                    "message": "RCA submitted successfully",
                    "mttr_minutes": mttr
                }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error submitting RCA: {e}")
        raise HTTPException(status_code=400, detail=str(e))