"""
Structured JSON Logging Module for AI Resume Shortlisting Assistant.

This module provides structured logging with context tracking for better
debugging and monitoring in production environments.

Features:
- JSON-formatted log entries for easy parsing
- Request ID tracking for distributed tracing
- Context management for correlated logs
- Structured metadata attachment
- Performance metrics tracking

Contributor: shubham21155102 - Enterprise-grade logging infrastructure
"""

import json
import logging
import sys
import time
import uuid
from contextvars import ContextVar
from datetime import datetime
from typing import Any, Dict, Optional, Union
from functools import wraps
from pathlib import Path

# Context variables for request tracking
_request_id: ContextVar[Optional[str]] = ContextVar('request_id', default=None)
_user_id: ContextVar[Optional[str]] = ContextVar('user_id', default=None)
_operation: ContextVar[Optional[str]] = ContextVar('operation', default=None)
_additional_context: ContextVar[Dict[str, Any]] = ContextVar('additional_context', default={})


class LogContext:
    """
    Context manager for setting logging context.

    Usage:
        with LogContext(request_id="123", operation="evaluate_resume"):
            logger.info("Processing resume")
    """

    def __init__(self, **kwargs):
        self.context = kwargs
        self.tokens = []

    def __enter__(self):
        for key, value in self.context.items():
            if key == 'request_id':
                self.tokens.append(_request_id.set(value))
            elif key == 'user_id':
                self.tokens.append(_user_id.set(value))
            elif key == 'operation':
                self.tokens.append(_operation.set(value))
            else:
                current = _additional_context.get({}).copy()
                current[key] = value
                self.tokens.append(_additional_context.set(current))
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        for token in self.tokens:
            token.var.reset(token)


class JSONFormatter(logging.Formatter):
    """
    Custom JSON formatter for structured logging.

    Outputs log entries as JSON with consistent structure including:
    - timestamp: ISO format timestamp
    - level: Log level (INFO, WARNING, ERROR, etc.)
    - message: Log message
    - request_id: Request tracking ID (if available)
    - user_id: User ID (if available)
    - operation: Operation being performed (if available)
    - context: Additional context (if available)
    - exception: Exception info (if applicable)
    """

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_entry = {
            'timestamp': datetime.fromtimestamp(record.created).isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
        }

        # Add context variables if available
        request_id = _request_id.get()
        if request_id:
            log_entry['request_id'] = request_id

        user_id = _user_id.get()
        if user_id:
            log_entry['user_id'] = user_id

        operation = _operation.get()
        if operation:
            log_entry['operation'] = operation

        # Add additional context
        extra_context = _additional_context.get({})
        if extra_context:
            log_entry['context'] = extra_context

        # Add any extra fields from the record
        if hasattr(record, 'extra'):
            log_entry.update(record.extra)

        # Add exception info if present
        if record.exc_info:
            log_entry['exception'] = {
                'type': record.exc_info[0].__name__ if record.exc_info[0] else None,
                'message': str(record.exc_info[1]) if record.exc_info[1] else None,
            }

        return json.dumps(log_entry, default=str)


class StructuredLogger:
    """
    Structured logger with context awareness.

    Provides methods for logging at different levels with automatic
    context inclusion.
    """

    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
        self._logger = self.logger

    def _log_with_context(
        self,
        level: int,
        msg: str,
        extra: Optional[Dict[str, Any]] = None,
        **kwargs
    ):
        """Log message with context."""
        if extra:
            # Merge with existing context
            combined_context = _additional_context.get({}).copy()
            combined_context.update(extra)
            kwargs['extra'] = {'extra': combined_context}
        self._logger.log(level, msg, **kwargs)

    def debug(self, msg: str, extra: Optional[Dict[str, Any]] = None, **kwargs):
        """Log debug message."""
        self._log_with_context(logging.DEBUG, msg, extra, **kwargs)

    def info(self, msg: str, extra: Optional[Dict[str, Any]] = None, **kwargs):
        """Log info message."""
        self._log_with_context(logging.INFO, msg, extra, **kwargs)

    def warning(self, msg: str, extra: Optional[Dict[str, Any]] = None, **kwargs):
        """Log warning message."""
        self._log_with_context(logging.WARNING, msg, extra, **kwargs)

    def error(self, msg: str, extra: Optional[Dict[str, Any]] = None, exc_info: bool = False, **kwargs):
        """Log error message."""
        self._log_with_context(logging.ERROR, msg, extra, exc_info=exc_info, **kwargs)

    def critical(self, msg: str, extra: Optional[Dict[str, Any]] = None, exc_info: bool = False, **kwargs):
        """Log critical message."""
        self._log_with_context(logging.CRITICAL, msg, extra, exc_info=exc_info, **kwargs)


