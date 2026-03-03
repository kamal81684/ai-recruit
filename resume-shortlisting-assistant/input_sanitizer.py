"""
Input Sanitization Module for AI Resume Shortlisting Assistant.

This module provides protection against prompt injection attacks and other
malicious input patterns that could compromise LLM interactions.

Features:
- Prompt injection pattern detection
- Input length and character validation
- Special character sanitization
- Known attack pattern signatures

Contributor: shubham21155102
"""

import re
import logging
from typing import Optional, List, Tuple
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class ThreatLevel(Enum):
    """Threat level classification."""
    SAFE = "safe"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class SanitizationResult:
    """Result of input sanitization."""
    is_safe: bool
    threat_level: ThreatLevel
    sanitized_input: Optional[str]
    detected_patterns: List[str]
    warnings: List[str]


# =============================================================================
# Known Attack Patterns
# =============================================================================

# Prompt injection patterns to detect
PROMPT_INJECTION_PATTERNS = [
    # Direct instruction override patterns
    r'(ignore|disregard|forget)\s+(all\s+)?(previous|above|earlier)\s+(instructions?|prompts?|commands?|text)',
    r'(you\s+are\s+(now\s+)?(no\s+longer|not)\s+(following|bound\s+by)\s+the\s+(above|previous|earlier))',
    r'(new\s+)?role\s*:?\s*(you\s+are\s+)?(now\s+)?(a\s+)?(different|new)',
    r'(act|behave|respond)\s+as\s+(if\s+)?(you\s+are\s+)?(a\s+)?(different|another)',
    r' pretend\s+(you\s+are)?',
    r' simulation\s+mode',
    r' hypothetical\s+scenario',

    # System prompt extraction attempts
    r'(print|output|display|show|reveal|tell\s+me)\s+(your\s+)?(system\s+)?prompt',
    r'(what\s+(are\s+)?your\s+)?(instructions?|commands?|guidelines?)',
    r'(repeat|echo)\s+(everything\s+)?(above|before)',
    r'(show\s+me\s+)?(the\s+)?(context|previous\s+text)',

    # Jailbreak patterns
    r'jailbreak',
    r'dan\s+mode',
    r'(developer|admin|root)\s+mode',
    r'(override|bypass|circumvent)\s+(safety|security|filter|restriction)',
    r'(unlock|enable)\s+(all\s+)?(features?|modes?)',

    # Output format manipulation
    r'(respond|answer|reply)\s+(only\s+)?(with|in)\s+(json|xml|yaml|code|markdown)',
    r'(don\'t|do\s+not|never)\s+(include|add|use)\s+(explanation|comment|description)',

    # Role confusion attacks
    r'you\s+are\s+(a\s+)?(helpful\s+)?assistant',
    r'you\s+are\s+(chat)?gpt',
    r'you\s+are\s+(claude|anthropic)',
    r'as\s+(an\s+)?ai\s+(language\s+)?model',

    # Data exfiltration patterns
    r'(base64|encode|decode)\s+(this\s+)?(message|text|prompt)',
    r'(translate|convert)\s+to\s+(base64|hex|binary)',

    # Instruction injection through formatting
    r'\\n\\n(\\n)?(note|remember|forget)',
    r'(---|\*\*\*)\s*(new|update|change)',
    r'(end|stop|finish)\s+(of\s+)?(prompt|context|input)',

    # Adversarial suffixes
    r'\s+(?!important)(?!urgent)(?!critical)',
]

# Suspicious character sequences
SUSPICIOUS_PATTERNS = [
    (r'<script[^>]*>', 'Script tag detected'),
    (r'javascript:', 'JavaScript protocol detected'),
    (r'on\w+\s*=', 'Event handler detected'),
    (r'<iframe', 'Iframe tag detected'),
    (r'<embed', 'Embed tag detected'),
    (r'<object', 'Object tag detected'),
]

# Maximum input lengths (characters)
MAX_LENGTHS = {
    'job_description': 10000,
    'resume_text': 50000,
    'additional_info': 2000,
    'cover_letter_tone': 100,
    'title': 255,
    'location': 255,
}


