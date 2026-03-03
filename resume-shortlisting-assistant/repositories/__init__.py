"""
Repository Pattern for AI Resume Shortlisting Assistant.

This module provides repository abstractions for database operations,
following the Repository pattern for clean separation of data access logic.

Contributor: shubham21155102 - Repository Pattern Architecture
"""

from .base_repository import BaseRepository
from .candidate_repository import CandidateRepository
from .job_repository import JobRepository
from .analytics_repository import AnalyticsRepository

__all__ = [
    'BaseRepository',
    'CandidateRepository',
    'JobRepository',
    'AnalyticsRepository',
]
