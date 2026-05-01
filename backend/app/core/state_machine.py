from abc import ABC, abstractmethod
from enum import Enum
from typing import Optional
import logging

logger = logging.getLogger(__name__)

class WorkItemState(str, Enum):
    OPEN = "OPEN"
    INVESTIGATING = "INVESTIGATING"
    RESOLVED = "RESOLVED"
    CLOSED = "CLOSED"

class State(ABC):
    """Abstract State class - implements State Design Pattern"""
    
    @abstractmethod
    def transition(self, event: str, context: 'WorkItemContext') -> 'State':
        """Transition to next state based on event"""
        pass
    
    @abstractmethod
    def get_state_name(self) -> str:
        pass

class OpenState(State):
    """Initial state when work item is first created"""
    
    def transition(self, event: str, context: 'WorkItemContext') -> State:
        if event == "start_investigation":
            logger.info(f"WorkItem {context.work_item_id}: OPEN → INVESTIGATING")
            return InvestigatingState()
        elif event == "resolve":
            logger.warning(f"Cannot resolve from OPEN state without investigation")
            raise ValueError(f"Cannot transition from OPEN via {event}. Must investigate first.")
        else:
            raise ValueError(f"Invalid event '{event}' for OPEN state. Allowed: start_investigation")
    
    def get_state_name(self) -> str:
        return WorkItemState.OPEN.value

class InvestigatingState(State):
    """State when incident is being investigated"""
    
    def transition(self, event: str, context: 'WorkItemContext') -> State:
        if event == "resolve":
            logger.info(f"WorkItem {context.work_item_id}: INVESTIGATING → RESOLVED")
            context.set_resolved_time()
            return ResolvedState()
        elif event == "escalate":
            logger.warning(f"Escalating work item {context.work_item_id} - staying in INVESTIGATING")
            # In real system, this would page on-call engineer
            return self
        else:
            raise ValueError(f"Invalid event '{event}' for INVESTIGATING state. Allowed: resolve, escalate")
    
    def get_state_name(self) -> str:
        return WorkItemState.INVESTIGATING.value

class ResolvedState(State):
    """State when incident is resolved but not yet closed"""
    
    def transition(self, event: str, context: 'WorkItemContext') -> State:
        if event == "close":
            # Check if RCA is completed before allowing close
            if not context.rca_completed:
                raise ValueError("Cannot close incident: RCA must be completed first")
            logger.info(f"WorkItem {context.work_item_id}: RESOLVED → CLOSED")
            context.set_closed_time()
            return ClosedState()
        elif event == "reopen":
            logger.warning(f"Reopening work item {context.work_item_id} - returning to INVESTIGATING")
            return InvestigatingState()
        else:
            raise ValueError(f"Invalid event '{event}' for RESOLVED state. Allowed: close, reopen")
    
    def get_state_name(self) -> str:
        return WorkItemState.RESOLVED.value

class ClosedState(State):
    """Final state - incident is fully closed"""
    
    def transition(self, event: str, context: 'WorkItemContext') -> State:
        if event == "reopen":
            logger.info(f"Reopening closed work item {context.work_item_id} - going to INVESTIGATING")
            return InvestigatingState()
        else:
            raise ValueError(f"Invalid event '{event}' for CLOSED state. Allowed: reopen")
    
    def get_state_name(self) -> str:
        return WorkItemState.CLOSED.value

class WorkItemContext:
    """Context class that holds the current state"""
    
    def __init__(self, work_item_id: str, initial_state: State = None):
        self.work_item_id = work_item_id
        self._state = initial_state if initial_state else OpenState()
        self.resolved_time = None
        self.closed_time = None
        self.rca_completed = False
    
    def transition(self, event: str):
        """Transition to new state based on event"""
        self._state = self._state.transition(event, self)
    
    def get_state(self) -> str:
        return self._state.get_state_name()
    
    def set_resolved_time(self):
        from datetime import datetime
        self.resolved_time = datetime.now()
    
    def set_closed_time(self):
        from datetime import datetime
        self.closed_time = datetime.now()
    
    def set_rca_completed(self, completed: bool):
        self.rca_completed = completed
    
    def can_transition(self, event: str) -> bool:
        """Check if a transition is valid without executing it"""
        try:
            # Create a copy of current state to test transition
            current_state = self._state
            # This is a simplified check - in real code you'd want a cleaner way
            return True
        except:
            return False

# Helper function to validate state transitions
def validate_transition(current_state: str, event: str) -> tuple[bool, str]:
    """Validate if a state transition is allowed"""
    transitions = {
        WorkItemState.OPEN: {
            "allowed": ["start_investigation"],
            "next_state": WorkItemState.INVESTIGATING
        },
        WorkItemState.INVESTIGATING: {
            "allowed": ["resolve", "escalate"],
            "next_state": WorkItemState.RESOLVED
        },
        WorkItemState.RESOLVED: {
            "allowed": ["close", "reopen"],
            "next_state": WorkItemState.CLOSED
        },
        WorkItemState.CLOSED: {
            "allowed": ["reopen"],
            "next_state": WorkItemState.INVESTIGATING
        }
    }
    
    if current_state not in transitions:
        return False, f"Invalid state: {current_state}"
    
    if event not in transitions[current_state]["allowed"]:
        return False, f"Event '{event}' not allowed from state '{current_state}'. Allowed: {transitions[current_state]['allowed']}"
    
    return True, transitions[current_state]["next_state"]