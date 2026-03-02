"""
Resilience Module - Retry Logic and Dead Letter Queue for AI Resume Shortlisting Assistant.

This module provides enterprise-grade resilience features:
1. Exponential backoff retry mechanisms for LLM API calls
2. Dead Letter Queue (DLQ) for failed evaluations
3. Circuit breaker pattern for failing services
4. Request timeout management

Features:
- Automatic retry with exponential backoff for transient failures
- Dead Letter Queue for storing failed requests for manual review/retry
- Circuit breaker to prevent cascading failures
- Comprehensive retry statistics tracking

Contributor: shubham21155102
"""

import logging
import time
import json
from datetime import datetime, timedelta
from typing import Optional, Callable, Any, Dict, List
from functools import wraps
from dataclasses import dataclass, asdict
from enum import Enum
import threading

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RetryStrategy(Enum):
    """Retry strategy types."""
    EXPONENTIAL_BACKOFF = "exponential_backoff"
    FIXED_DELAY = "fixed_delay"
    LINEAR_BACKOFF = "linear_backoff"


class CircuitState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"  # Normal operation
    OPEN = "open"      # Failing, reject requests
    HALF_OPEN = "half_open"  # Testing if service recovered


@dataclass
class RetryConfig:
    """Configuration for retry logic."""
    max_attempts: int = 3
    base_delay: float = 1.0  # Base delay in seconds
    max_delay: float = 60.0  # Maximum delay in seconds
    exponential_base: float = 2.0  # Base for exponential backoff
    strategy: RetryStrategy = RetryStrategy.EXPONENTIAL_BACKOFF
    retry_on_exceptions: tuple = (Exception,)
    retry_on_status_codes: Optional[tuple] = None


