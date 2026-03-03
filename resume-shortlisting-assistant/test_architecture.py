"""
Unit Tests for Phase 4 Architecture Improvements.

This module provides comprehensive unit tests for:
1. Task Queue System
2. Service Layer
3. Rate Limiter

These tests follow TDD principles and can be run with pytest.

Run tests:
    pytest test_architecture.py -v
    pytest test_architecture.py -v --cov=.

Contributor: shubham21155102
"""

import pytest
import time
import threading
from io import BytesIO
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta

# Import modules to test
from task_queue import TaskQueue, Task, TaskStatus, get_task_queue, get_task_status
from rate_limiter import RateLimiter, TokenBucket, rate_limit, RateLimitExceeded
from services import (
    CandidateService,
    JobPostService,
    AnalyticsService,
    ValidationError,
    ResourceNotFoundError
)


# =============================================================================
# Task Queue Tests
# =============================================================================

class TestTaskQueue:
    """Test suite for TaskQueue functionality."""

    @pytest.fixture
    def queue(self):
        """Create a fresh task queue for each test."""
        q = TaskQueue(max_workers=2)
        q.start()
        yield q
        q.stop()

    @pytest.fixture
    def simple_task(self):
        """Create a simple task function."""
        def task_func(x, y):
            return x + y
        return task_func

    def test_task_submit(self, queue, simple_task):
        """Test submitting a task to the queue."""
        task_id = queue.submit(simple_task, 5, 3)
        assert task_id is not None
        assert isinstance(task_id, str)

    def test_task_execution(self, queue, simple_task):
        """Test that a task executes correctly."""
        task_id = queue.submit(simple_task, 5, 3)

        # Wait for task to complete
        time.sleep(0.5)

        task = queue.get_task(task_id)
        assert task is not None
        assert task.status == TaskStatus.COMPLETED
        assert task.result == 8

    def test_task_with_failure(self, queue):
        """Test handling of task that raises an exception."""
        def failing_task():
            raise ValueError("Test error")

        task_id = queue.submit(failing_task)

        # Wait for task to fail
        time.sleep(0.5)

        task = queue.get_task(task_id)
        assert task.status == TaskStatus.FAILED
        assert "Test error" in task.error

    def test_task_cancellation(self, queue, simple_task):
        """Test cancelling a pending task."""
        # Submit many tasks to ensure some stay pending
        task_ids = [queue.submit(simple_task, i, i) for i in range(10)]

        # Try to cancel one immediately
        cancelled = queue.cancel_task(task_ids[0])
        assert cancelled is True

        task = queue.get_task(task_ids[0])
        assert task.status == TaskStatus.CANCELLED

    def test_task_statistics(self, queue, simple_task):
        """Test getting queue statistics."""
        # Submit some tasks
        for i in range(5):
            queue.submit(simple_task, i, i)

        stats = queue.get_statistics()
        assert stats['total_tasks'] == 5
        assert stats['workers'] == 2
        assert stats['running'] is True

    def test_task_to_dict(self, queue, simple_task):
        """Test Task.to_dict serialization."""
        task_id = queue.submit(simple_task, 5, 3)
        task = queue.get_task(task_id)

        task_dict = task.to_dict()
        assert 'task_id' in task_dict
        assert 'status' in task_dict
        assert 'created_at' in task_dict
        assert task_dict['task_id'] == task_id


class TestTokenBucket:
    """Test suite for TokenBucket algorithm."""

    @pytest.fixture
    def bucket(self):
        """Create a token bucket with rate=10/sec, capacity=20."""
        return TokenBucket(rate=10.0, capacity=20)

    def test_initial_tokens(self, bucket):
        """Test bucket starts with full capacity."""
        assert bucket.tokens == 20

    def test_consume_tokens(self, bucket):
        """Test consuming tokens."""
        assert bucket.consume(5) is True
        assert bucket.tokens == 15

    def test_consume_all_tokens(self, bucket):
        """Test consuming all available tokens."""
        assert bucket.consume(20) is True
        assert bucket.consume(1) is False

    def test_token_replenishment(self, bucket):
        """Test tokens are replenished over time."""
        # Consume all tokens
        bucket.consume(20)
        assert bucket.consume(1) is False

        # Wait for token replenishment (0.1s = 1 token at rate 10/s)
        time.sleep(0.15)
        assert bucket.consume(1) is True

    def test_burst_handling(self, bucket):
        """Test handling of burst traffic."""
        # Initial burst should use full capacity
        assert bucket.consume(15) is True

        # Wait a bit for some replenishment
        time.sleep(0.1)

        # Should have some tokens available
        assert bucket.consume(1) is True

    def test_get_retry_after(self, bucket):
        """Test calculating retry after time."""
        bucket.consume(20)
        retry_after = bucket.get_retry_after(1)
        assert retry_after > 0
        assert retry_after <= 1  # Should be about 0.1s at rate 10/s


