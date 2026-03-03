"""
Global exception handling middleware for AI Resume Shortlisting Assistant.

This module provides standardized error responses with proper error codes,
improving API reliability and client integration.

Features:
- Standardized error response format
- Error codes for programmatic handling
- Request ID tracking for debugging
- HTTP status code mapping

Contributor: shubham21155102
"""

import logging
from typing import Any, Dict, Optional
from flask import Flask, jsonify, request
import uuid
import traceback

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class APIError(Exception):
    """Base exception for API errors."""

    def __init__(
        self,
        message: str,
        status_code: int = 500,
        error_code: str = "INTERNAL_ERROR",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        self.details = details or {}


class ValidationError(APIError):
    """Validation error (400)."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, 400, "VALIDATION_ERROR", details)


class NotFoundError(APIError):
    """Resource not found error (404)."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, 404, "NOT_FOUND", details)


class ConfigurationError(APIError):
    """Configuration error (500)."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, 500, "CONFIGURATION_ERROR", details)


class FileProcessingError(APIError):
    """File processing error (400)."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, 400, "FILE_PROCESSING_ERROR", details)


class DatabaseError(APIError):
    """Database operation error (500)."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, 500, "DATABASE_ERROR", details)


class BusinessLogicError(APIError):
    """Business logic error (422)."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, 422, "BUSINESS_LOGIC_ERROR", details)


def get_request_id() -> str:
    """Get or generate request ID."""
    if request and request.headers:
        return request.headers.get('X-Request-ID', str(uuid.uuid4()))
    return str(uuid.uuid4())


def format_error_response(
    error: APIError,
    request_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Format error response in standard structure.

    Args:
        error: The APIError instance
        request_id: Optional request ID for tracking

    Returns:
        Dictionary with standardized error format
    """
    response = {
        "error": {
            "code": error.error_code,
            "message": error.message
        }
    }

    if request_id:
        response["request_id"] = request_id

    if error.details:
        response["error"]["details"] = error.details

    return response


def register_error_handlers(app: Flask) -> None:
    """
    Register global error handlers with Flask app.

    Args:
        app: Flask application instance
    """

    @app.errorhandler(APIError)
    def handle_api_error(error: APIError):
        """Handle custom API errors."""
        request_id = get_request_id()
        response_data = format_error_response(error, request_id)

        logger.warning(
            f"API Error [{error.error_code}]: {error.message} | "
            f"Request ID: {request_id} | Path: {request.path if request else 'N/A'}"
        )

        return jsonify(response_data), error.status_code

    @app.errorhandler(ValidationError)
    def handle_validation_error(error: ValidationError):
        """Handle validation errors."""
        request_id = get_request_id()
        response_data = format_error_response(error, request_id)

        logger.info(
            f"Validation Error: {error.message} | "
            f"Request ID: {request_id} | Path: {request.path if request else 'N/A'}"
        )

        return jsonify(response_data), error.status_code

    @app.errorhandler(404)
    def handle_not_found(error):
        """Handle 404 errors."""
        request_id = get_request_id()
        response_data = {
            "error": {
                "code": "NOT_FOUND",
                "message": "The requested resource was not found"
            },
            "request_id": request_id
        }

        logger.info(f"404 Error | Request ID: {request_id} | Path: {request.path if request else 'N/A'}")

        return jsonify(response_data), 404

    @app.errorhandler(405)
    def handle_method_not_allowed(error):
        """Handle 405 errors."""
        request_id = get_request_id()
        response_data = {
            "error": {
                "code": "METHOD_NOT_ALLOWED",
                "message": "The method is not allowed for the requested URL"
            },
            "request_id": request_id
        }

        logger.info(f"405 Error | Request ID: {request_id} | Path: {request.path if request else 'N/A'}")

        return jsonify(response_data), 405

    @app.errorhandler(Exception)
    def handle_unexpected_error(error: Exception):
        """Handle unexpected errors."""
        request_id = get_request_id()

        # Log full traceback for debugging
        logger.error(
            f"Unexpected Error: {str(error)} | "
            f"Request ID: {request_id} | Path: {request.path if request else 'N/A'}",
            exc_info=True
        )

        response_data = {
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "An unexpected error occurred. Please try again later."
            },
            "request_id": request_id
        }

        # In development mode, include more details
        if app.debug:
            response_data["error"]["details"] = {
                "type": type(error).__name__,
                "message": str(error),
                "traceback": traceback.format_exc()
            }

        return jsonify(response_data), 500


def init_request_tracking(app: Flask) -> None:
    """
    Initialize request ID tracking middleware.

    Args:
        app: Flask application instance
    """

    @app.before_request
    def before_request():
        """Generate request ID before processing."""
        request_id = request.headers.get('X-Request-ID', str(uuid.uuid4()))
        request.request_id = request_id  # type: ignore

    @app.after_request
    def add_request_id_header(response):
        """Add request ID to response headers."""
        if hasattr(request, 'request_id'):
            response.headers['X-Request-ID'] = request.request_id
        return response
