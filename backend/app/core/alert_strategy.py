from abc import ABC, abstractmethod
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

class AlertStrategy(ABC):
    """Abstract Strategy class - implements Strategy Design Pattern"""
    
    @abstractmethod
    async def send_alert(self, work_item: Dict[str, Any]) -> None:
        """Send alert based on severity strategy"""
        pass

class P0Strategy(AlertStrategy):
    """P0 Critical - Page everyone immediately, create war room"""
    
    async def send_alert(self, work_item: Dict[str, Any]) -> None:
        logger.error(f"🚨 P0 ALERT - CRITICAL INCIDENT!")
        logger.error(f"   Component: {work_item['component_id']}")
        logger.error(f"   Action: Paging on-call engineer, creating war room")
        logger.error(f"   Work Item ID: {work_item['id']}")
        # In production: Send to PagerDuty, OpsGenie, Slack, SMS, Phone call
        # For demo: Just log with high visibility
        print(f"\n{'='*60}")
        print(f"🔴 P0 CRITICAL ALERT 🔴")
        print(f"Component: {work_item['component_id']}")
        print(f"Action Required: IMMEDIATE - Create war room, page all engineers")
        print(f"Work Item: {work_item['id']}")
        print(f"{'='*60}\n")

class P1Strategy(AlertStrategy):
    """P1 High - Page on-call engineer immediately"""
    
    async def send_alert(self, work_item: Dict[str, Any]) -> None:
        logger.warning(f"⚠️ P1 ALERT - High Severity Incident")
        logger.warning(f"   Component: {work_item['component_id']}")
        logger.warning(f"   Action: Paging on-call engineer")
        logger.warning(f"   Work Item ID: {work_item['id']}")
        print(f"\n🟠 P1 HIGH ALERT | Component: {work_item['component_id']} | Paging on-call")

class P2Strategy(AlertStrategy):
    """P2 Medium - Slack notification only, no page"""
    
    async def send_alert(self, work_item: Dict[str, Any]) -> None:
        logger.info(f"📢 P2 ALERT - Medium severity (degraded performance)")
        logger.info(f"   Component: {work_item['component_id']}")
        logger.info(f"   Action: Sending Slack notification")
        print(f"\n🟡 P2 ALERT | Component: {work_item['component_id']} | Slack notification sent")

# Component to severity mapping (from the assignment guide)
COMPONENT_STRATEGIES = {
    "RDBMS_PRIMARY": P0Strategy(),
    "RDBMS_SECONDARY": P1Strategy(),
    "API_GATEWAY": P0Strategy(),
    "MCP_HOST": P1Strategy(),
    "MCP_HOST_01": P1Strategy(),
    "CACHE_CLUSTER": P2Strategy(),
    "ASYNC_QUEUE": P1Strategy(),
    "LOAD_BALANCER": P1Strategy(),
    "MESSAGE_BROKER": P1Strategy(),
    # Default fallback
    "DEFAULT": P1Strategy()
}

async def send_alert_for_work_item(work_item: Dict[str, Any]) -> None:
    """
    Send alert based on work item's component and severity
    Uses Strategy pattern to choose appropriate alerting method
    """
    component_id = work_item.get('component_id', 'UNKNOWN')
    severity = work_item.get('severity', 'P1')
    
    # First try by component-specific strategy (from guide's component type mapping)
    strategy = COMPONENT_STRATEGIES.get(component_id)
    
    if not strategy:
        # Fallback to severity-based strategy
        if severity == "P0":
            strategy = P0Strategy()
        elif severity == "P1":
            strategy = P1Strategy()
        else:
            strategy = P2Strategy()
    
    await strategy.send_alert(work_item)
    
    # Return the strategy type for metrics
    return strategy.__class__.__name__