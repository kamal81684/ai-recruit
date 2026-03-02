"""
Pydantic validation models for AI Resume Shortlisting Assistant API.

This module provides input validation for all API endpoints, ensuring
data integrity and preventing malicious payloads.

Features:
- Type-safe input validation
- Automatic field sanitization
- Clear error messages
- Reusable validation schemas

Contributor: shubham21155102
"""

from typing import Optional, List
from pydantic import BaseModel, Field, validator, EmailStr
from enum import Enum


class TierEnum(str, Enum):
    """Valid tier classifications."""
    TIER_A = "Tier A"
    TIER_B = "Tier B"
    TIER_C = "Tier C"


class JobStatusEnum(str, Enum):
    """Valid job post statuses."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    DRAFT = "draft"
    CLOSED = "closed"


class QuestionCategoryEnum(str, Enum):
    """Valid interview question categories."""
    TECHNICAL = "Technical"
    BEHAVIORAL = "Behavioral"
    SITUATIONAL = "Situational"
    CULTURAL = "Cultural"
    GENERAL = "General"


# =============================================================================
# Request Models
# =============================================================================

class EvaluateCandidateRequest(BaseModel):
    """Validation model for candidate evaluation requests."""

    job_description: str = Field(
        ...,
        min_length=50,
        max_length=10000,
        description="Full job description text"
    )

    @validator('job_description')
    def validate_job_description(cls, v):
        """Ensure job description contains meaningful content."""
        if len(v.strip()) < 50:
            raise ValueError('Job description must be at least 50 characters long')
        return v.strip()


class CreateJobPostRequest(BaseModel):
    """Validation model for creating job posts."""

    title: str = Field(
        ...,
        min_length=3,
        max_length=255,
        description="Job title"
    )
    description: str = Field(
        ...,
        min_length=50,
        max_length=10000,
        description="Job description"
    )
    location: Optional[str] = Field(
        None,
        max_length=255,
        description="Job location"
    )
    requirements: Optional[str] = Field(
        None,
        max_length=5000,
        description="Job requirements"
    )
    status: JobStatusEnum = Field(
        default=JobStatusEnum.ACTIVE,
        description="Job post status"
    )

    @validator('title')
    def validate_title(cls, v):
        """Ensure title is not empty or just whitespace."""
        if not v.strip():
            raise ValueError('Title cannot be empty or whitespace only')
        return v.strip()

    @validator('description')
    def validate_description(cls, v):
        """Ensure description contains meaningful content."""
        if len(v.strip()) < 50:
            raise ValueError('Description must be at least 50 characters long')
        return v.strip()


class UpdateJobPostRequest(BaseModel):
    """Validation model for updating job posts."""

    title: Optional[str] = Field(None, min_length=3, max_length=255)
    description: Optional[str] = Field(None, min_length=50, max_length=10000)
    location: Optional[str] = Field(None, max_length=255)
    requirements: Optional[str] = Field(None, max_length=5000)
    status: Optional[JobStatusEnum] = None

    @validator('title')
    def validate_title(cls, v):
        """Validate title if provided."""
        if v is not None and not v.strip():
            raise ValueError('Title cannot be empty or whitespace only')
        return v.strip() if v else v

    @validator('description')
    def validate_description(cls, v):
        """Validate description if provided."""
        if v is not None and len(v.strip()) < 50:
            raise ValueError('Description must be at least 50 characters long')
        return v.strip() if v else v


class GenerateJobPostRequest(BaseModel):
    """Validation model for AI job post generation."""

    title: str = Field(
        ...,
        min_length=3,
        max_length=255,
        description="Job title for generation"
    )
    location: Optional[str] = Field(
        None,
        max_length=255,
        description="Optional location context"
    )
    additional_info: Optional[str] = Field(
        None,
        max_length=2000,
        description="Additional context for AI generation"
    )

    @validator('title')
    def validate_title(cls, v):
        """Ensure title is not empty or just whitespace."""
        if not v.strip():
            raise ValueError('Title cannot be empty or whitespace only')
        return v.strip()


class GenerateQuestionsRequest(BaseModel):
    """Validation model for generating interview questions."""

    num_questions: int = Field(
        default=10,
        ge=1,
        le=20,
        description="Number of questions to generate (1-20)"
    )

    @validator('num_questions')
    def validate_num_questions(cls, v):
        """Ensure reasonable number of questions."""
        if v < 1:
            raise ValueError('At least 1 question must be requested')
        if v > 20:
            raise ValueError('Cannot generate more than 20 questions at once')
        return v


# =============================================================================
# Response Models
# =============================================================================

class EvaluationScoreResponse(BaseModel):
    """Response model for evaluation scores."""

    score: int = Field(..., ge=0, le=100, description="Score from 0-100")
    explanation: str = Field(..., description="Detailed explanation of the score")


class CandidateEvaluationResponse(BaseModel):
    """Response model for candidate evaluation results."""

    tier: TierEnum = Field(..., description="Candidate tier classification")
    summary: str = Field(..., description="Overall evaluation summary")
    exact_match: EvaluationScoreResponse
    similarity_match: EvaluationScoreResponse
    achievement_impact: EvaluationScoreResponse
    ownership: EvaluationScoreResponse
    candidate_id: Optional[int] = Field(None, description="Database candidate ID")
    extracted_info: Optional[dict] = Field(None, description="Extracted candidate information")


class InterviewQuestionResponse(BaseModel):
    """Response model for interview questions."""

    id: int
    candidate_id: int
    question: str
    category: QuestionCategoryEnum
    created_at: Optional[str] = None


class JobPostResponse(BaseModel):
    """Response model for job posts."""

    id: int
    title: str
    description: str
    location: Optional[str]
    requirements: Optional[str]
    status: JobStatusEnum
    created_at: str
    updated_at: str


class StatisticsResponse(BaseModel):
    """Response model for statistics."""

    total_candidates: int
    by_tier: dict[str, int]
    average_scores: dict[str, float]


class SkillGapAnalysisRequest(BaseModel):
    """Request model for skill gap analysis."""

    job_skills: List[str] = Field(
        ...,
        min_items=1,
        max_items=50,
        description="Required skills for the position"
    )

    @validator('job_skills')
    def validate_job_skills(cls, v):
        """Ensure skills are not empty strings."""
        cleaned = [s.strip().lower() for s in v if s.strip()]
        if not cleaned:
            raise ValueError('At least one valid skill is required')
        return cleaned


class SkillGapAnalysisResponse(BaseModel):
    """Response model for skill gap analysis."""

    missing_skills: List[str] = Field(..., description="Skills not found in candidate pool")
    coverage_percentage: float = Field(..., description="Percentage of skills covered by candidates")
    candidate_count: int = Field(..., description="Number of candidates analyzed")
    recommendations: List[str] = Field(..., description="Recommendations for addressing gaps")
