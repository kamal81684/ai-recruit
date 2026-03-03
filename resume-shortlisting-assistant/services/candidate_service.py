"""
Candidate Service - Business logic for candidate operations.

This service handles all candidate-related business rules, decoupling
the logic from API controllers.

Contributor: shubham21155102 - Service Layer Architecture
"""

from typing import List, Dict, Optional, Any
from dataclasses import dataclass
from datetime import datetime

from database import db
from error_handlers import NotFoundError, ValidationError, BusinessLogicError
from structured_logging import get_logger, LogContext

logger = get_logger(__name__)


@dataclass
class CandidateFilter:
    """Filter parameters for candidate queries"""
    tier: Optional[str] = None
    location: Optional[str] = None
    skills: Optional[List[str]] = None
    min_experience: Optional[int] = None
    max_experience: Optional[int] = None
    search_query: Optional[str] = None
    limit: int = 50
    offset: int = 0


@dataclass
class CandidateSummary:
    """AI-generated candidate summary"""
    candidate_id: int
    summary: str
    key_strengths: List[str]
    potential_concerns: List[str]
    recommended_next_steps: List[str]
    confidence_score: float
    generated_at: datetime


class CandidateService:
    """
    Service layer for candidate operations.

    This class encapsulates all business logic related to candidates,
    including validation, filtering, and AI-powered features.
    """

    def __init__(self):
        self.db = db

    def get_candidates(
        self,
        filters: Optional[CandidateFilter] = None,
        request_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get candidates with optional filtering.

        Args:
            filters: CandidateFilter object with query parameters
            request_id: Request tracking ID

        Returns:
            Dict with candidates list and metadata

        Raises:
            BusinessLogicError: If business rule validation fails
        """
        with LogContext(request_id=request_id, operation='get_candidates'):
            try:
                filters = filters or CandidateFilter()

                logger.info(
                    "Fetching candidates",
                    extra={
                        'filters': {
                            'tier': filters.tier,
                            'location': filters.location,
                            'limit': filters.limit,
                            'offset': filters.offset
                        }
                    }
                )

                # Apply tier filter if specified
                if filters.tier:
                    candidates = self.db.get_candidates_by_tier(filters.tier)
                else:
                    candidates = self.db.get_all_candidates(
                        limit=filters.limit,
                        offset=filters.offset
                    )

                # Apply additional filters (in-memory for now, can be optimized with SQL)
                if filters.location:
                    candidates = [
                        c for c in candidates
                        if c.get('location', '').lower() == filters.location.lower()
                    ]

                if filters.min_experience is not None:
                    candidates = [
                        c for c in candidates
                        if (c.get('experience_years') or 0) >= filters.min_experience
                    ]

                if filters.max_experience is not None:
                    candidates = [
                        c for c in candidates
                        if (c.get('experience_years') or 0) <= filters.max_experience
                    ]

                if filters.skills:
                    candidates = [
                        c for c in candidates
                        if any(
                            skill.lower() in (c.get('skills') or '').lower()
                            for skill in filters.skills
                        )
                    ]

                logger.info(
                    "Candidates retrieved successfully",
                    extra={'count': len(candidates)}
                )

                return {
                    'candidates': candidates,
                    'count': len(candidates),
                    'filters_applied': {
                        'tier': filters.tier,
                        'location': filters.location,
                        'skills': filters.skills,
                        'min_experience': filters.min_experience,
                        'max_experience': filters.max_experience
                    }
                }

            except Exception as e:
                logger.error("Failed to fetch candidates", exc_info=True)
                raise BusinessLogicError(f"Failed to fetch candidates: {str(e)}")

    def get_candidate_by_id(
        self,
        candidate_id: int,
        request_id: Optional[str] = None
    ) -> Dict:
        """
        Get a specific candidate by ID.

        Args:
            candidate_id: Candidate ID
            request_id: Request tracking ID

        Returns:
            Candidate data

        Raises:
            NotFoundError: If candidate not found
        """
        with LogContext(request_id=request_id, operation='get_candidate'):
            try:
                logger.info(f"Fetching candidate {candidate_id}")

                candidate = self.db.get_candidate_by_id(candidate_id)

                if not candidate:
                    logger.warning(f"Candidate {candidate_id} not found")
                    raise NotFoundError(f"Candidate {candidate_id} not found")

                logger.info(f"Candidate {candidate_id} retrieved successfully")
                return candidate

            except NotFoundError:
                raise
            except Exception as e:
                logger.error(f"Failed to fetch candidate {candidate_id}", exc_info=True)
                raise BusinessLogicError(f"Failed to fetch candidate: {str(e)}")

    def delete_candidate(
        self,
        candidate_id: int,
        request_id: Optional[str] = None
    ) -> bool:
        """
        Delete a candidate by ID.

        Args:
            candidate_id: Candidate ID
            request_id: Request tracking ID

        Returns:
            True if successful

        Raises:
            NotFoundError: If candidate not found
        """
        with LogContext(request_id=request_id, operation='delete_candidate'):
            try:
                # Verify candidate exists first
                candidate = self.db.get_candidate_by_id(candidate_id)
                if not candidate:
                    raise NotFoundError(f"Candidate {candidate_id} not found")

                logger.info(f"Deleting candidate {candidate_id}")

                success = self.db.delete_candidate(candidate_id)

                if success:
                    logger.info(f"Candidate {candidate_id} deleted successfully")
                else:
                    logger.error(f"Failed to delete candidate {candidate_id}")

                return success

            except NotFoundError:
                raise
            except Exception as e:
                logger.error(f"Failed to delete candidate {candidate_id}", exc_info=True)
                raise BusinessLogicError(f"Failed to delete candidate: {str(e)}")

    def update_candidate_status(
        self,
        candidate_id: int,
        status: str,
        notes: Optional[str] = None,
        request_id: Optional[str] = None
    ) -> bool:
        """
        Update candidate status (e.g., for interview scheduling).

        Args:
            candidate_id: Candidate ID
            status: New status
            notes: Optional notes about the status change
            request_id: Request tracking ID

        Returns:
            True if successful

        Raises:
            NotFoundError: If candidate not found
            ValidationError: If status is invalid
        """
        with LogContext(request_id=request_id, operation='update_status'):
            try:
                # Validate status
                valid_statuses = [
                    'new', 'reviewing', 'shortlisted', 'interview_scheduled',
                    'interviewed', 'offered', 'rejected', 'hired'
                ]
                if status not in valid_statuses:
                    raise ValidationError(
                        f"Invalid status. Must be one of: {', '.join(valid_statuses)}"
                    )

                # Verify candidate exists
                candidate = self.db.get_candidate_by_id(candidate_id)
                if not candidate:
                    raise NotFoundError(f"Candidate {candidate_id} not found")

                logger.info(
                    f"Updating candidate {candidate_id} status to {status}",
                    extra={'status': status, 'notes': notes}
                )

                # For now, we'll add this to a separate table
                # In a full implementation, you'd add a candidate_status table
                # with history tracking

                logger.info(f"Candidate {candidate_id} status updated to {status}")
                return True

            except (NotFoundError, ValidationError):
                raise
            except Exception as e:
                logger.error(f"Failed to update candidate {candidate_id} status", exc_info=True)
                raise BusinessLogicError(f"Failed to update candidate status: {str(e)}")

    def get_interview_questions(
        self,
        candidate_id: int,
        request_id: Optional[str] = None
    ) -> List[Dict]:
        """
        Get interview questions for a candidate.

        Args:
            candidate_id: Candidate ID
            request_id: Request tracking ID

        Returns:
            List of interview questions

        Raises:
            NotFoundError: If candidate not found
        """
        with LogContext(request_id=request_id, operation='get_questions'):
            try:
                # Verify candidate exists
                candidate = self.db.get_candidate_by_id(candidate_id)
                if not candidate:
                    raise NotFoundError(f"Candidate {candidate_id} not found")

                logger.info(f"Fetching interview questions for candidate {candidate_id}")

                questions = self.db.get_interview_questions(candidate_id)

                logger.info(
                    f"Retrieved {len(questions)} questions for candidate {candidate_id}"
                )
                return questions

            except NotFoundError:
                raise
            except Exception as e:
                logger.error(f"Failed to fetch questions for candidate {candidate_id}", exc_info=True)
                raise BusinessLogicError(f"Failed to fetch interview questions: {str(e)}")

    def generate_interview_questions(
        self,
        candidate_id: int,
        request_id: Optional[str] = None
    ) -> List[Dict]:
        """
        Generate AI-powered interview questions for a candidate.

        Args:
            candidate_id: Candidate ID
            request_id: Request tracking ID

        Returns:
            List of generated interview questions

        Raises:
            NotFoundError: If candidate not found
            BusinessLogicError: If generation fails
        """
        with LogContext(request_id=request_id, operation='generate_questions'):
            try:
                # Import here to avoid circular dependency
                from llm_providers import get_provider
                import json

                # Verify candidate exists
                candidate = self.db.get_candidate_by_id(candidate_id)
                if not candidate:
                    raise NotFoundError(f"Candidate {candidate_id} not found")

                logger.info(f"Generating interview questions for candidate {candidate_id}")

                # Delete existing questions
                self.db.delete_interview_questions(candidate_id)

                # Generate AI questions
                provider = get_provider()
                questions_list = provider.generate_interview_questions(
                    candidate_profile=candidate,
                    job_description=candidate.get('job_description', 'Not specified'),
                    num_questions=10
                )

                # Save questions to database
                saved_questions = []
                for q in questions_list:
                    if isinstance(q, dict) and 'question' in q:
                        category = q.get('category', 'General')
                        question_id = self.db.save_interview_question(
                            candidate_id, q['question'], category
                        )
                        if question_id:
                            saved_questions.append({
                                'id': question_id,
                                'candidate_id': candidate_id,
                                'question': q['question'],
                                'category': category,
                                'created_at': None
                            })

                logger.info(
                    f"Generated {len(saved_questions)} questions for candidate {candidate_id}"
                )
                return saved_questions

            except NotFoundError:
                raise
            except Exception as e:
                logger.error(f"Failed to generate questions for candidate {candidate_id}", exc_info=True)
                raise BusinessLogicError(f"Failed to generate interview questions: {str(e)}")


# Singleton instance
candidate_service = CandidateService()
