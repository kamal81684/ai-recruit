"""
Service Layer for AI Resume Shortlisting Assistant.

This module implements the Service Layer pattern, decoupling business logic
from the API controllers. Services act as intermediaries between the API layer
and the core business logic/engine.

Benefits:
1. Separation of concerns - API handles HTTP, Services handle business logic
2. Reusability - Services can be used by multiple endpoints
3. Testability - Services can be unit tested independently
4. Transaction management - Services can manage database transactions
5. Caching - Services can implement caching strategies

Contributor: shubham21155102
"""

import logging
from typing import Optional, Dict, Any, List
from io import BytesIO
from datetime import datetime

from engine import extract_text_from_pdf, evaluate_resume, generate_job_post
from resume_parser import extract_candidate_info
from database import db
from config import get_config
from task_queue import submit_evaluation_task, get_task_status
from llm_providers import get_provider

logger = logging.getLogger(__name__)


class ValidationError(Exception):
    """Raised when input validation fails."""
    pass


class ResourceNotFoundError(Exception):
    """Raised when a requested resource is not found."""
    pass


class BusinessLogicError(Exception):
    """Raised when business logic validation fails."""
    pass


# =============================================================================
# Candidate Service
# =============================================================================

class CandidateService:
    """
    Service for candidate-related business operations.

    This service handles:
    - Resume parsing and evaluation
    - Candidate CRUD operations
    - Interview question generation
    - Batch operations
    """

    @staticmethod
    def evaluate_resume_async(
        resume_file: BytesIO,
        job_description: str,
        filename: str
    ) -> Dict[str, Any]:
        """
        Evaluate a resume asynchronously using background task queue.

        Args:
            resume_file: Resume file as BytesIO
            job_description: Job description text
            filename: Original filename

        Returns:
            Dictionary with task_id for tracking

        Raises:
            ValidationError: If input validation fails
        """
        # Validate inputs
        if not job_description or not job_description.strip():
            raise ValidationError("Job description is required")

        if not filename.endswith('.pdf'):
            raise ValidationError("Only PDF files are supported")

        logger.info(f"Starting async evaluation for file: {filename}")

        # Extract text from PDF
        try:
            resume_text = extract_text_from_pdf(resume_file)
        except Exception as e:
            raise ValidationError(f"Failed to parse PDF: {str(e)}")

        if not resume_text or len(resume_text.strip()) < 50:
            raise ValidationError("Resume text is too short or empty")

        # Submit to background queue
        task_id = submit_evaluation_task(resume_text, job_description)

        # Store initial candidate record
        candidate_id = db.save_candidate(
            resume_filename=filename,
            resume_text=resume_text,
            job_description=job_description,
            evaluation={'status': 'processing', 'task_id': task_id},
            extracted_info={}
        )

        logger.info(f"Candidate {candidate_id} created with task {task_id}")

        return {
            'candidate_id': candidate_id,
            'task_id': task_id,
            'status': 'processing'
        }

    @staticmethod
    def evaluate_resume_sync(
        resume_file: BytesIO,
        job_description: str,
        filename: str
    ) -> Dict[str, Any]:
        """
        Evaluate a resume synchronously.

        Args:
            resume_file: Resume file as BytesIO
            job_description: Job description text
            filename: Original filename

        Returns:
            Dictionary with evaluation results

        Raises:
            ValidationError: If input validation fails
        """
        # Validate inputs
        if not job_description or not job_description.strip():
            raise ValidationError("Job description is required")

        if not filename.endswith('.pdf'):
            raise ValidationError("Only PDF files are supported")

        logger.info(f"Starting sync evaluation for file: {filename}")

        # Extract text from PDF
        try:
            resume_text = extract_text_from_pdf(resume_file)
        except Exception as e:
            raise ValidationError(f"Failed to parse PDF: {str(e)}")

        if not resume_text or len(resume_text.strip()) < 50:
            raise ValidationError("Resume text is too short or empty")

        # Extract candidate info
        extracted_info = extract_candidate_info(resume_text)

        # Evaluate resume
        evaluation = evaluate_resume(resume_text, job_description)

        # Convert to dict
        result = {
            'tier': evaluation.tier,
            'summary': evaluation.summary,
            'exact_match': {
                'score': evaluation.exact_match.score,
                'explanation': evaluation.exact_match.explanation
            },
            'similarity_match': {
                'score': evaluation.similarity_match.score,
                'explanation': evaluation.similarity_match.explanation
            },
            'achievement_impact': {
                'score': evaluation.achievement_impact.score,
                'explanation': evaluation.achievement_impact.explanation
            },
            'ownership': {
                'score': evaluation.ownership.score,
                'explanation': evaluation.ownership.explanation
            },
            'extracted_info': extracted_info
        }

        # Save to database
        candidate_id = db.save_candidate(
            resume_filename=filename,
            resume_text=resume_text,
            job_description=job_description,
            evaluation=result,
            extracted_info=extracted_info
        )

        result['candidate_id'] = candidate_id
        return result

    @staticmethod
    def get_candidate(candidate_id: int) -> Dict[str, Any]:
        """
        Get a candidate by ID.

        Args:
            candidate_id: Candidate database ID

        Returns:
            Candidate data dictionary

        Raises:
            ResourceNotFoundError: If candidate not found
        """
        candidate = db.get_candidate_by_id(candidate_id)

        if not candidate:
            raise ResourceNotFoundError(f"Candidate {candidate_id} not found")

        return candidate

    @staticmethod
    def list_candidates(
        limit: int = 50,
        offset: int = 0,
        tier: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        List candidates with optional filtering.

        Args:
            limit: Maximum number of results
            offset: Pagination offset
            tier: Filter by tier (optional)

        Returns:
            List of candidate dictionaries
        """
        if tier:
            return db.get_candidates_by_tier(tier)
        return db.get_all_candidates(limit=limit, offset=offset)

    @staticmethod
    def delete_candidate(candidate_id: int) -> bool:
        """
        Delete a candidate.

        Args:
            candidate_id: Candidate database ID

        Returns:
            True if deleted successfully

        Raises:
            ResourceNotFoundError: If candidate not found
        """
        candidate = db.get_candidate_by_id(candidate_id)
        if not candidate:
            raise ResourceNotFoundError(f"Candidate {candidate_id} not found")

        return db.delete_candidate(candidate_id)

    @staticmethod
    def generate_interview_questions(
        candidate_id: int,
        num_questions: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Generate AI-powered interview questions for a candidate.

        Args:
            candidate_id: Candidate database ID
            num_questions: Number of questions to generate

        Returns:
            List of question dictionaries

        Raises:
            ResourceNotFoundError: If candidate not found
        """
        candidate = db.get_candidate_by_id(candidate_id)
        if not candidate:
            raise ResourceNotFoundError(f"Candidate {candidate_id} not found")

        # Delete existing questions
        db.delete_interview_questions(candidate_id)

        # Generate questions using provider
        provider = get_provider()
        questions_list = provider.generate_interview_questions(
            candidate_profile=candidate,
            job_description=candidate.get('job_description', 'Not specified'),
            num_questions=num_questions
        )

        # Save questions to database
        saved_questions = []
        for q in questions_list:
            if isinstance(q, dict) and 'question' in q:
                category = q.get('category', 'General')
                question_id = db.save_interview_question(
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

        return saved_questions

    @staticmethod
    def get_interview_questions(candidate_id: int) -> List[Dict[str, Any]]:
        """
        Get interview questions for a candidate.

        Args:
            candidate_id: Candidate database ID

        Returns:
            List of question dictionaries
        """
        return db.get_interview_questions(candidate_id)


# =============================================================================
# Job Post Service
# =============================================================================

class JobPostService:
    """
    Service for job post-related business operations.

    This service handles:
    - Job post CRUD operations
    - AI-powered job post generation
    - Job post analytics
    """

    @staticmethod
    def create_job_post(
        title: str,
        description: str,
        location: Optional[str] = None,
        requirements: Optional[str] = None,
        status: str = 'active'
    ) -> int:
        """
        Create a new job post.

        Args:
            title: Job title
            description: Job description
            location: Job location (optional)
            requirements: Job requirements (optional)
            status: Post status (default: 'active')

        Returns:
            Job post ID

        Raises:
            ValidationError: If validation fails
        """
        if not title or not title.strip():
            raise ValidationError("Title is required")

        if not description or not description.strip():
            raise ValidationError("Description is required")

        job_id = db.save_job_post(
            title=title,
            description=description,
            location=location,
            requirements=requirements,
            status=status
        )

        logger.info(f"Created job post {job_id}: {title}")
        return job_id

    @staticmethod
    def generate_ai_job_post(
        title: str,
        location: Optional[str] = None,
        additional_info: Optional[str] = None
    ) -> Dict[str, str]:
        """
        Generate a job post using AI.

        Args:
            title: Job title
            location: Job location (optional)
            additional_info: Additional context (optional)

        Returns:
            Dictionary with 'description' and 'requirements'

        Raises:
            ValidationError: If validation fails
        """
        if not title or not title.strip():
            raise ValidationError("Title is required")

        logger.info(f"Generating AI job post for: {title}")

        generated = generate_job_post(
            title=title,
            location=location,
            additional_info=additional_info
        )

        return {
            'description': generated['description'],
            'requirements': generated['requirements']
        }

    @staticmethod
    def get_job_post(job_id: int) -> Dict[str, Any]:
        """
        Get a job post by ID.

        Args:
            job_id: Job post database ID

        Returns:
            Job post dictionary

        Raises:
            ResourceNotFoundError: If job post not found
        """
        job_post = db.get_job_post_by_id(job_id)

        if not job_post:
            raise ResourceNotFoundError(f"Job post {job_id} not found")

        return job_post

    @staticmethod
    def list_job_posts(
        limit: int = 50,
        offset: int = 0,
        status: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        List job posts with optional filtering.

        Args:
            limit: Maximum number of results
            offset: Pagination offset
            status: Filter by status (optional)

        Returns:
            List of job post dictionaries
        """
        return db.get_all_job_posts(status=status, limit=limit, offset=offset)

    @staticmethod
    def update_job_post(
        job_id: int,
        title: Optional[str] = None,
        description: Optional[str] = None,
        location: Optional[str] = None,
        requirements: Optional[str] = None,
        status: Optional[str] = None
    ) -> bool:
        """
        Update a job post.

        Args:
            job_id: Job post database ID
            title: New title (optional)
            description: New description (optional)
            location: New location (optional)
            requirements: New requirements (optional)
            status: New status (optional)

        Returns:
            True if updated successfully

        Raises:
            ResourceNotFoundError: If job post not found
        """
        job_post = db.get_job_post_by_id(job_id)
        if not job_post:
            raise ResourceNotFoundError(f"Job post {job_id} not found")

        return db.update_job_post(
            job_id=job_id,
            title=title,
            description=description,
            location=location,
            requirements=requirements,
            status=status
        )

    @staticmethod
    def delete_job_post(job_id: int) -> bool:
        """
        Delete a job post.

        Args:
            job_id: Job post database ID

        Returns:
            True if deleted successfully

        Raises:
            ResourceNotFoundError: If job post not found
        """
        job_post = db.get_job_post_by_id(job_id)
        if not job_post:
            raise ResourceNotFoundError(f"Job post {job_id} not found")

        return db.delete_job_post(job_id)


# =============================================================================
# Analytics Service
# =============================================================================

class AnalyticsService:
    """
    Service for analytics and insights.

    This service handles:
    - Candidate statistics
    - Skill gap analysis
    - Trend analysis
    """

    @staticmethod
    def get_overall_statistics() -> Dict[str, Any]:
        """
        Get overall system statistics.

        Returns:
            Dictionary with statistics
        """
        return db.get_statistics()

    @staticmethod
    def analyze_skill_gap(job_skills: List[str]) -> Dict[str, Any]:
        """
        Analyze skill gaps in the candidate pool.

        Args:
            job_skills: List of required skills

        Returns:
            Dictionary with gap analysis results

        Raises:
            ValidationError: If validation fails
        """
        if not job_skills or not isinstance(job_skills, list):
            raise ValidationError("job_skills must be a non-empty list")

        if len(job_skills) < 1:
            raise ValidationError("At least one skill is required")

        logger.info(f"Analyzing skill gap for {len(job_skills)} skills")

        cursor = db.conn.cursor()
        candidates = cursor.execute(
            "SELECT id, name, skills, tier FROM candidates WHERE skills IS NOT NULL",
        ).fetchall()

        if not candidates:
            return {
                'missing_skills': job_skills,
                'coverage_percentage': 0.0,
                'candidate_count': 0,
                'recommendations': [
                    'No candidates found in database. Start by uploading resumes.',
                ]
            }

        # Analyze skill coverage
        job_skills_lower = [s.lower().strip() for s in job_skills]
        found_skills = set()

        for candidate in candidates:
            candidate_skills = candidate[2].lower() if candidate[2] else ''
            for skill in job_skills_lower:
                if skill in candidate_skills:
                    found_skills.add(skill)

        missing_skills = [s for s in job_skills_lower if s not in found_skills]
        coverage_percentage = (len(found_skills) / len(job_skills_lower)) * 100

        return {
            'missing_skills': missing_skills,
            'coverage_percentage': round(coverage_percentage, 1),
            'candidate_count': len(candidates),
            'found_skills': list(found_skills),
        }


# =============================================================================
# Task Service
# =============================================================================

class TaskService:
    """
    Service for background task management.

    This service handles:
    - Task status checking
    - Task result retrieval
    """

    @staticmethod
    def get_task_status(task_id: str) -> Optional[Dict[str, Any]]:
        """
        Get the status of a background task.

        Args:
            task_id: Task ID to check

        Returns:
            Task status dictionary or None if not found
        """
        return get_task_status(task_id)

    @staticmethod
    def get_task_queue_statistics() -> Dict[str, Any]:
        """
        Get task queue statistics.

        Returns:
            Dictionary with queue statistics
        """
        from task_queue import get_task_queue
        queue = get_task_queue()
        return queue.get_statistics()