def get_logger(name: str) -> StructuredLogger:
    """
    Get a structured logger instance.

    Args:
        name: Logger name (usually __name__ of the module)

    Returns:
        StructuredLogger instance
    """
    return StructuredLogger(name)


def setup_logging(
    level: Union[str, int] = logging.INFO,
    log_file: Optional[Path] = None,
    enable_console: bool = True
) -> None:
    """
    Set up structured logging for the application.

    Args:
        level: Logging level (default: INFO)
        log_file: Optional file path for log output
        enable_console: Whether to output to console (default: True)
    """
    # Convert string level to int if needed
    if isinstance(level, str):
        level = getattr(logging, level.upper(), logging.INFO)

    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Remove existing handlers
    root_logger.handlers.clear()

    # Create JSON formatter
    formatter = JSONFormatter()

    # Add console handler if requested
    if enable_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)

    # Add file handler if specified
    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)


def log_execution_time(logger: Optional[StructuredLogger] = None):
    """
    Decorator to log function execution time.

    Usage:
        @log_execution_time()
        def my_function():
            pass

    Args:
        logger: Logger instance to use (creates new if None)
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            func_name = f"{func.__module__}.{func.__name__}"

            try:
                result = func(*args, **kwargs)
                execution_time = time.time() - start_time

                log = logger or get_logger(func.__module__)
                log.info(
                    f"{func.__name__} completed",
                    extra={
                        'function': func_name,
                        'execution_time_ms': round(execution_time * 1000, 2)
                    }
                )
                return result

            except Exception as e:
                execution_time = time.time() - start_time
                log = logger or get_logger(func.__module__)
                log.error(
                    f"{func.__name__} failed",
                    extra={
                        'function': func_name,
                        'execution_time_ms': round(execution_time * 1000, 2),
                        'error': str(e)
                    },
                    exc_info=True
                )
                raise

        return wrapper
    return decorator


def generate_request_id() -> str:
    """Generate a unique request ID."""
    return str(uuid.uuid4())


def get_request_id() -> Optional[str]:
    """Get the current request ID from context."""
    return _request_id.get()


def set_request_id(request_id: str) -> None:
    """Set the request ID in context."""
    _request_id.set(request_id)


# =============================================================================
# Middleware Integration
# =============================================================================

class LoggingMiddleware:
    """
    Flask middleware for automatic request logging.

    Adds request ID generation and logging to all requests.
    """

    def __init__(self, app):
        self.app = app
        self.init_app(app)

    def init_app(self, app):
        """Initialize middleware with Flask app."""
        app.before_request(self._before_request)
        app.after_request(self._after_request)
        app.teardown_appcontext(self._teardown)

    def _before_request(self):
        """Generate request ID before processing."""
        import flask
        request_id = flask.request.headers.get('X-Request-ID', generate_request_id())
        set_request_id(request_id)
        flask.g.request_id = request_id
        flask.g.start_time = time.time()

    def _after_request(self, response):
        """Log request completion."""
        import flask
        logger = get_logger('api')

        execution_time = time.time() - getattr(flask.g, 'start_time', time.time())

        logger.info(
            "Request completed",
            extra={
                'method': flask.request.method,
                'path': flask.request.path,
                'status_code': response.status_code,
                'execution_time_ms': round(execution_time * 1000, 2),
                'user_agent': flask.request.headers.get('User-Agent'),
            }
        )

        # Add request ID to response headers
        response.headers['X-Request-ID'] = get_request_id() or 'unknown'
        return response

    def _teardown(self, exception):
        """Clean up context."""
        _request_id.set(None)
        _user_id.set(None)
        _operation.set(None)
        _additional_context.set({})


# =============================================================================
# Export Public API
# =============================================================================

__all__ = [
    'get_logger',
    'setup_logging',
    'LogContext',
    'StructuredLogger',
    'log_execution_time',
    'generate_request_id',
    'get_request_id',
    'set_request_id',
    'LoggingMiddleware',
]