# =============================================================================
# Sanitization Functions
# =============================================================================

def sanitize_llm_input(
    input_text: str,
    input_type: str = 'general',
    allow_markdown: bool = True
) -> SanitizationResult:
    """
    Sanitize user input before sending to LLM.

    Args:
        input_text: Raw user input
        input_type: Type of input (job_description, resume_text, etc.)
        allow_markdown: Whether to allow markdown formatting

    Returns:
        SanitizationResult with safety assessment
    """
    if not input_text:
        return SanitizationResult(
            is_safe=True,
            threat_level=ThreatLevel.SAFE,
            sanitized_input="",
            detected_patterns=[],
            warnings=[]
        )

    detected_patterns = []
    warnings = []
    threat_level = ThreatLevel.SAFE
    sanitized = input_text

    # 1. Check input length
    max_length = MAX_LENGTHS.get(input_type, MAX_LENGTHS['job_description'])
    if len(input_text) > max_length:
        warnings.append(f"Input exceeds maximum length of {max_length} characters")
        threat_level = _max_threat_level(threat_level, ThreatLevel.LOW)
        sanitized = sanitized[:max_length]

    # 2. Check for prompt injection patterns
    for pattern in PROMPT_INJECTION_PATTERNS:
        matches = re.finditer(pattern, input_text, re.IGNORECASE)
        for match in matches:
            detected_patterns.append(f"Prompt injection: {match.group()[:50]}")
            threat_level = _max_threat_level(threat_level, ThreatLevel.HIGH)

    # 3. Check for suspicious HTML/script patterns
    for pattern, description in SUSPICIOUS_PATTERNS:
        if re.search(pattern, input_text, re.IGNORECASE):
            detected_patterns.append(description)
            threat_level = _max_threat_level(threat_level, ThreatLevel.CRITICAL)

    # 4. Check for excessive special characters (potential obfuscation)
    special_char_ratio = _calculate_special_char_ratio(input_text)
    if special_char_ratio > 0.3:
        warnings.append(f"High special character ratio: {special_char_ratio:.1%}")
        threat_level = _max_threat_level(threat_level, ThreatLevel.MEDIUM)

    # 5. Check for excessive whitespace/newlines (potential injection)
    consecutive_newlines = len(re.findall(r'\n\s*\n', input_text))
    if consecutive_newlines > 10:
        warnings.append(f"Excessive consecutive newlines: {consecutive_newlines}")
        threat_level = _max_threat_level(threat_level, ThreatLevel.MEDIUM)

    # 6. Check for repetition attacks
    if _has_excessive_repetition(input_text):
        warnings.append("Excessive text repetition detected")
        threat_level = _max_threat_level(threat_level, ThreatLevel.MEDIUM)

    # 7. Remove or escape dangerous patterns
    if threat_level in [ThreatLevel.HIGH, ThreatLevel.CRITICAL]:
        sanitized = _remove_dangerous_patterns(sanitized)

    # Determine if input is safe enough to proceed
    is_safe = threat_level in [ThreatLevel.SAFE, ThreatLevel.LOW]

    if not is_safe:
        logger.warning(
            f"Input sanitization blocked input with threat level {threat_level.value}. "
            f"Patterns: {detected_patterns}"
        )

    return SanitizationResult(
        is_safe=is_safe,
        threat_level=threat_level,
        sanitized_input=sanitized if is_safe else None,
        detected_patterns=detected_patterns,
        warnings=warnings
    )


def sanitize_job_description(job_description: str) -> str:
    """
    Sanitize job description input.

    Args:
        job_description: Raw job description text

    Returns:
        Sanitized job description

    Raises:
        ValueError: If input contains dangerous patterns
    """
    result = sanitize_llm_input(job_description, 'job_description')

    if not result.is_safe:
        if result.threat_level in [ThreatLevel.HIGH, ThreatLevel.CRITICAL]:
            raise ValueError(
                f"Job description contains potentially malicious content. "
                f"Detected patterns: {', '.join(result.detected_patterns)}"
            )
        # For lower threat levels, log warning but proceed
        for warning in result.warnings:
            logger.warning(f"Job description sanitization warning: {warning}")

    return result.sanitized_input or job_description


