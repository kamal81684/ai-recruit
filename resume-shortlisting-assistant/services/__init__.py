"""
Service Layer for AI Resume Shortlisting Assistant.

This module provides a clean separation between business logic and API controllers.
Each service encapsulates specific business rules and use cases.

Contributor: shubham21155102 - Service Layer Architecture
"""

from .candidate_service import CandidateService
from .job_service import JobService
from .evaluation_service import EvaluationService
from .analytics_service import AnalyticsService

__all__ = [
    'CandidateService',
    'JobService',
    'EvaluationService',
    'AnalyticsService',
]