class TestRateLimiter:
    """Test suite for RateLimiter functionality."""

    @pytest.fixture
    def limiter(self):
        """Create a fresh rate limiter."""
        return RateLimiter()

    def test_check_within_limit(self, limiter):
        """Test check returns True when within limit."""
        allowed, _ = limiter.check("test_key", requests=10, window=60)
        assert allowed is True

    def test_check_exceeds_limit(self, limiter):
        """Test check returns False when limit exceeded."""
        # Consume all tokens
        for _ in range(20):
            limiter.check("test_key", requests=10, window=60)

        allowed, retry_after = limiter.check("test_key", requests=10, window=60)
        assert allowed is False
        assert retry_after > 0

    def test_sliding_window_limit(self, limiter):
        """Test sliding window rate limiting."""
        # Fill the window
        for _ in range(10):
            limiter.check_sliding_window("sw_key", requests=10, window=1)

        allowed, _ = limiter.check_sliding_window("sw_key", requests=10, window=1)
        assert allowed is False

    def test_sliding_window_replenishment(self, limiter):
        """Test sliding window allows requests after time passes."""
        # Fill the window
        for _ in range(10):
            limiter.check_sliding_window("sw_key2", requests=10, window=1)

        # Wait for window to expire
        time.sleep(1.1)

        allowed, _ = limiter.check_sliding_window("sw_key2", requests=10, window=1)
        assert allowed is True

    def test_reset(self, limiter):
        """Test resetting rate limits."""
        # Use some tokens
        for _ in range(5):
            limiter.check("reset_key", requests=10, window=60)

        # Reset
        limiter.reset("reset_key")

        # Should be fresh now
        allowed, _ = limiter.check("reset_key", requests=10, window=60)
        assert allowed is True

    def test_get_stats(self, limiter):
        """Test getting limiter statistics."""
        limiter.check("stats_key", requests=10, window=60)
        stats = limiter.get_stats()
        assert 'total_keys' in stats
        assert stats['total_keys'] >= 1


# =============================================================================
# Service Layer Tests
# =============================================================================

class TestCandidateService:
    """Test suite for CandidateService."""

    @pytest.fixture
    def mock_db(self):
        """Mock database module."""
        with patch('services.db') as mock:
            yield mock

    @pytest.fixture
    def mock_engine(self):
        """Mock engine module."""
        with patch('services.evaluate_resume') as mock:
            mock.return_value = MagicMock(
                tier='Tier A',
                summary='Test summary',
                exact_match=MagicMock(score=85, explanation='Good match'),
                similarity_match=MagicMock(score=80, explanation='Similar'),
                achievement_impact=MagicMock(score=75, explanation='Impactful'),
                ownership=MagicMock(score=70, explanation='Owner')
            )
            yield mock

    def test_evaluate_resume_sync_validation_error(self, mock_engine):
        """Test sync evaluation validates inputs."""
        with pytest.raises(ValidationError):
            CandidateService.evaluate_resume_sync(
                BytesIO(b"test"),
                "",  # Empty job description
                "test.pdf"
            )

    def test_evaluate_resume_sync_invalid_file(self, mock_engine):
        """Test sync evaluation rejects non-PDF files."""
        with pytest.raises(ValidationError):
            CandidateService.evaluate_resume_sync(
                BytesIO(b"test"),
                "Test job description",
                "test.txt"  # Not a PDF
            )

    def test_get_candidate_not_found(self):
        """Test get_candidate raises error when not found."""
        with patch('services.db.get_candidate_by_id', return_value=None):
            with pytest.raises(ResourceNotFoundError):
                CandidateService.get_candidate(999)

    def test_delete_candidate_not_found(self):
        """Test delete_candidate handles not found."""
        with patch('services.db.get_candidate_by_id', return_value=None):
            with pytest.raises(ResourceNotFoundError):
                CandidateService.delete_candidate(999)


class TestJobPostService:
    """Test suite for JobPostService."""

    def test_create_job_post_validation_error(self):
        """Test create validates inputs."""
        with pytest.raises(ValidationError):
            JobPostService.create_job_post("", "Description")

    def test_create_job_post_empty_description(self):
        """Test create validates description."""
        with pytest.raises(ValidationError):
            JobPostService.create_job_post("Title", "")

    def test_generate_ai_job_post_validation(self):
        """Test AI generation validates title."""
        with pytest.raises(ValidationError):
            JobPostService.generate_ai_job_post("")

    def test_get_job_post_not_found(self):
        """Test get handles not found."""
        with patch('services.db.get_job_post_by_id', return_value=None):
            with pytest.raises(ResourceNotFoundError):
                JobPostService.get_job_post(999)


