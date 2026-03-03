"""
Unit Tests for Security Headers and API Versioning Modules

Test suite for security features and API versioning functionality.

Contributor: shubham21155102
"""

import pytest
from flask import Flask, Response
from security_headers import (
    SecurityHeadersConfig,
    add_security_headers,
    register_security_headers,
    SecurityAuditLogger,
    validate_security_headers
)
from api_versioning import (
    API_VERSIONS,
    APIVersion,
    add_version_headers,
    validate_api_version,
    create_versioned_blueprint,
    build_version_info
)


class TestSecurityHeaders:
    """Test suite for security headers functionality."""

    def test_production_csp_headers(self):
        """Test CSP headers for production environment."""
        config = SecurityHeadersConfig(environment="production")

        assert "script-src 'self'" in config.csp
        assert "upgrade-insecure-requests" in config.csp
        assert "block-all-mixed-content" in config.csp

    def test_development_csp_headers(self):
        """Test CSP headers for development environment."""
        config = SecurityHeadersConfig(environment="development")

        assert "unsafe-inline" in config.csp  # Allow inline scripts in dev
        assert "localhost" in config.csp  # Allow local connections

    def test_hsts_in_production(self):
        """Test HSTS is enabled in production."""
        config = SecurityHeadersConfig(environment="production")

        assert config.hsts.startswith("max-age=31536000")
        assert "includeSubDomains" in config.hsts
        assert "preload" in config.hsts

    def test_hsts_disabled_in_development(self):
        """Test HSTS is disabled in development."""
        config = SecurityHeadersConfig(environment="development")

        assert config.hsts == "max-age=0"

    def test_x_frame_options(self):
        """Test frame options prevent clickjacking."""
        config = SecurityHeadersConfig()

        assert config.x_frame_options == "DENY"

    def test_permissions_policy(self):
        """Test permissions policy restricts features."""
        config = SecurityHeadersConfig()

        assert "camera=()" in config.permissions_policy
        assert "microphone=()" in config.permissions_policy
        assert "geolocation=()" in config.permissions_policy

    def test_add_security_headers_to_response(self):
        """Test adding security headers to a Flask response."""
        config = SecurityHeadersConfig(environment="production")
        response = Response("Test content")

        secured_response = add_security_headers(response, config)

        assert "Content-Security-Policy" in secured_response.headers
        assert "Strict-Transport-Security" in secured_response.headers
        assert "X-Frame-Options" in secured_response.headers
        assert "X-Content-Type-Options" in secured_response.headers
        assert "Referrer-Policy" in secured_response.headers
        assert "Permissions-Policy" in secured_response.headers

    def test_server_header_replacement(self):
        """Test server header is replaced."""
        config = SecurityHeadersConfig()
        response = Response("Test")
        response.headers["Server"] = "Apache/2.4.41"

        secured = add_security_headers(response, config)

        assert secured.headers.get("Server") == "AI-Recruit-API"

    def test_x_powered_by_removal(self):
        """Test X-Powered-By header is removed."""
        config = SecurityHeadersConfig()
        response = Response("Test")
        response.headers["X-Powered-By"] = "Express"

        secured = add_security_headers(response, config)

        assert "X-Powered-By" not in secured.headers

    def test_cache_control_headers(self):
        """Test cache control headers prevent caching."""
        config = SecurityHeadersConfig()
        response = Response("Test")

        secured = add_security_headers(response, config)

        assert "no-store" in secured.headers.get("Cache-Control", "")
        assert "no-cache" in secured.headers.get("Cache-Control", "")


class TestSecurityAuditLogger:
    """Test suite for security audit logging."""

    def test_logger_initialization(self):
        """Test logger can be initialized."""
        logger = SecurityAuditLogger()
        assert logger.logger is not None

    def test_log_security_event(self):
        """Test logging security events."""
        logger = SecurityAuditLogger()

        # Should not raise exception
        logger.log_security_event("TEST_EVENT", {"test": "data"})

    def test_log_rate_limit_exceeded(self):
        """Test logging rate limit events."""
        logger = SecurityAuditLogger()

        # Should not raise exception
        logger.log_rate_limit_exceeded("/api/evaluate", "client_123")

    def test_log_failed_authentication(self):
        """Test logging failed authentication."""
        logger = SecurityAuditLogger()

        # Should not raise exception
        logger.log_failed_authentication("user@example.com", "invalid_credentials")

    def test_log_suspicious_activity(self):
        """Test logging suspicious activity."""
        logger = SecurityAuditLogger()

        # Should not raise exception
        logger.log_suspicious_activity("SQL_INJECTION_ATTEMPT", {"ip": "192.168.1.1"})