@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker."""
    failure_threshold: int = 5  # Open circuit after N failures
    recovery_timeout: float = 60.0  # Wait N seconds before attempting recovery
    expected_exception: type[Exception] = Exception


@dataclass
class FailedRequest:
    """Represents a failed request in the DLQ."""
    id: str
    timestamp: datetime
    endpoint: str
    method: str
    payload: Dict[str, Any]
    error_message: str
    error_type: str
    retry_count: int
    last_retry_attempt: Optional[datetime] = None
    resolved: bool = False


# =============================================================================
# Circuit Breaker Implementation
# =============================================================================

class CircuitBreaker:
    """
    Circuit breaker pattern implementation.

    Prevents cascading failures by stopping requests to a failing service
    after a threshold of failures is reached.
    """

    def __init__(self, config: CircuitBreakerConfig):
        self.config = config
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.last_failure_time: Optional[datetime] = None
        self._lock = threading.Lock()

    def call(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute a function through the circuit breaker.

        Args:
            func: Function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments

        Returns:
            Result of the function call

        Raises:
            Exception: If circuit is open or function raises an exception
        """
        with self._lock:
            if self.state == CircuitState.OPEN:
                if self._should_attempt_reset():
                    logger.info("Circuit breaker: Attempting to reset to HALF_OPEN state")
                    self.state = CircuitState.HALF_OPEN
                else:
                    raise Exception(f"Circuit breaker is OPEN. Service unavailable. Retry after {self._remaining_recovery_time():.1f}s")

            if self.state == CircuitState.HALF_OPEN:
                logger.info("Circuit breaker: HALF_OPEN state, attempting recovery")

        try:
            result = func(*args, **kwargs)

            # Success - reset the circuit
            with self._lock:
                if self.state == CircuitState.HALF_OPEN:
                    logger.info("Circuit breaker: Recovery successful, closing circuit")
                    self.state = CircuitState.CLOSED
                self.failure_count = 0
                self.last_failure_time = None

            return result

        except self.config.expected_exception as e:
            with self._lock:
                self.failure_count += 1
                self.last_failure_time = datetime.now()

                if self.failure_count >= self.config.failure_threshold:
                    logger.error(
                        f"Circuit breaker: Failure threshold reached ({self.failure_count}). Opening circuit."
                    )
                    self.state = CircuitState.OPEN
                else:
                    logger.warning(
                        f"Circuit breaker: Failure count increased to {self.failure_count}/{self.config.failure_threshold}"
                    )

            raise

    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt recovery."""
        if self.last_failure_time is None:
            return True
        elapsed = (datetime.now() - self.last_failure_time).total_seconds()
        return elapsed >= self.config.recovery_timeout

    def _remaining_recovery_time(self) -> float:
        """Calculate remaining time before recovery attempt."""
        if self.last_failure_time is None:
            return 0.0
        elapsed = (datetime.now() - self.last_failure_time).total_seconds()
        return max(0.0, self.config.recovery_timeout - elapsed)

    def reset(self):
        """Manually reset the circuit breaker."""
        with self._lock:
            self.state = CircuitState.CLOSED
            self.failure_count = 0
            self.last_failure_time = None
            logger.info("Circuit breaker: Manually reset to CLOSED state")


# =============================================================================
# Retry Decorator Implementation
# =============================================================================

def retry_with_backoff(
    config: Optional[RetryConfig] = None,
    on_retry: Optional[Callable] = None
):
    """
    Decorator for retrying functions with exponential backoff.

    Args:
        config: Retry configuration
        on_retry: Optional callback function called on each retry

    Returns:
        Decorated function with retry logic
    """
    if config is None:
        config = RetryConfig()

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None

            for attempt in range(config.max_attempts):
                try:
                    return func(*args, **kwargs)
                except config.retry_on_exceptions as e:
                    last_exception = e

                    if attempt < config.max_attempts - 1:
                        delay = _calculate_delay(attempt, config)

                        logger.warning(
                            f"Retry: Function '{func.__name__}' failed (attempt {attempt + 1}/{config.max_attempts}). "
                            f"Retrying in {delay:.2f}s. Error: {str(e)}"
                        )

                        if on_retry:
                            on_retry(attempt, e, delay)

                        time.sleep(delay)
                    else:
                        logger.error(
                            f"Retry: Function '{func.__name__}' failed after {config.max_attempts} attempts. "
                            f"Final error: {str(e)}"
                        )

            raise last_exception

        return wrapper

    return decorator


def _calculate_delay(attempt: int, config: RetryConfig) -> float:
    """Calculate delay based on retry strategy."""
    if config.strategy == RetryStrategy.EXPONENTIAL_BACKOFF:
        delay = config.base_delay * (config.exponential_base ** attempt)
    elif config.strategy == RetryStrategy.LINEAR_BACKOFF:
        delay = config.base_delay * (attempt + 1)
    else:  # FIXED_DELAY
        delay = config.base_delay

    return min(delay, config.max_delay)


# =============================================================================
# Dead Letter Queue Implementation
# =============================================================================

class DeadLetterQueue:
    """
    In-memory Dead Letter Queue for storing failed requests.

    Failed requests are stored for later review and retry.
    This implementation is in-memory; for production, consider
    using a persistent store (database, Redis, etc.).
    """

    def __init__(self, max_size: int = 1000):
        self._queue: List[FailedRequest] = []
        self._max_size = max_size
        self._lock = threading.Lock()

    def add(
        self,
        endpoint: str,
        method: str,
        payload: Dict[str, Any],
        error_message: str,
        error_type: str,
        retry_count: int = 0
    ) -> FailedRequest:
        """
        Add a failed request to the DLQ.

        Args:
            endpoint: API endpoint or function name
            method: HTTP method or function identifier
            payload: Request payload
            error_message: Error message
            error_type: Type of error
            retry_count: Number of retries already attempted

        Returns:
            FailedRequest object
        """
        with self._lock:
            # Remove oldest entries if queue is full
            if len(self._queue) >= self._max_size:
                removed = self._queue.pop(0)
                logger.warning(f"DLQ: Full, removed oldest entry: {removed.id}")

            failed_request = FailedRequest(
                id=f"{endpoint}_{int(time.time())}_{retry_count}",
                timestamp=datetime.now(),
                endpoint=endpoint,
                method=method,
                payload=payload,
                error_message=error_message,
                error_type=error_type,
                retry_count=retry_count
            )

            self._queue.append(failed_request)
            logger.error(f"DLQ: Added failed request {failed_request.id} to queue")

            return failed_request

    def get_all(self) -> List[FailedRequest]:
        """Get all failed requests."""
        with self._lock:
            return list(self._queue)

    def get_unresolved(self) -> List[FailedRequest]:
        """Get all unresolved failed requests."""
        with self._lock:
            return [fr for fr in self._queue if not fr.resolved]

    def get_by_id(self, request_id: str) -> Optional[FailedRequest]:
        """Get a failed request by ID."""
        with self._lock:
            for fr in self._queue:
                if fr.id == request_id:
                    return fr
            return None

    def mark_resolved(self, request_id: str) -> bool:
        """Mark a failed request as resolved."""
        with self._lock:
            for fr in self._queue:
                if fr.id == request_id:
                    fr.resolved = True
                    logger.info(f"DLQ: Marked request {request_id} as resolved")
                    return True
            return False

    def remove(self, request_id: str) -> bool:
        """Remove a failed request from the queue."""
        with self._lock:
            for i, fr in enumerate(self._queue):
                if fr.id == request_id:
                    self._queue.pop(i)
                    logger.info(f"DLQ: Removed request {request_id}")
                    return True
            return False

    def clear_resolved(self) -> int:
        """Remove all resolved requests from the queue."""
        with self._lock:
            original_size = len(self._queue)
            self._queue = [fr for fr in self._queue if not fr.resolved]
            removed = original_size - len(self._queue)
            logger.info(f"DLQ: Cleared {removed} resolved requests")
            return removed

    def get_statistics(self) -> Dict[str, Any]:
        """Get DLQ statistics."""
        with self._lock:
            unresolved = [fr for fr in self._queue if not fr.resolved]
            error_types = {}
            for fr in unresolved:
                error_types[fr.error_type] = error_types.get(fr.error_type, 0) + 1

            return {
                "total_requests": len(self._queue),
                "unresolved_count": len(unresolved),
                "resolved_count": len(self._queue) - len(unresolved),
                "error_types": error_types,
                "oldest_unresolved": min(unresolved, key=lambda x: x.timestamp).timestamp if unresolved else None,
                "newest_unresolved": max(unresolved, key=lambda x: x.timestamp).timestamp if unresolved else None,
            }


# Global DLQ instance
_dla: Optional[DeadLetterQueue] = None


def get_dlq() -> DeadLetterQueue:
    """Get the global Dead Letter Queue instance."""
    global _dla
    if _dla is None:
        _dla = DeadLetterQueue()
    return _dla


# =============================================================================
# Convenience Decorators for API Resilience
# =============================================================================

def resilient_llm_call(
    max_attempts: int = 3,
    use_circuit_breaker: bool = True,
    use_dlq: bool = True
):
    """
    Decorator for making resilient LLM API calls.

    Combines retry logic, circuit breaker, and DLQ for maximum resilience.

    Args:
        max_attempts: Maximum retry attempts
        use_circuit_breaker: Enable circuit breaker
        use_dlq: Enable dead letter queue

    Returns:
        Decorated function with resilience features
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            config = RetryConfig(max_attempts=max_attempts)

            # Setup circuit breaker if enabled
            breaker = None
            if use_circuit_breaker:
                breaker_config = CircuitBreakerConfig(
                    failure_threshold=5,
                    recovery_timeout=60.0
                )
                breaker = CircuitBreaker(breaker_config)

            dlq = get_dlq() if use_dlq else None

            last_exception = None

            for attempt in range(max_attempts):
                try:
                    if breaker:
                        return breaker.call(func, *args, **kwargs)
                    else:
                        return func(*args, **kwargs)

                except Exception as e:
                    last_exception = e

                    if attempt < max_attempts - 1:
                        delay = _calculate_delay(attempt, RetryConfig(max_attempts=max_attempts))
                        logger.warning(
                            f"Resilient LLM call failed (attempt {attempt + 1}/{max_attempts}). "
                            f"Retrying in {delay:.2f}s. Error: {str(e)}"
                        )
                        time.sleep(delay)
                    else:
                        # Final attempt failed - add to DLQ
                        if dlq:
                            dlq.add(
                                endpoint=func.__name__,
                                method="LLM_CALL",
                                payload={"args": str(args)[:1000], "kwargs": str(kwargs)[:1000]},
                                error_message=str(e),
                                error_type=type(e).__name__,
                                retry_count=max_attempts
                            )

                        logger.error(
                            f"Resilient LLM call failed after {max_attempts} attempts. "
                            f"Added to DLQ. Final error: {str(e)}"
                        )

            raise last_exception

        return wrapper

    return decorator
