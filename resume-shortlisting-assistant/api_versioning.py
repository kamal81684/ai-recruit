"""
API Versioning module for AI Resume Shortlisting Assistant.

This module implements versioned API endpoints following REST best practices.
All endpoints are prefixed with version identifiers (e.g., /api/v1/).

Benefits:
- Backward compatibility support
- Independent evolution of API versions
- Clear deprecation strategy
- Version-specific documentation

Contributor: shubham21155102
"""

from typing import Callable, Optional
from flask import Blueprint, request, jsonify, g
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

# Supported API versions with their status
API_VERSIONS = {
    "v1": {
        "status": "current",
        "released": "2024-01-01",
        "deprecated": None,
        "sunset": None,
    },
    "v2": {
        "status": "experimental",
        "released": None,
        "deprecated": None,
        "sunset": None,
    }
}


class APIVersion:
    """API Version information class."""

    def __init__(self, version: str, status: str = "current"):
        self.version = version
        self.status = status
        self.metadata = API_VERSIONS.get(version, {})

    def is_deprecated(self) -> bool:
        """Check if this API version is deprecated."""
        return self.metadata.get("status") == "deprecated"

    def get_sunset_date(self) -> Optional[str]:
        """Get sunset date for deprecated versions."""
        return self.metadata.get("sunset")


def add_version_headers(response, version: str) -> None:
    """
    Add API version headers to response.

    Args:
        response: Flask response object
        version: API version string (e.g., 'v1')
    """
    version_info = API_VERSIONS.get(version, {})
    response.headers['API-Version'] = version
    response.headers['API-Status'] = version_info.get('status', 'unknown')

    if version_info.get('deprecated'):
        response.headers['API-Deprecated'] = 'true'
        response.headers['API-Sunset'] = version_info.get('sunset', 'TBD')

    # Add backend version
    response.headers['X-Backend-Version'] = '1.0.0'


def validate_api_version(version: str) -> tuple[bool, Optional[str]]:
    """
    Validate if the requested API version is supported.

    Args:
        version: API version string (e.g., 'v1', 'v2')

    Returns:
        Tuple of (is_valid, error_message)
    """
    if version not in API_VERSIONS:
        return False, f"Unsupported API version: {version}. Supported versions: {', '.join(API_VERSIONS.keys())}"

    version_info = API_VERSIONS[version]
    if version_info.get('status') == 'deprecated':
        logger.warning(f"Deprecated API version {version} being used")

    return True, None


def create_versioned_blueprint(name: str, import_name: str, version: str = "v1") -> Blueprint:
    """
    Create a versioned API blueprint.

    Args:
        name: Blueprint name
        import_name: Import name for the blueprint
        version: API version (default: 'v1')

    Returns:
        Configured Blueprint with version prefix
    """
    url_prefix = f"/api/{version}"
    blueprint = Blueprint(name, import_name, url_prefix=url_prefix)

    @blueprint.before_request
    def set_api_version():
        """Store API version in Flask g object for access in routes."""
        g.api_version = version

    @blueprint.after_request
    def add_version_info(response):
        """Add version headers to all responses."""
        add_version_headers(response, version)
        return response

    return blueprint


# Version status endpoint response builder
def build_version_info() -> dict:
    """
    Build version information response for status endpoint.

    Returns:
        Dictionary with version information
    """
    return {
        "current_version": "v1",
        "supported_versions": list(API_VERSIONS.keys()),
        "versions": API_VERSIONS,
        "documentation": "/api/docs",
        "support": "https://github.com/kamal81684/ai-recruit/issues"
    }


def register_version_redirects(app) -> None:
    """
    Register redirects from unversioned to versioned endpoints.

    Args:
        app: Flask application instance
    """
    @app.route('/api/health')
    def health_redirect():
        """Redirect legacy health endpoint to v1."""
        return jsonify({
            "message": "API versioning is now required. Please use /api/v1/health",
            "new_location": "/api/v1/health",
            "current_version": "v1",
            "documentation": "/api/v1/info"
        }), 301  # Moved Permanently

    @app.route('/api/info')
    def api_info():
        """Get API version information."""
        return jsonify(build_version_info()), 200
