from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List
from enum import Enum

class WorkItemStatus(str, Enum):
    OPEN = "OPEN"
    INVESTIGATING = "INVESTIGATING"
    RESOLVED = "RESOLVED"
    CLOSED = "CLOSED"

class WorkItem(BaseModel):
    id: str
    component_id: str
    status: WorkItemStatus = WorkItemStatus.OPEN
    severity: str  # P0, P1, P2
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    resolved_at: Optional[datetime] = None
    closed_at: Optional[datetime] = None
    signal_ids: List[str] = []
    mttr_minutes: Optional[float] = None
    rca_completed: bool = False
    
    # ✅ Use ONLY model_config (NOT class Config)
    model_config = {
        "use_enum_values": True,
        "from_attributes": True
    }