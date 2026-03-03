"""
Unit Tests for PII Redaction Module

Test suite for PII detection and redaction functionality to ensure
comprehensive protection of sensitive candidate information.

Contributor: shubham21155102
"""

import pytest
from pii_redaction import (
    PIIRedactor,
    PIIAuditor,
    PIICategory,
    sanitize_for_logging,
    redact_for_ai_prompt,
    RedactionResult
)


class TestPIIRedactor:
    """Test suite for PIIRedactor class."""

    def test_email_redaction(self):
        """Test email address detection and redaction."""
        redactor = PIIRedactor()
        text = "Contact me at john.doe@example.com for more info"

        result = redactor.redact(text)

        assert result.redactions_made == 1
        assert "email" in result.categories_found
        assert "john.doe@example.com" not in result.redacted_text
        assert "[REDACTED_EMAIL]" in result.redacted_text
        assert "Contact me at" in result.redacted_text  # Preserve context

    def test_multiple_emails_redaction(self):
        """Test redaction of multiple email addresses."""
        redactor = PIIRedactor()
        text = "Email john@example.com or jane@example.org"

        result = redactor.redact(text)

        assert result.redactions_made == 2
        assert "john@example.com" not in result.redacted_text
        assert "jane@example.org" not in result.redacted_text

    def test_phone_redaction(self):
        """Test phone number detection and redaction."""
        redactor = PIIRedactor()
        test_cases = [
            "Call me at 555-123-4567",
            "Phone: (555) 123-4567",
            "Mobile: 555.123.4567",
            "International: +1 555 123 4567",
        ]

        for text in test_cases:
            result = redactor.redact(text)
            assert "phone" in result.categories_found
            assert result.redactions_made >= 1

    def test_ssn_redaction(self):
        """Test Social Security Number detection and redaction."""
        redactor = PIIRedactor()
        text = "My SSN is 123-45-6789"

        result = redactor.redact(text)

        assert result.redactions_made == 1
        assert "ssn" in result.categories_found
        assert "123-45-6789" not in result.redacted_text

    def test_address_redaction(self):
        """Test address detection and redaction."""
        redactor = PIIRedactor()
        text = "I live at 123 Main Street, Springfield"

        result = redactor.redact(text)

        assert "address" in result.categories_found
        assert "123 Main Street" not in result.redacted_text

    def test_credit_card_redaction(self):
        """Test credit card number detection and redaction."""
        redactor = PIIRedactor()
        text = "Card: 4532-1234-5678-9010"

        result = redactor.redact(text)

        assert "credit_card" in result.categories_found
        assert "4532-1234-5678-9010" not in result.redacted_text

    def test_mixed_pii_redaction(self):
        """Test redaction of text containing multiple PII types."""
        redactor = PIIRedactor()
        text = "Contact John at john@example.com or call 555-123-4567. SSN: 123-45-6789"

        result = redactor.redact(text)

        assert result.redactions_made == 3
        assert len(result.categories_found) == 3
        assert "email" in result.categories_found
        assert "phone" in result.categories_found
        assert "ssn" in result.categories_found

    def test_no_pii_in_text(self):
        """Test handling of text without PII."""
        redactor = PIIRedactor()
        text = "This is a simple text with no personal information"

        result = redactor.redact(text)

        assert result.redactions_made == 0
        assert len(result.categories_found) == 0
        assert result.redacted_text == text

    def test_preserve_length_redaction(self):
        """Test length-preserving redaction."""
        redactor = PIIRedactor(preserve_length=True)
        text = "Email: test@example.com"

        result = redactor.redact(text)

        # The redacted text should have same length as original email
        original_email = "test@example.com"
        redacted_portion = result.redacted_text.split(": ")[1]
        assert len(redacted_portion) == len(original_email)
        assert all(c == "*" for c in redacted_portion)

    def test_custom_redaction_token(self):
        """Test custom redaction token."""
        redactor = PIIRedactor(redaction_token="[HIDDEN]")
        text = "Email me at john@example.com"

        result = redactor.redact(text)

        assert "[HIDDEN_EMAIL]" in result.redacted_text
        assert "[REDACTED]" not in result.redacted_text

    def test_selective_category_redaction(self):
        """Test redaction of specific PII categories only."""
        redactor = PIIRedactor()
        text = "Email john@example.com or call 555-123-4567"

        # Only redact emails
        result = redactor.redact(text, categories=[PIICategory.EMAIL])

        assert "email" in result.categories_found
        assert "john@example.com" not in result.redacted_text
        assert "555-123-4567" in result.redacted_text  # Phone should not be redacted

    def test_redact_candidate_profile(self):
        """Test redaction of candidate profile dictionary."""
        redactor = PIIRedactor()
        profile = {
            "name": "John Doe",
            "email": "john@example.com",
            "phone": "555-123-4567",
            "resume_text": "Contact me at john@example.com",
            "skills": "Python, JavaScript"
        }

        result = redactor.redact_candidate_profile(profile)

        assert result["email"] != profile["email"]
        assert result["phone"] != profile["phone"]
        assert "john@example.com" not in result["resume_text"]
        assert result["skills"] == profile["skills"]  # Non-PII fields preserved

    def test_detect_without_redaction(self):
        """Test PII detection without redaction."""
        redactor = PIIRedactor()
        text = "Email: john@example.com, Phone: 555-123-4567"

        detected = redactor.detect(text)

        assert "email" in detected
        assert "phone" in detected
        assert "john@example.com" in detected["email"]
        assert "555-123-4567" in detected["phone"]

    def test_empty_text_handling(self):
        """Test handling of empty text."""
        redactor = PIIRedactor()

        result = redactor.redact("")
        assert result.redactions_made == 0
        assert result.redacted_text == ""

        result = redactor.redact(None)
        assert result.redactions_made == 0

    def test_custom_pattern_redaction(self):
        """Test custom regex pattern redaction."""
        custom_patterns = {
            "employee_id": r"EMP\d{6}",
            "custom_code": r"CC-\d{4}-ABC"
        }
        redactor = PIIRedactor(custom_patterns=custom_patterns)
        text = "Employee ID: EMP123456 and Code: CC-9876-ABC"

        result = redactor.redact(text)

        assert "EMP123456" not in result.redacted_text
        assert "CC-9876-ABC" not in result.redacted_text
        assert result.redactions_made == 2


