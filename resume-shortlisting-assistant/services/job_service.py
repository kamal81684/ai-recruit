"""
Job Service - Business logic for job post operations.

This service handles all job-related business rules, decoupling
the logic from API controllers.

Contributor: shubham21155102 - Service Layer Architecture
"""

from typing import List, Dict, Optional, Any
from dataclasses import dataclass

from database import db
from error_handlers import NotFoundError, ValidationError, BusinessLogicError
from structured_logging import get_logger, LogContext

logger = get_logger(__name__)


@dataclass
class JobPostInput:
    """Input data for creating/updating job posts"""
    title: str
    description: str
    location: Optional[str] = None
    requirements: Optional[str] = None
    status: str = 'active'

    def validate(self):
        """Validate job post input."""
        if not self.title or not self.title.strip():
            raise ValidationError("Job title is required")

        if not self.description or not self.description.strip():
            raise ValidationError("Job description is required")

        # Validate status
        valid_statuses = ['active', 'inactive', 'closed', 'draft']
        if self.status not in valid_statuses:
            raise ValidationError(
                f"Invalid status. Must be one of: {', '.join(valid_statuses)}"
            )

        # Check title length
        if len(self.title) > 255:
            raise ValidationError("Job title must be 255 characters or less")


class JobService:
    """
    Service layer for job post operations.

    This class encapsulates all business logic related to job posts,
    including validation, status management, and AI-powered features.
    """

    def __init__(self):
        self.db = db

    def create_job(
        self,
        job_input: JobPostInput,
        request_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a new job post.

        Args:
            job_input: JobPostInput with job details
            request_id: Request tracking ID

        Returns:
            Dict with created job data and ID

        Raises:
            ValidationError: If input validation fails
            BusinessLogicError: If creation fails
        """
        with LogContext(request_id=request_id, operation='create_job'):
            try:
                # Validate input
                job_input.validate()

                logger.info(
                    f"Creating job post: {job_input.title}",
                    extra={'title': job_input.title, 'location': job_input.location}
                )

                # Save to database
                job_id = self.db.save_job_post(
                    title=job_input.title,
                    description=job_input.description,
                    location=job_input.location,
                    requirements=job_input.requirements,
                    status=job_input.status
                )

                if not job_id:
                    raise BusinessLogicError("Failed to create job post")

                logger.info(f"Job post created with ID: {job_id}")

                return {
                    'job_id': job_id,
                    'title': job_input.title,
                    'location': job_input.location,
                    'status': job_input.status
                }

            except ValidationError:
                raise
            except Exception as e:
                logger.error("Failed to create job post", exc_info=True)
                raise BusinessLogicError(f"Failed to create job post: {str(e)}")

    def get_jobs(
        self,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
        request_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get job posts with optional filtering.

        Args:
            status: Filter by status
            limit: Number of results
            offset: Pagination offset
            request_id: Request tracking ID

        Returns:
            Dict with job posts list and count
        """
        with LogContext(request_id=request_id, operation='get_jobs'):
            try:
                logger.info(
                    "Fetching job posts",
                    extra={'status': status, 'limit': limit, 'offset': offset}
                )

                job_posts = self.db.get_all_job_posts(
                    status=status,
                    limit=limit,
                    offset=offset
                )

                logger.info(f"Retrieved {len(job_posts)} job posts")

                return {
                    'job_posts': job_posts,
                    'count': len(job_posts)
                }

            except Exception as e:
                logger.error("Failed to fetch job posts", exc_info=True)
                raise BusinessLogicError(f"Failed to fetch job posts: {str(e)}")

    def get_job_by_id(
        self,
        job_id: int,
        request_id: Optional[str] = None
    ) -> Dict:
        """
        Get a specific job post by ID.

        Args:
            job_id: Job post ID
            request_id: Request tracking ID

        Returns:
            Job post data

        Raises:
            NotFoundError: If job not found
        """
        with LogContext(request_id=request_id, operation='get_job'):
            try:
                logger.info(f"Fetching job post {job_id}")

                job_post = self.db.get_job_post_by_id(job_id)

                if not job_post:
                    logger.warning(f"Job post {job_id} not found")
                    raise NotFoundError(f"Job post {job_id} not found")

                logger.info(f"Job post {job_id} retrieved successfully")
                return job_post

            except NotFoundError:
                raise
            except Exception as e:
                logger.error(f"Failed to fetch job post {job_id}", exc_info=True)
                raise BusinessLogicError(f"Failed to fetch job post: {str(e)}")

    def update_job(
        self,
        job_id: int,
        job_input: JobPostInput,
        request_id: Optional[str] = None
    ) -> bool:
        """
        Update a job post.

        Args:
            job_id: Job post ID
            job_input: JobPostInput with updated details
            request_id: Request tracking ID

        Returns:
            True if successful

        Raises:
            NotFoundError: If job not found
            ValidationError: If input validation fails
        """
        with LogContext(request_id=request_id, operation='update_job'):
            try:
                # Validate input
                job_input.validate()

                # Verify job exists
                job_post = self.db.get_job_post_by_id(job_id)
                if not job_post:
                    raise NotFoundError(f"Job post {job_id} not found")

                logger.info(f"Updating job post {job_id}")

                success = self.db.update_job_post(
                    job_id=job_id,
                    title=job_input.title,
                    description=job_input.description,
                    location=job_input.location,
                    requirements=job_input.requirements,
                    status=job_input.status
                )

                if success:
                    logger.info(f"Job post {job_id} updated successfully")
                else:
                    logger.warning(f"No changes made to job post {job_id}")

                return success

            except (NotFoundError, ValidationError):
                raise
            except Exception as e:
                logger.error(f"Failed to update job post {job_id}", exc_info=True)
                raise BusinessLogicError(f"Failed to update job post: {str(e)}")

    def delete_job(
        self,
        job_id: int,
        request_id: Optional[str] = None
    ) -> bool:
        """
        Delete a job post by ID.

        Args:
            job_id: Job post ID
            request_id: Request tracking ID

        Returns:
            True if successful

        Raises:
            NotFoundError: If job not found
        """
        with LogContext(request_id=request_id, operation='delete_job'):
            try:
                # Verify job exists
                job_post = self.db.get_job_post_by_id(job_id)
                if not job_post:
                    raise NotFoundError(f"Job post {job_id} not found")

                logger.info(f"Deleting job post {job_id}")

                success = self.db.delete_job_post(job_id)

                if success:
                    logger.info(f"Job post {job_id} deleted successfully")
                else:
                    logger.error(f"Failed to delete job post {job_id}")

                return success

            except NotFoundError:
                raise
            except Exception as e:
                logger.error(f"Failed to delete job post {job_id}", exc_info=True)
                raise BusinessLogicError(f"Failed to delete job post: {str(e)}")

    def generate_ai_job_post(
        self,
        title: str,
        location: Optional[str] = None,
        additional_info: Optional[str] = None,
        request_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate a job post using AI.

        Args:
            title: Job title
            location: Job location (optional)
            additional_info: Additional context (optional)
            request_id: Request tracking ID

        Returns:
            Dict with generated description and requirements

        Raises:
            BusinessLogicError: If generation fails
        """
        with LogContext(request_id=request_id, operation='generate_ai_job'):
            try:
                from engine import generate_job_post

                if not title or not title.strip():
                    raise ValidationError("Job title is required")

                logger.info(
                    f"Generating AI job post for: {title}",
                    extra={'title': title, 'location': location}
                )

                generated = generate_job_post(
                    title=title,
                    location=location,
                    additional_info=additional_info
                )

                logger.info("AI job post generated successfully")

                return {
                    'description': generated['description'],
                    'requirements': generated['requirements']
                }

            except ValidationError:
                raise
            except Exception as e:
                logger.error("Failed to generate AI job post", exc_info=True)
                raise BusinessLogicError(f"Failed to generate job post: {str(e)}")


# Singleton instance
job_service = JobService()