class TestSecurityHeaderValidation:
    """Test suite for request header validation."""

    def test_validate_valid_headers(self):
        """Test validation passes for valid headers."""
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }

        result = validate_security_headers(headers)

        assert result["valid"] is True
        assert len(result["issues"]) == 0

    def test_detect_deprecated_browser(self):
        """Test detection of deprecated browsers."""
        headers = {
            "User-Agent": "Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1)"
        }

        result = validate_security_headers(headers)

        assert result["valid"] is False
        assert any(issue["code"] == "DEPRECATED_BROWSER" for issue in result["issues"])


class TestAPIVersioning:
    """Test suite for API versioning functionality."""

    def test_api_version_data_structure(self):
        """Test API versions are properly defined."""
        assert "v1" in API_VERSIONS
        assert "status" in API_VERSIONS["v1"]
        assert "released" in API_VERSIONS["v1"]

    def test_v1_is_current(self):
        """Test v1 is marked as current version."""
        v1_info = API_VERSIONS["v1"]
        assert v1_info["status"] == "current"

    def test_validate_supported_version(self):
        """Test validation of supported API version."""
        is_valid, error = validate_api_version("v1")

        assert is_valid is True
        assert error is None

    def test_validate_unsupported_version(self):
        """Test validation of unsupported API version."""
        is_valid, error = validate_api_version("v99")

        assert is_valid is False
        assert error is not None
        assert "Unsupported API version" in error

    def test_add_version_headers(self):
        """Test adding version headers to response."""
        response = Response("Test content")
        add_version_headers(response, "v1")

        assert response.headers.get("API-Version") == "v1"
        assert response.headers.get("API-Status") == "current"
        assert response.headers.get("X-Backend-Version") == "1.0.0"

    def test_deprecated_version_headers(self):
        """Test deprecated version has deprecation headers."""
        # First mark v1 as deprecated for this test
        import api_versioning
        original_status = API_VERSIONS["v1"]["status"]
        API_VERSIONS["v1"]["status"] = "deprecated"
        API_VERSIONS["v1"]["sunset"] = "2025-12-31"

        try:
            response = Response("Test")
            add_version_headers(response, "v1")

            assert response.headers.get("API-Deprecated") == "true"
            assert response.headers.get("API-Sunset") == "2025-12-31"
        finally:
            # Restore original status
            API_VERSIONS["v1"]["status"] = original_status

    def test_build_version_info(self):
        """Test building version information response."""
        info = build_version_info()

        assert "current_version" in info
        assert "supported_versions" in info
        assert "versions" in info
        assert info["current_version"] == "v1"

    def test_api_version_is_deprecated(self):
        """Test checking if version is deprecated."""
        version = APIVersion("v1")

        # v1 should not be deprecated
        assert version.is_deprecated() is False

    def test_create_versioned_blueprint(self):
        """Test creating a versioned blueprint."""
        from flask import Flask

        app = Flask(__name__)
        blueprint = create_versioned_blueprint("test", __name__, "v1")

        assert blueprint.url_prefix == "/api/v1"

    def test_version_blueprint_before_request(self):
        """Test version is set in Flask g object."""
        from flask import Flask, g

        app = Flask(__name__)
        blueprint = create_versioned_blueprint("test", __name__, "v1")

        @blueprint.route("/test")
        def test_route():
            return {"version": g.get("api_version", "none")}

        app.register_blueprint(blueprint)

        with app.test_client() as client:
            response = client.get("/api/v1/test")
            assert response.status_code == 200
            data = response.get_json()
            assert data["version"] == "v1"


class TestIntegration:
    """Integration tests for security and versioning features."""

    def test_security_and_versioning_together(self):
        """Test security headers and versioning work together."""
        from flask import Flask

        app = Flask(__name__)
        register_security_headers(app, environment="production")

        @app.route("/api/v1/test")
        def test_endpoint():
            return {"message": "test"}

        with app.test_client() as client:
            response = client.get("/api/v1/test")

            # Check security headers are present
            assert "Content-Security-Policy" in response.headers
            assert "X-Frame-Options" in response.headers

            # Check version headers are present
            assert "API-Version" in response.headers


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
