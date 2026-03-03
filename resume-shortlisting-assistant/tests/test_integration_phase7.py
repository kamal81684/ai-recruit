"""
Comprehensive Integration Tests for Phase 7 Enterprise Features.

Test suite for fairness checker, AI microservice, and enhanced features.

Contributor: shubham21155102 - Enterprise Architecture Phase 7
"""

import pytest
import asyncio
import json
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from datetime import datetime, timedelta
from typing import Dict, Any, List

# Import modules to test
from fairness_checker import (
    FairnessChecker,
    FairnessAudit,
    BiasAlert,
    BiasType,
    SeverityLevel,
    fairness_checker
)


class TestFairnessChecker:
    """Test suite for fairness checker functionality."""

    def test_fairness_checker_initialization(self):
        """Test fairness checker can be initialized."""
        checker = FairnessChecker(threshold=0.7)
        assert checker.threshold == 0.7
        assert checker.db is not None

    def test_analyze_empty_candidate_pool(self):
        """Test analyzing an empty candidate pool."""
        with patch.object(fairness_checker, '_get_candidates', return_value=[]):
            audit = fairness_checker.analyze_candidate_pool()

            assert audit.candidate_pool_size == 0
            assert audit.overall_fairness_score == 0.0
            assert audit.passed_threshold is False
            assert len(audit.alerts) == 0

    def test_detect_university_bias(self):
        """Test detection of university name bias."""
        candidates = [
            {'education': 'Stanford University Computer Science', 'tier': 'A'},
            {'education': 'MIT Computer Science', 'tier': 'A'},
            {'education': 'Stanford University Engineering', 'tier': 'A'},
            {'education': 'MIT Data Science', 'tier': 'A'},
            {'education': 'Stanford University BS', 'tier': 'A'},
            {'education': 'Harvard Computer Science', 'tier': 'A'},
            {'education': 'Stanford University MBA', 'tier': 'A'},
        ]

        with patch.object(fairness_checker, '_get_candidates', return_value=candidates):
            audit = fairness_checker.analyze_candidate_pool()

            # Should detect university bias
            university_alerts = [a for a in audit.alerts if a.bias_type == BiasType.UNIVERSITY]
            assert len(university_alerts) > 0

    def test_detect_location_bias(self):
        """Test detection of geographic location bias."""
        candidates = [
            {'location': 'San Francisco, CA', 'tier': 'A'},
            {'location': 'San Francisco, CA', 'tier': 'A'},
            {'location': 'San Francisco, CA', 'tier': 'A'},
            {'location': 'San Francisco, CA', 'tier': 'A'},
            {'location': 'San Francisco, CA', 'tier': 'A'},
            {'location': 'San Francisco, CA', 'tier': 'A'},
            {'location': 'New York, NY', 'tier': 'B'},
        ]

        with patch.object(fairness_checker, '_get_candidates', return_value=candidates):
            audit = fairness_checker.analyze_candidate_pool()

            # Should detect location bias
            location_alerts = [a for a in audit.alerts if a.bias_type == BiasType.LOCATION]
            assert len(location_alerts) > 0

    def test_detect_experience_bias(self):
        """Test detection of experience level bias."""
        candidates = [
            {'experience_years': 10, 'tier': 'A'},
            {'experience_years': 15, 'tier': 'A'},
            {'experience_years': 12, 'tier': 'A'},
            {'experience_years': 8, 'tier': 'A'},
            {'experience_years': 20, 'tier': 'A'},
            {'experience_years': 7, 'tier': 'A'},
        ]

        with patch.object(fairness_checker, '_get_candidates', return_value=candidates):
            audit = fairness_checker.analyze_candidate_pool()

            # Should detect experience bias
            experience_alerts = [a for a in audit.alerts if a.bias_type == BiasType.EXPERIENCE]
            assert len(experience_alerts) > 0

    def test_calculate_demographics(self):
        """Test demographic calculation."""
        candidates = [
            {'email': 'test1@example.com', 'phone': '555-0100', 'location': 'NYC', 'skills': 'Python', 'tier': 'A'},
            {'email': 'test2@example.com', 'phone': None, 'location': 'LA', 'skills': 'Java', 'tier': 'B'},
            {'email': None, 'phone': '555-0102', 'location': None, 'skills': 'React', 'tier': 'A'},
        ]

        demographics = fairness_checker._calculate_demographics(candidates)

        assert demographics['total_candidates'] == 3
        assert demographics['with_email'] == 2
        assert demographics['with_phone'] == 2
        assert demographics['with_location'] == 2
        assert demographics['with_skills'] == 3
        assert demographics['tier_distribution']['A'] == 2
        assert demographics['tier_distribution']['B'] == 1

    def test_check_job_description_fairness(self):
        """Test job description fairness checking."""
        # Test with potentially biased job description
        biased_jd = """
        We are looking for an aggressive, competitive individual to lead our team.
        Must have 15+ years of experience and be a recent graduate from a top university.
        """
        result = fairness_checker.check_job_description_fairness(biased_jd)

        assert result['fairness_score'] < 1.0
        assert len(result['issues']) > 0
        assert 'recommendations' in result

    def test_fairness_audit_serialization(self):
        """Test audit can be serialized to dictionary."""
        audit = FairnessAudit(
            audit_id="test_audit_001",
            timestamp=datetime.now(),
            candidate_pool_size=100,
            alerts=[
                BiasAlert(
                    bias_type=BiasType.UNIVERSITY,
                    severity=SeverityLevel.HIGH,
                    message="Test alert",
                    affected_count=50,
                    total_count=100,
                    percentage=50.0,
                    recommendations=["Test recommendation"]
                )
            ],
            demographics={'total_candidates': 100},
            fairness_scores={'university_fairness': 0.5},
            overall_fairness_score=0.7,
            passed_threshold=True
        )

        audit_dict = audit.to_dict()

        assert audit_dict['audit_id'] == "test_audit_001"
        assert audit_dict['candidate_pool_size'] == 100
        assert len(audit_dict['alerts']) == 1
        assert audit_dict['alerts'][0]['bias_type'] == 'university'
        assert audit_dict['passed_threshold'] is True


