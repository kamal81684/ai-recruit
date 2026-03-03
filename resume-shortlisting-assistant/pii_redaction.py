"""
PII (Personally Identifiable Information) Redaction Utility

This module provides enterprise-grade PII detection and redaction capabilities
for handling sensitive candidate information. It helps protect privacy and ensures
compliance with data protection regulations like GDPR and CCPA.

Features:
- Email address detection and redaction
- Phone number detection and redaction (international formats)
- SSN/SIN detection and redaction
- Address detection and redaction
- Credit card number detection
- Custom pattern redaction
- Redaction audit logging

Contributor: shubham21155102
"""

import re
import logging
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class PIICategory(Enum):
    """Categories of PII that can be redacted."""
    EMAIL = "email"
    PHONE = "phone"
    SSN = "ssn"
    ADDRESS = "address"
    CREDIT_CARD = "credit_card"
    DATE_OF_BIRTH = "date_of_birth"
    PASSPORT = "passport"
    DRIVERS_LICENSE = "drivers_license"
    CUSTOM = "custom"


@dataclass
class RedactionResult:
    """Result of a redaction operation."""
    original_text: str
    redacted_text: str
    redactions_made: int
    categories_found: List[str]
    audit_log: List[Dict[str, Any]]


class PIIRedactor:
    """
    PII Redaction utility for detecting and redacting sensitive information.

    Example:
        redactor = PIIRedactor()
        result = redactor.redact("Call me at 555-123-4567")
        # Result: "Call me at [REDACTED_PHONE]"
    """

    def __init__(self,
                 redaction_token: str = "[REDACTED]",
                 preserve_length: bool = False,
                 custom_patterns: Optional[Dict[str, str]] = None):
        """
        Initialize the PII Redactor.

        Args:
            redaction_token: Token to replace redacted content with
            preserve_length: If True, preserve original length with * characters
            custom_patterns: Dictionary of custom regex patterns to redact
        """
        self.redaction_token = redaction_token
        self.preserve_length = preserve_length
        self.custom_patterns = custom_patterns or {}
        self._audit_log = []

        # Compile regex patterns for better performance
        self._patterns = self._compile_patterns()

    def _compile_patterns(self) -> Dict[PIICategory, List[re.Pattern]]:
        """Compile all regex patterns for PII detection."""
        return {
            PIICategory.EMAIL: [
                # Standard email format
                re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'),
            ],
            PIICategory.PHONE: [
                # US format: (555) 123-4567, 555-123-4567, 555.123.4567
                re.compile(r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}'),
                # International: +1 555 123 4567
                re.compile(r'\+\d{1,3}[-.\s]?\(?\d{1,4}\)?[-.\s]?\d{1,4}[-.\s]?\d{1,4}[-.\s]?\d{1,9}'),
                # 10 digit continuous
                re.compile(r'\b\d{10}\b'),
            ],
            PIICategory.SSN: [
                # SSN format: 123-45-6789
                re.compile(r'\b\d{3}-\d{2}-\d{4}\b'),
                # SSN without dashes
                re.compile(r'\b\d{9}\b'),
            ],
            PIICategory.ADDRESS: [
                # Street address pattern
                re.compile(r'\d+\s+[A-Za-z\s]+(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Lane|Ln|Drive|Dr|Court|Ct|Way|Place|Pl)\b', re.IGNORECASE),
                # ZIP code
                re.compile(r'\b\d{5}(?:-\d{4})?\b'),
            ],
            PIICategory.CREDIT_CARD: [
                # Credit card formats (Visa, MC, Amex, Discover)
                re.compile(r'\b(?:4[0-9]{12}(?:[0-9]{3})?|5[1-5][0-9]{14}|3[47][0-9]{13}|3[0-9]{13}|6(?:011|5[0-9]{2})[0-9]{12})\b'),
                # Credit card with spaces/dashes
                re.compile(r'\b(?:\d{4}[-\s]?){3}\d{4}\b'),
            ],
            PIICategory.DATE_OF_BIRTH: [
                # DOB patterns: MM/DD/YYYY, DD-MM-YYYY, etc.
                re.compile(r'\b(?:0[1-9]|1[0-2])[/\-\.](?:0[1-9]|[12][0-9]|3[01])[/\-\.]\d{4}\b'),
                re.compile(r'\b(?:0[1-9]|[12][0-9]|3[01])[/\-\.](?:0[1-9]|1[0-2])[/\-\.]\d{4}\b'),
            ],
        }

    def _redact_with_token(self, match: re.Match, category: PIICategory) -> str:
        """
        Redact a matched pattern with the appropriate token.

        Args:
            match: Regex match object
            category: Category of PII

        Returns:
            Redacted string
        """
        original = match.group(0)

        if self.preserve_length:
            return '*' * len(original)
        else:
            return f"{self.redaction_token}_{category.value.upper()}"

    def redact(self, text: str, categories: Optional[List[PIICategory]] = None) -> RedactionResult:
        """
        Redact PII from the given text.

        Args:
            text: Text to redact
            categories: List of PII categories to redact. If None, redacts all.

        Returns:
            RedactionResult with details about what was redacted
        """
        if not text:
            return RedactionResult(
                original_text=text,
                redacted_text=text,
                redactions_made=0,
                categories_found=[],
                audit_log=[]
            )

        result_text = text
        categories_found = set()
        total_redactions = 0
        self._audit_log = []

        categories_to_check = categories or list(PIICategory)[:-1]  # Exclude CUSTOM

        for category in categories_to_check:
            if category not in self._patterns:
                continue

            patterns = self._patterns[category]
            for pattern in patterns:
                matches = list(pattern.finditer(result_text))
                if matches:
                    categories_found.add(category.value)
                    for match in matches:
                        original = match.group(0)
                        redacted = self._redact_with_token(match, category)
                        result_text = result_text.replace(original, redacted)
                        total_redactions += 1

                        self._audit_log.append({
                            'category': category.value,
                            'original': original if not self.preserve_length else '*' * len(original),
                            'redacted': redacted,
                            'position': match.start(),
                            'length': len(original)
                        })

        # Handle custom patterns if provided
        for name, pattern_str in self.custom_patterns.items():
            pattern = re.compile(pattern_str)
            matches = list(pattern.finditer(result_text))
            if matches:
                categories_found.add(name)
                for match in matches:
                    original = match.group(0)
                    redacted = f"{self.redaction_token}_{name.upper()}"
                    result_text = result_text.replace(original, redacted)
                    total_redactions += 1

        return RedactionResult(
            original_text=text,
            redacted_text=result_text,
            redactions_made=total_redactions,
            categories_found=list(categories_found),
            audit_log=self._audit_log
        )

    def detect(self, text: str) -> Dict[str, List[str]]:
        """
        Detect PII in text without redacting.

        Args:
            text: Text to analyze

        Returns:
            Dictionary mapping categories to list of found items
        """
        result = {}

        for category, patterns in self._patterns.items():
            found = []
            for pattern in patterns:
                matches = pattern.findall(text)
                found.extend(matches)

            if found:
                result[category.value] = found

        return result

    def redact_candidate_profile(self, profile: Dict[str, Any]) -> Dict[str, Any]:
        """
        Redact PII from a candidate profile dictionary.

        Args:
            profile: Candidate profile dictionary

        Returns:
            Profile with redacted values
        """
        redacted = profile.copy()

        # Fields to redact
        pii_fields = [
            'name', 'email', 'phone', 'mobile', 'address', 'location',
            'ssn', 'social_security', 'date_of_birth', 'dob'
        ]

        for field in pii_fields:
            if field in redacted and isinstance(redacted[field], str):
                result = self.redact(redacted[field])
                redacted[field] = result.redacted_text

        # Redact within resume text
        if 'resume_text' in redacted and isinstance(redacted['resume_text'], str):
            result = self.redact(redacted['resume_text'])
            redacted['resume_text'] = result.redacted_text
            redacted['_pii_redaction_summary'] = {
                'redactions_made': result.redactions_made,
                'categories_found': result.categories_found
            }

        return redacted


