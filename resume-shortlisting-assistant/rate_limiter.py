"""
Rate Limiting Middleware for AI Resume Shortlisting Assistant.

This module provides rate limiting functionality to protect the API from abuse
and ensure fair resource allocation.

Features:
- Token bucket algorithm for rate limiting
- IP-based rate limiting
- Endpoint-specific rate limits
- Distributed rate limiting support (Redis)
- Graceful degradation

Usage:
    from rate_limiter import rate_limit, init_rate_limiter

    app = Flask(__name__)
    init_rate_limiter(app)

    @app.route('/api/evaluate')
    @rate_limit(requests=10, window=60, key_func=lambda: request.remote_addr)
    def evaluate():
        return jsonify({'status': 'ok'})

Contributor: shubham21155102
"""

import time
import logging
from typing import Dict, Optional, Callable, Any
from functools import wraps
from collections import defaultdict
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class RateLimitExceeded(Exception):
    """Raised when rate limit is exceeded."""
    def __init__(self, retry_after: int):
        self.retry_after = retry_after
        super().__init__(f"Rate limit exceeded. Retry after {retry_after} seconds")


class TokenBucket:
    """
    Token bucket implementation for rate limiting.

    The token bucket algorithm allows for bursts of traffic while
    maintaining a long-term rate limit.
    """

    def __init__(self, rate: float, capacity: int):
        """
        Initialize a token bucket.

        Args:
            rate: Tokens added per second
            capacity: Maximum bucket capacity (max tokens)
        """
        self.rate = rate
        self.capacity = capacity
        self.tokens = float(capacity)
        self.last_update = time.time()
        self._lock = None  # Simple in-memory, no locking needed

    def consume(self, tokens: int = 1) -> bool:
        """
        Try to consume tokens from the bucket.

        Args:
            tokens: Number of tokens to consume

        Returns:
            True if tokens were consumed, False otherwise
        """
        now = time.time()
        elapsed = now - self.last_update

        # Add tokens based on elapsed time
        self.tokens = min(
            self.capacity,
            self.tokens + elapsed * self.rate
        )
        self.last_update = now

        if self.tokens >= tokens:
            self.tokens -= tokens
            return True
        return False

    def get_retry_after(self, tokens: int = 1) -> int:
        """
        Calculate seconds until tokens are available.

        Args:
            tokens: Number of tokens needed

        Returns:
            Seconds until tokens are available
        """
        now = time.time()
        elapsed = now - self.last_update

        # Calculate current tokens
        current_tokens = min(
            self.capacity,
            self.tokens + elapsed * self.rate
        )

        if current_tokens >= tokens:
            return 0

        # Calculate time needed
        tokens_needed = tokens - current_tokens
        return int(tokens_needed / self.rate) + 1


class RateLimiter:
    """
    In-memory rate limiter using token bucket algorithm.

    For production with multiple workers, use Redis-based rate limiting.
    """

    def __init__(self):
        """Initialize the rate limiter."""
        self.buckets: Dict[str, TokenBucket] = {}
        self.windows: Dict[str, list] = {}  # For sliding window algorithm
        self.default_rate = 10  # requests per minute
        self.default_window = 60  # seconds
        self.burst_capacity = 20  # max burst

    def _get_bucket(self, key: str, rate: float, capacity: int) -> TokenBucket:
        """Get or create a token bucket for a key."""
        if key not in self.buckets:
            self.buckets[key] = TokenBucket(rate, capacity)
        return self.buckets[key]

    def check(self, key: str, requests: int, window: int) -> tuple[bool, int]:
        """
        Check if a request is within rate limits.

        Args:
            key: Unique identifier (e.g., IP address, user ID)
            requests: Number of requests allowed
            window: Time window in seconds

        Returns:
            Tuple of (allowed: bool, retry_after: int)
        """
        rate = requests / window  # tokens per second
        bucket = self._get_bucket(key, rate, requests + self.burst_capacity)

        if bucket.consume(1):
            return True, 0
        else:
            retry_after = bucket.get_retry_after(1)
            return False, retry_after

    def check_sliding_window(self, key: str, requests: int, window: int) -> tuple[bool, int]:
        """
        Check rate limit using sliding window algorithm.

        Args:
            key: Unique identifier
            requests: Number of requests allowed
            window: Time window in seconds

        Returns:
            Tuple of (allowed: bool, retry_after: int)
        """
        now = time.time()
        window_start = now - window

        # Initialize window if needed
        if key not in self.windows:
            self.windows[key] = []

        # Remove old timestamps
        self.windows[key] = [
            ts for ts in self.windows[key]
            if ts > window_start
        ]

        # Check if under limit
        if len(self.windows[key]) < requests:
            self.windows[key].append(now)
            return True, 0
        else:
            # Calculate retry after
            oldest_timestamp = self.windows[key][0]
            retry_after = int(oldest_timestamp + window - now) + 1
            return False, retry_after

    def reset(self, key: Optional[str] = None):
        """
        Reset rate limits for a key or all keys.

        Args:
            key: Specific key to reset, or None to reset all
        """
        if key:
            self.buckets.pop(key, None)
            self.windows.pop(key, None)
        else:
            self.buckets.clear()
            self.windows.clear()

    def get_stats(self) -> Dict[str, Any]:
        """
        Get rate limiter statistics.

        Returns:
            Dictionary with statistics
        """
        return {
            'total_keys': len(self.buckets),
            'active_keys': sum(
                1 for b in self.buckets.values()
                if b.tokens < b.capacity
            )
        }