class TestAnalyticsService:
    """Test suite for AnalyticsService."""

    def test_skill_gap_validation_empty_list(self):
        """Test skill gap validates input list."""
        with pytest.raises(ValidationError):
            AnalyticsService.analyze_skill_gap([])

    def test_skill_gap_validation_not_list(self):
        """Test skill gap validates input type."""
        with pytest.raises(ValidationError):
            AnalyticsService.analyze_skill_gap("python")


# =============================================================================
# Integration Tests
# =============================================================================

class TestTaskQueueIntegration:
    """Integration tests for task queue with real operations."""

    def test_concurrent_task_execution(self):
        """Test multiple tasks execute concurrently."""
        queue = TaskQueue(max_workers=4)
        queue.start()

        def slow_task(value):
            time.sleep(0.2)
            return value * 2

        # Submit multiple tasks
        start = time.time()
        task_ids = [queue.submit(slow_task, i) for i in range(8)]

        # Wait for all to complete
        for task_id in task_ids:
            task = queue.get_task(task_id)
            timeout = 5
            while task.status == TaskStatus.PENDING and timeout > 0:
                time.sleep(0.1)
                timeout -= 0.1
                task = queue.get_task(task_id)

        elapsed = time.time() - start
        queue.stop()

        # Should complete in ~0.4s (2 batches of 4 workers), not 1.6s (sequential)
        assert elapsed < 1.0

    def test_task_retry_mechanism(self):
        """Test that failing tasks retry up to max_retries."""
        queue = TaskQueue(max_workers=1)

        retry_count = {'value': 0}

        def flaky_task():
            retry_count['value'] += 1
            if retry_count['value'] < 3:
                raise ValueError("Not yet!")
            return "success"

        queue.start()
        task_id = queue.submit(flaky_task)

        # Wait for completion
        time.sleep(2)

        task = queue.get_task(task_id)
        queue.stop()

        assert task.status == TaskStatus.COMPLETED
        assert task.result == "success"
        assert task.retry_count == 2


# =============================================================================
# Performance Tests
# =============================================================================

class TestPerformance:
    """Performance tests for critical components."""

    def test_token_bucket_performance(self):
        """Test token bucket can handle high request rates."""
        bucket = TokenBucket(rate=1000, capacity=10000)

        start = time.time()
        for _ in range(10000):
            bucket.consume(1)
        elapsed = time.time() - start

        # Should process 10k consumes quickly
        assert elapsed < 0.1

    def test_rate_limiter_throughput(self):
        """Test rate limiter can handle many keys."""
        limiter = RateLimiter()

        start = time.time()
        for i in range(1000):
            limiter.check(f"key_{i % 100}", requests=10, window=60)
        elapsed = time.time() - start

        # Should handle 1000 checks quickly
        assert elapsed < 0.5


# =============================================================================
# Test Fixtures and Utilities
# =============================================================================

@pytest.fixture
def sample_pdf_content():
    """Return sample PDF text content for testing."""
    return """
    JOHN DOE
    john.doe@email.com | (555) 123-4567 | San Francisco, CA

    SUMMARY
    Senior Software Engineer with 8 years of experience building scalable web applications.

    SKILLS
    - Python, JavaScript, TypeScript, React, Node.js
    - PostgreSQL, MongoDB, Redis
    - AWS, Docker, Kubernetes
    - CI/CD, Git, Agile

    EXPERIENCE
    Senior Software Engineer | Tech Corp | 2020 - Present
    - Led development of microservices architecture serving 1M+ users
    - Improved application performance by 40% through optimization
    - Mentored team of 5 junior developers

    Software Engineer | Startup Inc | 2017 - 2020
    - Built RESTful APIs using Flask and Node.js
    - Implemented real-time features using WebSockets
    - Reduced page load time by 60%

    EDUCATION
    B.S. Computer Science | Stanford University | 2017
    """


@pytest.fixture
def sample_job_description():
    """Return sample job description for testing."""
    return """
    Senior Software Engineer

    We are looking for a Senior Software Engineer to join our team.

    Requirements:
    - 5+ years of experience in software development
    - Proficiency in Python, JavaScript, or similar languages
    - Experience with React or similar frontend frameworks
    - Knowledge of databases (PostgreSQL, MongoDB)
    - Experience with cloud platforms (AWS, GCP)
    - Strong problem-solving and communication skills

    Responsibilities:
    - Design and implement scalable software solutions
    - Collaborate with cross-functional teams
    - Mentor junior developers
    - Participate in code reviews and architectural discussions
    """


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
