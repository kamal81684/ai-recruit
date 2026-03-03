"""
Security Headers Middleware for AI Resume Shortlisting Assistant.

This module implements enterprise-grade security headers following OWASP
and security best practices for web applications.

Features:
- Content Security Policy (CSP)
- Strict Transport Security (HSTS)
- X-Frame-Options (Clickjacking protection)
- X-Content-Type-Options (MIME-sniffing protection)
- Referrer-Policy
- Permissions-Policy
- Cross-Origin headers

Contributor: shubham21155102
"""

from flask import Flask, Response
from typing import Optional
import os


class SecurityHeadersConfig:
    """Configuration for security headers."""

    def __init__(self, environment: str = "production"):
        self.environment = environment

        # Content Security Policy - restricts sources of content
        # For development, we allow more sources for testing
        if environment == "development":
            self.csp = (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net; "
                "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
                "font-src 'self' https://fonts.gstatic.com; "
                "img-src 'self' data: https: http:; "
                "connect-src 'self' http://localhost:* http://127.0.0.1:*; "
                "frame-ancestors 'self'; "
                "form-action 'self'; "
                "base-uri 'self'; "
                "upgrade-insecure-requests"
            )
        else:
            # Production - more restrictive
            self.csp = (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline'; "
                "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
                "font-src 'self' https://fonts.gstatic.com; "
                "img-src 'self' data: https:; "
                "connect-src 'self' https:; "
                "frame-ancestors 'none'; "
                "form-action 'self'; "
                "base-uri 'self'; "
                "upgrade-insecure-requests; "
                "block-all-mixed-content"
            )

        # Strict Transport Security - enforce HTTPS
        # Only set HSTS in production with valid HTTPS
        if environment == "production":
            self.hsts = "max-age=31536000; includeSubDomains; preload"
        else:
            self.hsts = "max-age=0"  # Disabled for development

        # Frame options - prevent clickjacking
        self.x_frame_options = "DENY"

        # Content type options - prevent MIME-sniffing
        self.x_content_type_options = "nosniff"

        # Referrer policy - control referrer information
        self.referrer_policy = "strict-origin-when-cross-origin"

        # Permissions policy (formerly Feature Policy)
        self.permissions_policy = (
            "camera=(), "
            "microphone=(), "
            "geolocation=(), "
            "payment=(), "
            "usb=(), "
            "magnetometer=(), "
            "gyroscope=(), "
            "accelerometer=()"
        )

        # Cross-Origin headers
        self.cross_origin_embedder_policy = "require-corp"
        self.cross_origin_opener_policy = "same-origin"
        self.cross_origin_resource_policy = "same-site"


def add_security_headers(response: Response, config: SecurityHeadersConfig) -> Response:
    """
    Add security headers to Flask response.

    Args:
        response: Flask Response object
        config: SecurityHeadersConfig instance

    Returns:
        Response with security headers added
    """
    # Content Security Policy
    response.headers['Content-Security-Policy'] = config.csp

    # Strict Transport Security (HTTPS enforcement)
    response.headers['Strict-Transport-Security'] = config.hsts

    # Frame options (prevent clickjacking)
    response.headers['X-Frame-Options'] = config.x_frame_options

    # Content type options (prevent MIME-sniffing)
    response.headers['X-Content-Type-Options'] = config.x_content_type_options

    # Referrer policy
    response.headers['Referrer-Policy'] = config.referrer_policy

    # Permissions policy
    response.headers['Permissions-Policy'] = config.permissions_policy

    # Additional security headers

    # X-XSS Protection (legacy but still useful for older browsers)
    response.headers['X-XSS-Protection'] = '1; mode=block'

    # Prevent caching of sensitive data
    if response.cache_control.max_age is None:
        response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'

    # Server information hiding
    response.headers['Server'] = 'AI-Recruit-API'

    # Remove X-Powered-By header (added by some frameworks)
    response.headers.pop('X-Powered-By', None)

    return response