class PIIAuditor:
    """Auditor for tracking PII redaction operations."""

    def __init__(self):
        self.redaction_history = []

    def log_redaction(self, result: RedactionResult, context: Optional[Dict] = None) -> None:
        """
        Log a redaction operation for audit purposes.

        Args:
            result: RedactionResult from a redaction operation
            context: Optional context information
        """
        log_entry = {
            'timestamp': __import__('datetime').datetime.utcnow().isoformat(),
            'redactions_made': result.redactions_made,
            'categories_found': result.categories_found,
            'context': context or {}
        }

        self.redaction_history.append(log_entry)

        # Log to system logger
        logger.info(f"PII Redaction: {result.redactions_made} items redacted. "
                   f"Categories: {', '.join(result.categories_found)}")

    def get_redaction_summary(self) -> Dict[str, Any]:
        """Get summary of all redaction operations."""
        total_redactions = sum(entry['redactions_made'] for entry in self.redaction_history)
        all_categories = set()
        for entry in self.redaction_history:
            all_categories.update(entry['categories_found'])

        return {
            'total_redactions': total_redactions,
            'total_operations': len(self.redaction_history),
            'categories_processed': list(all_categories),
            'history': self.redaction_history
        }


def sanitize_for_logging(text: str, max_length: int = 200) -> str:
    """
    Sanitize text for logging by redacting PII and limiting length.

    Args:
        text: Text to sanitize
        max_length: Maximum length to return

    Returns:
        Sanitized text safe for logging
    """
    redactor = PIIRedactor(redaction_token="[REDACTED]")
    result = redactor.redact(text)

    # Truncate if too long
    if len(result.redacted_text) > max_length:
        return result.redacted_text[:max_length] + "..."

    return result.redacted_text


def redact_for_ai_prompt(text: str, preserve_structure: bool = True) -> str:
    """
    Redact PII from text intended for AI prompts while preserving structure.

    This function ensures that PII is not sent to LLMs for privacy and
    to prevent PII leakage in AI training data.

    Args:
        text: Text to redact
        preserve_structure: If True, preserve document structure

    Returns:
        Redacted text safe for AI processing
    """
    # Use length-preserving redaction to maintain document structure
    redactor = PIIRedactor(
        redaction_token="[REDACTED]",
        preserve_length=preserve_structure
    )

    result = redactor.redact(text)

    logger.info(f"Redacted {result.redactions_made} PII items before AI processing. "
                f"Categories: {result.categories_found}")

    return result.redacted_text
