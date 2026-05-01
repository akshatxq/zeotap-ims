import pytest
from unittest.mock import AsyncMock, patch, MagicMock

class TestDebouncer:
    
    @pytest.mark.asyncio
    async def test_debouncer_creates_single_work_item_for_multiple_signals(self):
        """Debouncer creates only one work item for multiple signals in window"""
        
        # Mock Redis client
        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(return_value=None)
        mock_redis.setex = AsyncMock(return_value=True)
        
        # Mock get_redis to return our mock
        with patch('app.core.debouncer.get_redis', return_value=mock_redis):
            from app.core.debouncer import get_or_create_work_item
            
            component_id = "test_component"
            
            # Create first work item
            work_item_id_1 = await get_or_create_work_item(component_id, "sig_1", "P1")
            
            # Mock second call to return existing work item
            mock_redis.get = AsyncMock(return_value=work_item_id_1)
            
            # Second signal should return same work item
            work_item_id_2 = await get_or_create_work_item(component_id, "sig_2", "P1")
            
            # Third signal should return same work item
            work_item_id_3 = await get_or_create_work_item(component_id, "sig_3", "P1")
            
            # All should be the same ID
            assert work_item_id_1 == work_item_id_2 == work_item_id_3