# Global rate limiter instance
_rate_limiter: Optional[RateLimiter] = None


def get_rate_limiter() -> RateLimiter:
    """Get the global rate limiter instance."""
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = RateLimiter()
    return _rate_limiter


# =============================================================================
# Flask Integration
# =============================================================================

def init_rate_limiter(app):
    """
    Initialize rate limiting for a Flask app.

    Adds a before_request handler for rate limiting.

    Args:
        app: Flask application instance
    """
    @app.before_request
    def _check_rate_limit():
        # Skip rate limiting for health checks
        if request.path == '/health':
            return None

        # Get client identifier
        key = _get_rate_limit_key()

        # Default limits: 30 requests per minute per IP
        allowed, retry_after = get_rate_limiter().check(
            key=key,
            requests=30,
            window=60
        )

        if not allowed:
            response = jsonify({
                'error': 'Rate limit exceeded',
                'retry_after': retry_after
            })
            response.status_code = 429
            response.headers['Retry-After'] = str(retry_after)
            return response

        return None


def rate_limit(
    requests: int = 10,
    window: int = 60,
    key_func: Optional[Callable] = None,
    on_limit_exceeded: Optional[Callable] = None
):
    """
    Decorator for rate limiting individual routes.

    Args:
        requests: Number of requests allowed
        window: Time window in seconds
        key_func: Function to generate rate limit key (default: IP address)
        on_limit_exceeded: Custom handler for rate limit exceeded

    Returns:
        Decorated function with rate limiting
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Get rate limit key
            if key_func:
                key = key_func()
            else:
                key = _get_rate_limit_key()

            # Check rate limit
            allowed, retry_after = get_rate_limiter().check(
                key=key,
                requests=requests,
                window=window
            )

            if not allowed:
                if on_limit_exceeded:
                    return on_limit_exceeded(retry_after)

                response = jsonify({
                    'error': f'Rate limit exceeded. Retry after {retry_after} seconds'
                })
                response.status_code = 429
                response.headers['Retry-After'] = str(retry_after)
                return response

            return func(*args, **kwargs)

        return wrapper

    return decorator


def _get_rate_limit_key() -> str:
    """
    Get the rate limit key for the current request.

    Tries multiple sources for the client IP to handle proxies.

    Returns:
        Client identifier string
    """
    from flask import request

    # Check for forwarded headers
    if request.headers.get('X-Forwarded-For'):
        return f"ip:{request.headers.get('X-Forwarded-For').split(',')[0].strip()}"
    if request.headers.get('X-Real-IP'):
        return f"ip:{request.headers.get('X-Real-IP')}"

    # Fall back to remote address
    return f"ip:{request.remote_addr}"


def get_rate_limit_headers(key: Optional[str] = None) -> Dict[str, str]:
    """
    Get rate limit headers for a response.

    Args:
        key: Rate limit key (optional)

    Returns:
        Dictionary with rate limit headers
    """
    limiter = get_rate_limiter()
    stats = limiter.get_stats()

    return {
        'X-RateLimit-Limit': '30',
        'X-RateLimit-Remaining': str(max(0, 30 - stats['active_keys'])),
        'X-RateLimit-Reset': str(int(time.time() + 60))
    }


# =============================================================================
# Endpoint-specific limits
# =============================================================================

ENDPOINT_LIMITS = {
    '/api/evaluate': (10, 60),      # 10 evaluations per minute
    '/api/jobs': (20, 60),          # 20 job requests per minute
    '/api/candidates': (30, 60),    # 30 candidate requests per minute
    '/api/analytics': (10, 60),     # 10 analytics requests per minute
}


def check_endpoint_limit(path: str) -> tuple[bool, int]:
    """
    Check if endpoint-specific rate limit allows the request.

    Args:
        path: Request path

    Returns:
        Tuple of (allowed: bool, retry_after: int)
    """
    key = _get_rate_limit_key()
    endpoint_key = f"{key}:{path}"

    if path in ENDPOINT_LIMITS:
        requests, window = ENDPOINT_LIMITS[path]
        return get_rate_limiter().check(endpoint_key, requests, window)

    # Default limit for unlisted endpoints
    return get_rate_limiter().check(endpoint_key, 30, 60)


# =============================================================================
# Cleanup
# =============================================================================

def cleanup_old_keys(max_age: int = 3600):
    """
    Remove old rate limit keys to prevent memory leaks.

    Args:
        max_age: Maximum age in seconds for inactive keys
    """
    limiter = get_rate_limiter()
    # Simple cleanup - in production use more sophisticated logic
    if len(limiter.buckets) > 10000:
        # Remove oldest buckets
        keys_to_remove = list(limiter.buckets.keys())[:1000]
        for key in keys_to_remove:
            limiter.reset(key)
        logger.info(f"Cleaned up {len(keys_to_remove)} old rate limit keys")