def register_security_headers(app: Flask, environment: Optional[str] = None) -> None:
    """
    Register security headers middleware with Flask app.

    Args:
        app: Flask application instance
        environment: Environment string ('production' or 'development')
                   If None, will read from FLASK_ENV or default to 'production'
    """
    if environment is None:
        environment = os.environ.get('FLASK_ENV', 'production')

    config = SecurityHeadersConfig(environment)

    @app.after_request
    def apply_security_headers(response: Response) -> Response:
        """Apply security headers to all responses."""
        return add_security_headers(response, config)

    # Log security configuration on startup
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"Security headers configured for environment: {environment}")
    logger.info(f"CSP: {config.csp[:100]}...")
    logger.info(f"HSTS: {'Enabled' if environment == 'production' else 'Disabled (development)'}")


def get_csp_report_handler():
    """
    Get a handler for CSP violation reports.

    Returns:
        Flask route handler function for CSP reports
    """
    from flask import request
    import logging

    logger = logging.getLogger(__name__)

    def handle_csp_report():
        """Handle Content Security Policy violation reports."""
        if request.method == 'POST':
            import json
            try:
                report = request.get_json()
                logger.warning(f"CSP Violation Report: {json.dumps(report, indent=2)}")
            except Exception as e:
                logger.error(f"Failed to parse CSP report: {e}")
        return '', 204  # No content

    return handle_csp_report


def setup_csp_reporting(app: Flask) -> None:
    """
    Set up CSP violation reporting endpoint.

    Args:
        app: Flask application instance
    """
    handler = get_csp_report_handler()
    app.route('/api/security/csp-report', methods=['POST'])(handler)

    import logging
    logger = logging.getLogger(__name__)
    logger.info("CSP violation reporting endpoint registered at /api/security/csp-report")


# Security header validation for API clients
def validate_security_headers(request_headers: dict) -> dict:
    """
    Validate incoming request headers for security requirements.

    Args:
        request_headers: Dictionary of request headers

    Returns:
        Dictionary with validation results
    """
    issues = []

    # Check for secure context headers
    user_agent = request_headers.get('User-Agent', '')

    # Warn about deprecated browsers
    if 'MSIE' in user_agent or 'Trident/' in user_agent:
        issues.append({
            'code': 'DEPRECATED_BROWSER',
            'message': 'Internet Explorer is not supported. Please use a modern browser.'
        })

    # Check for proper content type on POST/PUT
    # (This should be validated per-endpoint)

    return {
        'valid': len(issues) == 0,
        'issues': issues
    }


class SecurityAuditLogger:
    """Logger for security-related events."""

    def __init__(self, app: Optional[Flask] = None):
        self.logger = logging.getLogger('security.audit')
        if app:
            self.init_app(app)

    def init_app(self, app: Flask) -> None:
        """Initialize with Flask app."""
        self.app = app

    def log_security_event(self, event_type: str, details: dict, request=None) -> None:
        """
        Log a security-related event.

        Args:
            event_type: Type of security event
            details: Event details
            request: Optional Flask request object
        """
        from flask import request

        log_data = {
            'event_type': event_type,
            'timestamp': __import__('datetime').datetime.utcnow().isoformat(),
            'ip_address': request.remote_addr if request else None,
            'user_agent': request.headers.get('User-Agent') if request else None,
            'details': details
        }

        self.logger.info(f"Security Event: {event_type} | {log_data}")

    def log_rate_limit_exceeded(self, endpoint: str, client_id: str) -> None:
        """Log rate limit exceeded event."""
        self.log_security_event('RATE_LIMIT_EXCEEDED', {
            'endpoint': endpoint,
            'client_id': client_id
        })

    def log_failed_authentication(self, username: str, reason: str) -> None:
        """Log failed authentication attempt."""
        self.log_security_event('AUTH_FAILED', {
            'username': username,
            'reason': reason
        })

    def log_suspicious_activity(self, activity_type: str, details: dict) -> None:
        """Log suspicious activity."""
        self.log_security_event('SUSPICIOUS_ACTIVITY', {
            'activity_type': activity_type,
            **details
        })
