import pytest
from datetime import datetime, timedelta
from app.models.rca import RCAModel

class TestRCAValidation:
    
    def test_rca_rejects_fix_under_20_chars(self):
        """RCA rejects fix description under 20 characters"""
        with pytest.raises(ValueError) as exc_info:
            RCAModel(
                incident_start=datetime.now() - timedelta(hours=1),
                incident_end=datetime.now(),
                root_cause_category="INFRA",
                fix_applied="too short",  # Only 9 characters
                prevention_steps="This is a valid prevention step with more than 20 characters",
                impact_description="Test impact"
            )
        assert "Fix description must be at least 20 characters" in str(exc_info.value)
    
    def test_rca_rejects_empty_prevention_steps(self):
        """RCA rejects empty prevention steps"""
        with pytest.raises(ValueError) as exc_info:
            RCAModel(
                incident_start=datetime.now() - timedelta(hours=1),
                incident_end=datetime.now(),
                root_cause_category="CONFIG",
                fix_applied="This is a valid fix description with more than 20 characters",
                prevention_steps="",  # Empty
                impact_description="Test impact"
            )
        assert "Prevention steps must be at least 20 characters" in str(exc_info.value)
    
    def test_rca_rejects_end_time_before_start(self):
        """RCA rejects end time before start time"""
        with pytest.raises(ValueError) as exc_info:
            RCAModel(
                incident_start=datetime.now(),
                incident_end=datetime.now() - timedelta(hours=1),  # End before start
                root_cause_category="NETWORK",
                fix_applied="This is a valid fix description with more than 20 characters",
                prevention_steps="This is a valid prevention step with more than 20 characters",
                impact_description="Test impact"
            )
        assert "End time must be after start time" in str(exc_info.value)
    
    def test_rca_rejects_invalid_category(self):
        """RCA rejects invalid root cause category"""
        with pytest.raises(ValueError) as exc_info:
            RCAModel(
                incident_start=datetime.now() - timedelta(hours=1),
                incident_end=datetime.now(),
                root_cause_category="INVALID_CATEGORY",  # Invalid
                fix_applied="This is a valid fix description with more than 20 characters",
                prevention_steps="This is a valid prevention step with more than 20 characters",
                impact_description="Test impact"
            )
        assert "Category must be one of" in str(exc_info.value)
    
    def test_rca_accepts_valid_complete_object(self):
        """RCA accepts valid complete object"""
        start_time = datetime.now() - timedelta(hours=2)
        end_time = datetime.now()
        
        rca = RCAModel(
            incident_start=start_time,
            incident_end=end_time,
            root_cause_category="CODE",
            fix_applied="This is a valid fix description with more than 20 characters",
            prevention_steps="This is a valid prevention step with more than 20 characters",
            impact_description="Test impact description"
        )
        
        assert rca.root_cause_category == "CODE"
        assert rca.fix_applied is not None
        assert rca.prevention_steps is not None
    
    def test_rca_calculates_mttr_correctly(self):
        """RCA calculates MTTR correctly in minutes"""
        start_time = datetime.now() - timedelta(hours=2, minutes=30)  # 150 minutes
        end_time = datetime.now()
        
        rca = RCAModel(
            incident_start=start_time,
            incident_end=end_time,
            root_cause_category="INFRA",
            fix_applied="This is a valid fix description with more than 20 characters",
            prevention_steps="This is a valid prevention step with more than 20 characters",
            impact_description="Test impact"
        )
        
        # Round to handle floating point precision
        assert round(rca.mttr_minutes, 2) == 150.00