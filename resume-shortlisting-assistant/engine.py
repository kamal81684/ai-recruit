"""
Evaluation engine for AI Resume Shortlisting Assistant.

This module provides resume evaluation, job post generation, and PDF text extraction
using pluggable LLM providers (Groq, OpenAI, Anthropic, etc.).

Architecture improvements:
- Provider abstraction for easy LLM swapping
- Centralized configuration with validation
- Separated prompt management
- Type-safe structured outputs

Contributor: shubham21155102 - Architecture refactored for provider abstraction
"""

import os
from io import BytesIO
from typing import Optional
from pypdf import PdfReader
from pydantic import BaseModel, Field

# Import new architecture modules
from config import get_config
from llm_providers import (
    get_provider,
    BaseLLMProvider,
    EvaluationScore,
    CandidateEvaluation,
    JobPostGeneration
)
from prompts import (
    get_resume_evaluation_prompt,
    get_job_post_generation_prompt,
    get_candidate_info_extraction_prompt
)


# =============================================================================
# Public API Functions
# =============================================================================

def extract_text_from_pdf(pdf_file: BytesIO) -> str:
    """
    Extracts text from a loaded PDF BytesIO object.

    Args:
        pdf_file: PDF file as BytesIO object

    Returns:
        Extracted text content

    Raises:
        ValueError: If PDF parsing fails
    """
    try:
        reader = PdfReader(pdf_file)
        text = ""
        for page in reader.pages:
            extracted_text = page.extract_text()
            if extracted_text:
                text += extracted_text + "\n"
        return text.strip()
    except Exception as e:
        raise ValueError(f"Failed to parse PDF: {str(e)}")


def evaluate_resume(resume_text: str, jd_text: str) -> CandidateEvaluation:
    """
    Evaluates a resume against a job description using the configured LLM provider.

    This function now uses the provider abstraction layer, allowing you to swap
    LLM providers (Groq, OpenAI, Anthropic, etc.) by changing configuration.

    Args:
        resume_text: Extracted text from candidate's resume
        jd_text: Job description text

    Returns:
        CandidateEvaluation: Structured evaluation with scores and explanations

    Raises:
        ValueError: If configuration is invalid
    """
    # Validate configuration on first call
    config = get_config()

    if not config.llm.api_key:
        raise ValueError(
            f"LLM API key not found. Please set {config.llm_provider.upper()}_API_KEY "
            "environment variable."
        )

    # Get the configured provider and evaluate
    provider = get_provider()
    return provider.evaluate_resume(resume_text, jd_text)


def generate_job_post(
    title: str,
    location: Optional[str] = None,
    additional_info: Optional[str] = None
) -> dict:
    """
    Generate a comprehensive job post using AI.

    Args:
        title: Job title
        location: Job location (optional)
        additional_info: Additional context for generation (optional)

    Returns:
        Dict with 'description' and 'requirements' keys

    Raises:
        ValueError: If configuration is invalid
    """
    # Validate configuration
    config = get_config()

    if not config.llm.api_key:
        raise ValueError(
            f"LLM API key not found. Please set {config.llm_provider.upper()}_API_KEY "
            "environment variable."
        )

    # Get the configured provider and generate
    provider = get_provider()
    return provider.generate_job_post(title, location, additional_info)


def extract_candidate_info(resume_text: str) -> dict:
    """
    Extract key information from a resume using AI.

    This function extracts structured information like name, email, skills, etc.

    Args:
        resume_text: Raw text extracted from resume PDF

    Returns:
        Dict with keys: name, email, phone, location, skills, education,
                       experience_years, current_role
    """
    # This would use the LLM provider for extraction
    # For now, returning a placeholder implementation
    # TODO: Implement full AI-based extraction using the provider pattern

    config = get_config()

    if not config.llm.api_key:
        raise ValueError(
            f"LLM API key not found. Please set {config.llm_provider.upper()}_API_KEY "
            "environment variable."
        )

    # Simple extraction logic (could be enhanced with LLM-based extraction)
    info = {
        'name': None,
        'email': None,
        'phone': None,
        'location': None,
        'skills': None,
        'education': None,
        'experience_years': None,
        'current_role': None
    }

    # Basic extraction patterns (placeholder - should use LLM)
    lines = resume_text.split('\n')
    for line in lines[:20]:  # Check first 20 lines
        line = line.strip()
        if '@' in line and '.' in line and not info['email']:
            info['email'] = line
        # Add more patterns as needed

    return info


# =============================================================================
# Legacy API Compatibility Layer
# =============================================================================

# Re-export types for backward compatibility
__all__ = [
    'extract_text_from_pdf',
    'evaluate_resume',
    'generate_job_post',
    'extract_candidate_info',
    'EvaluationScore',
    'CandidateEvaluation',
    'JobPostGeneration',
]