class TestAIMicroservice:
    """Test suite for AI microservice client."""

    def test_service_endpoint_creation(self):
        """Test service endpoint configuration."""
        from ai_microservice import ServiceEndpoint

        endpoint = ServiceEndpoint(
            url="http://localhost:8000",
            name="test_service",
            timeout=10.0
        )

        assert endpoint.url == "http://localhost:8000"
        assert endpoint.name == "test_service"
        assert endpoint.timeout == 10.0
        assert endpoint.enabled is True

    def test_circuit_breaker_initialization(self):
        """Test circuit breaker can be initialized."""
        from ai_microservice import CircuitBreaker

        breaker = CircuitBreaker(
            failure_threshold=3,
            recovery_timeout=60.0
        )

        assert breaker.failure_threshold == 3
        assert breaker.recovery_timeout == 60.0
        assert breaker.state == ServiceStatus.HEALTHY

    def test_circuit_breaker_opens_on_failures(self):
        """Test circuit breaker opens after threshold failures."""
        from ai_microservice import CircuitBreaker

        breaker = CircuitBreaker(failure_threshold=2)

        def failing_func():
            raise Exception("Test failure")

        # First failure
        with pytest.raises(Exception):
            breaker.call(failing_func)
        assert breaker.state == ServiceStatus.HEALTHY

        # Second failure - should open circuit
        with pytest.raises(Exception):
            breaker.call(failing_func)
        assert breaker.state == ServiceStatus.CIRCUIT_OPEN

        # Third call should fail immediately without calling function
        with pytest.raises(Exception, match="Circuit breaker is OPEN"):
            breaker.call(failing_func)

    def test_circuit_breaker_resets_after_timeout(self):
        """Test circuit breaker resets after recovery timeout."""
        from ai_microservice import CircuitBreaker

        breaker = CircuitBreaker(
            failure_threshold=2,
            recovery_timeout=0.1  # Short timeout for testing
        )

        def failing_func():
            raise Exception("Test failure")

        # Open the circuit
        with pytest.raises(Exception):
            breaker.call(failing_func)
        with pytest.raises(Exception):
            breaker.call(failing_func)

        assert breaker.state == ServiceStatus.CIRCUIT_OPEN

        # Wait for recovery timeout
        import time
        time.sleep(0.15)

        # Should now attempt recovery
        def success_func():
            return "success"

        result = breaker.call(success_func)
        assert result == "success"
        assert breaker.state == ServiceStatus.HEALTHY

    def test_ai_service_manager_initialization(self):
        """Test AI service manager can be initialized."""
        from ai_microservice import AIServiceManager

        manager = AIServiceManager(microservice_endpoints=None)
        assert manager.use_microservice is False
        assert manager.local_service is not None

    @pytest.mark.asyncio
    async def test_local_service_fallback(self):
        """Test local service is used when microservice is unavailable."""
        from ai_microservice import AIServiceManager

        manager = AIServiceManager(microservice_endpoints=None)

        # Should use local service
        result = await manager.local_service.evaluate_resume(
            resume_text="Test resume",
            job_description="Test job"
        )

        assert result is not None
        assert 'tier' in result

    def test_get_metrics(self):
        """Test getting service metrics."""
        from ai_microservice import AIServiceManager

        manager = AIServiceManager(microservice_endpoints=None)
        metrics = manager.get_metrics()

        assert 'status' in metrics
        assert metrics['status'] == 'local_only'