def sanitize_resume_text(resume_text: str) -> str:
    """
    Sanitize resume text input.

    Args:
        resume_text: Raw resume text

    Returns:
        Sanitized resume text

    Raises:
        ValueError: If input contains dangerous patterns
    """
    result = sanitize_llm_input(resume_text, 'resume_text')

    if not result.is_safe:
        if result.threat_level in [ThreatLevel.HIGH, ThreatLevel.CRITICAL]:
            # For resumes, be more lenient as they may contain technical content
            logger.warning(
                f"Resume text flagged with threat level {result.threat_level.value}. "
                f"Patterns: {result.detected_patterns}"
            )
        else:
            for warning in result.warnings:
                logger.warning(f"Resume text sanitization warning: {warning}")

    return result.sanitized_input or resume_text


def sanitize_additional_info(additional_info: str) -> str:
    """
    Sanitize additional information input.

    Args:
        additional_info: Raw additional info text

    Returns:
        Sanitized additional info

    Raises:
        ValueError: If input contains dangerous patterns
    """
    result = sanitize_llm_input(additional_info, 'additional_info')

    if not result.is_safe:
        if result.threat_level in [ThreatLevel.MEDIUM, ThreatLevel.HIGH, ThreatLevel.CRITICAL]:
            raise ValueError(
                f"Additional information contains potentially malicious content. "
                f"Detected patterns: {', '.join(result.detected_patterns)}"
            )

    return result.sanitized_input or additional_info


# =============================================================================
# Helper Functions
# =============================================================================

def _max_threat_level(current: ThreatLevel, new: ThreatLevel) -> ThreatLevel:
    """Return the higher threat level."""
    levels = [ThreatLevel.SAFE, ThreatLevel.LOW, ThreatLevel.MEDIUM, ThreatLevel.HIGH, ThreatLevel.CRITICAL]
    return max(levels.index(current), levels.index(new), key=lambda x: levels.index(x))


def _calculate_special_char_ratio(text: str) -> float:
    """Calculate ratio of special characters to total characters."""
    if not text:
        return 0.0

    special_chars = set(r'!@#$%^&*()_+=[]{}|;:,.<>?/~`\'"\\')
    special_count = sum(1 for c in text if c in special_chars)
    return special_count / len(text)


def _has_excessive_repetition(text: str, threshold: int = 5) -> bool:
    """Check for excessive character or word repetition."""
    # Check for character repetition
    if re.search(r'(.)\1{10,}', text):
        return True

    # Check for word repetition
    words = text.lower().split()
    for i in range(len(words) - threshold):
        if len(set(words[i:i + threshold])) == 1:
            return True

    return False


def _remove_dangerous_patterns(text: str) -> str:
    """Remove or escape potentially dangerous patterns."""
    # Remove script tags and content
    text = re.sub(r'<script[^>]*>.*?</script>', '', text, flags=re.IGNORECASE | re.DOTALL)

    # Remove other HTML tags
    text = re.sub(r'<[^>]+>', '', text)

    # Escape markdown code blocks that could be used for injection
    text = re.sub(r'```', '\\`\\`\\`', text)

    # Remove excessive newlines
    text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)

    return text.strip()


# =============================================================================
# Batch Sanitization
# =============================================================================

def sanitize_batch(inputs: dict) -> dict:
    """
    Sanitize multiple inputs at once.

    Args:
        inputs: Dictionary of input_name -> input_text

    Returns:
        Dictionary of sanitized inputs

    Raises:
        ValueError: If any input contains dangerous patterns
    """
    sanitized = {}
    errors = {}

    for key, value in inputs.items():
        try:
            if key == 'job_description':
                sanitized[key] = sanitize_job_description(value)
            elif key == 'resume_text':
                sanitized[key] = sanitize_resume_text(value)
            elif key == 'additional_info':
                sanitized[key] = sanitize_additional_info(value)
            else:
                sanitized[key] = sanitize_llm_input(value, key).sanitized_input or value
        except ValueError as e:
            errors[key] = str(e)

    if errors:
        raise ValueError(f"Sanitization errors: {errors}")

    return sanitized