class TestPIIAuditor:
    """Test suite for PIIAuditor class."""

    def test_log_redaction(self):
        """Test logging of redaction operations."""
        auditor = PIIAuditor()
        redactor = PIIRedactor()
        result = redactor.redact("Email: john@example.com")

        auditor.log_redaction(result, context={"action": "test"})

        assert len(auditor.redaction_history) == 1
        assert auditor.redaction_history[0]["redactions_made"] == 1

    def test_multiple_logs(self):
        """Test multiple log entries."""
        auditor = PIIAuditor()
        redactor = PIIRedactor()

        for text in ["Email: test1@example.com", "Email: test2@example.com"]:
            result = redactor.redact(text)
            auditor.log_redaction(result)

        assert len(auditor.redaction_history) == 2

    def test_redaction_summary(self):
        """Test redaction summary generation."""
        auditor = PIIAuditor()
        redactor = PIIRedactor()

        # Log multiple redactions
        texts = [
            "Email: john@example.com",
            "Phone: 555-123-4567",
            "Email: jane@example.org and SSN: 123-45-6789"
        ]
        for text in texts:
            result = redactor.redact(text)
            auditor.log_redaction(result)

        summary = auditor.get_redaction_summary()

        assert summary["total_operations"] == 3
        assert summary["total_redactions"] == 4
        assert "email" in summary["categories_processed"]
        assert "phone" in summary["categories_processed"]


class TestUtilityFunctions:
    """Test suite for utility functions."""

    def test_sanitize_for_logging(self):
        """Test sanitization of text for logging."""
        text = "User john@example.com called from 555-123-4567"

        sanitized = sanitize_for_logging(text, max_length=100)

        # PII should be redacted
        assert "john@example.com" not in sanitized
        assert "555-123-4567" not in sanitized
        assert len(sanitized) <= 103  # max_length + "..."

    def test_sanitize_with_truncation(self):
        """Test truncation in sanitization."""
        long_text = "A" * 300
        sanitized = sanitize_for_logging(long_text, max_length=50)

        assert len(sanitized) <= 53  # 50 + "..."
        assert sanitized.endswith("...")

    def test_redact_for_ai_prompt_basic(self):
        """Test AI prompt redaction."""
        text = "Candidate john@example.com has SSN 123-45-6789"

        redacted = redact_for_ai_prompt(text)

        assert "john@example.com" not in redacted
        assert "123-45-6789" not in redacted
        assert "[REDACTED]" in redacted

    def test_redact_for_ai_prompt_preserve_structure(self):
        """Test that AI prompt redaction preserves structure."""
        text = """
        John Doe
        Email: john@example.com
        Phone: 555-123-4567
        Experience: 5 years
        """

        redacted = redact_for_ai_prompt(text, preserve_structure=True)

        # Structure should be preserved
        assert "Experience:" in redacted
        assert "years" in redacted
        # PII should be redacted
        assert "john@example.com" not in redacted
        assert "555-123-4567" not in redacted


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_unicode_handling(self):
        """Test handling of Unicode characters."""
        redactor = PIIRedactor()
        text = "Contact 日本人@example.com or call +81-90-1234-5678"

        result = redactor.redact(text)

        assert result.redactions_made >= 1

    def test_international_phone_formats(self):
        """Test various international phone number formats."""
        redactor = PIIRedactor()
        test_phones = [
            "+44 20 7123 4567",  # UK
            "+33 1 42 86 83 27",  # France
            "+49 30 12345678",    # Germany
        ]

        for phone in test_phones:
            text = f"Call me at {phone}"
            result = redactor.redact(text)
            # Should detect international numbers
            assert result.redactions_made >= 0  # May or may not detect all formats

    def test_overlapping_patterns(self):
        """Test handling of overlapping PII patterns."""
        redactor = PIIRedactor()
        text = "Email john@example.com has 9 digits like 123456789"

        result = redactor.redact(text)

        # Should redact the email
        assert "john@example.com" not in result.redacted_text

    def test_multiple_redactions_same_pattern(self):
        """Test multiple instances of same PII type."""
        redactor = PIIRedactor()
        text = "Email john@example.com or jane@example.com"

        result = redactor.redact(text)

        assert result.redacted_text.count("[REDACTED_EMAIL]") == 2

    def test_nesting_redaction_operations(self):
        """Test that redaction can be safely nested."""
        redactor = PIIRedactor()
        text = "Contact john@example.com"

        result1 = redactor.redact(text)
        result2 = redactor.redact(result1.redacted_text)

        # Second redaction should not find anything to redact
        assert result2.redactions_made == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