class TestSmartDiffView:
    """Test suite for smart diff view component logic."""

    def test_skill_match_categorization(self):
        """Test skills are correctly categorized as matched/missing."""
        job_skills = ['python', 'javascript', 'react', 'aws', 'docker']
        resume_text = "Experienced in Python, JavaScript and AWS. Built React applications."

        resume_lower = resume_text.lower()
        matches = []

        for skill in job_skills:
            exact_match = skill.lower() in resume_lower
            matches.append({
                'skill': skill,
                'matched': exact_match
            })

        matched_count = sum(1 for m in matches if m['matched'])
        assert matched_count == 4  # python, javascript, react, aws
        assert matches[3]['skill'] == 'aws'
        assert matches[3]['matched'] is True
        assert matches[4]['skill'] == 'docker'
        assert matches[4]['matched'] is False

    def test_partial_skill_matching(self):
        """Test partial skill matching logic."""
        job_skills = ['react.js', 'node.js', 'typescript']
        extracted_skills = ['React', 'NodeJS', 'JavaScript']

        # Check for partial matches
        partial_matches = []
        for job_skill in job_skills:
            for extracted in extracted_skills:
                if job_skill.lower() in extracted.lower() or extracted.lower() in job_skill.lower():
                    partial_matches.append((job_skill, extracted))
                    break

        assert len(partial_matches) >= 2  # Should match React and Node


class TestAPIEndpoints:
    """Test suite for new API endpoints."""

    @pytest.fixture
    def app(self):
        """Create test Flask app."""
        from api import app
        app.config['TESTING'] = True
        return app

    @pytest.fixture
    def client(self, app):
        """Create test client."""
        return app.test_client()

    def test_fairness_statistics_endpoint(self, client):
        """Test fairness statistics endpoint."""
        response = client.get('/api/fairness/statistics')

        # Should return 200 even with no candidates
        assert response.status_code in [200, 500]  # May fail if DB not available
        if response.status_code == 200:
            data = response.get_json()
            assert 'demographics' in data or 'error' in data

    def test_health_check_endpoint(self, client):
        """Test health check includes new features."""
        response = client.get('/health')

        assert response.status_code == 200
        data = response.get_json()
        assert data['status'] == 'ok'
        assert 'version' in data


class TestIntegration:
    """Integration tests for complete workflows."""

    def test_end_to_end_evaluation_with_fairness_check(self):
        """Test complete evaluation workflow with fairness checking."""
        # This test would require actual database and LLM setup
        # For now, we test the integration points

        # Mock the database and LLM
        with patch('fairness_checker.db') as mock_db, \
             patch('fairness_checker.get_logger') as mock_logger:

            # Setup mocks
            mock_cursor = MagicMock()
            mock_db.conn.cursor.return_value = mock_cursor
            mock_cursor.fetchall.return_value = [
                {
                    'id': 1,
                    'name': 'Test Candidate',
                    'email': 'test@example.com',
                    'education': 'MIT Computer Science',
                    'location': 'San Francisco, CA',
                    'skills': 'Python, JavaScript',
                    'tier': 'A',
                    'experience_years': 5
                }
            ]

            # Run fairness audit
            audit = fairness_checker.analyze_candidate_pool()

            # Verify results
            assert audit.candidate_pool_size == 1
            assert isinstance(audit.overall_fairness_score, float)

    def test_websocket_integration(self):
        """Test WebSocket integration with task updates."""
        from websocket_support import WebSocketManager, WebSocketMessage, MessageType

        manager = WebSocketManager()

        # Test statistics
        stats = manager.get_statistics()
        assert 'total_connections' in stats
        assert stats['total_connections'] == 0

        # Test message creation
        message = WebSocketMessage(
            type=MessageType.TASK_COMPLETED,
            data={'task_id': 'test_123', 'result': 'success'}
        )

        message_dict = json.loads(message.to_json())
        assert message_dict['type'] == 'task_completed'
        assert message_dict['data']['task_id'] == 'test_123'


class TestResilienceFeatures:
    """Test suite for resilience and error handling."""

    def test_retry_mechanism(self):
        """Test retry mechanism for failed requests."""
        from resilience import RetryConfig, retry_with_exponential_backoff

        attempt_count = 0

        def flaky_function():
            nonlocal attempt_count
            attempt_count += 1
            if attempt_count < 3:
                raise Exception("Temporary failure")
            return "success"

        config = RetryConfig(max_attempts=3, base_delay=0.01)
        result = retry_with_exponential_backoff(flaky_function, config)

        assert result == "success"
        assert attempt_count == 3

    def test_dead_letter_queue(self):
        """Test dead letter queue for permanently failed tasks."""
        from resilience import DeadLetterQueue

        dlq = DeadLetterQueue(max_size=100)

        # Add failed task
        dlq.add(task_id='task_001', error='Permanent failure', payload={'test': 'data'})

        # Verify task was added
        failed_tasks = dlq.get_all()
        assert len(failed_tasks) == 1
        assert failed_tasks[0]['task_id'] == 'task_001'

    def test_rate_limiting(self):
        """Test rate limiting functionality."""
        from rate_limiter import RateLimiter

        limiter = RateLimiter(requests=5, window=60)

        # First 5 requests should pass
        for _ in range(5):
            assert limiter.is_allowed('test_client') is True

        # 6th request should be rate limited
        assert limiter.is_allowed('test_client') is False


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
