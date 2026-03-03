"""
Evaluation Service - Business logic for resume evaluation operations.

This service handles all evaluation-related business rules, decoupling
the logic from API controllers.

Contributor: shubham21155102 - Service Layer Architecture
"""

from typing import Dict, Optional, Any
from dataclasses import dataclass
from io import BytesIO

from engine import extract_text_from_pdf, evaluate_resume
from resume_parser import extract_candidate_info
from database import db
from error_handlers import ValidationError, BusinessLogicError, FileProcessingError
from structured_logging import get_logger, LogContext

logger = get_logger(__name__)


@dataclass
class EvaluationInput:
    """Input data for resume evaluation"""
    resume_bytes: BytesIO
    resume_filename: str
    job_description: str

    def validate(self):
        """Validate evaluation input."""
        if not self.job_description or not self.job_description.strip():
            raise ValidationError("Job description is required")

        if not self.resume_bytes:
            raise ValidationError("Resume file is required")

        if not self.resume_filename.lower().endswith('.pdf'):
            raise ValidationError("Only PDF files are supported")

        # Check job description length
        if len(self.job_description) < 50:
            raise ValidationError(
                "Job description is too short. Please provide more details."
            )


@dataclass
class ResumeRewriteInput:
    """Input data for resume rewriting"""
    resume_text: str
    job_description: str
    job_title: str

    def validate(self):
        """Validate resume rewrite input."""
        if not self.resume_text or not self.resume_text.strip():
            raise ValidationError("Resume text is required")

        if not self.job_description or not self.job_description.strip():
            raise ValidationError("Job description is required")

        if not self.job_title or not self.job_title.strip():
            raise ValidationError("Job title is required")


class EvaluationService:
    """
    Service layer for evaluation operations.

    This class encapsulates all business logic related to resume evaluation,
    including validation, AI processing, and result storage.
    """

    def __init__(self):
        self.db = db

    def evaluate_candidate(
        self,
        evaluation_input: EvaluationInput,
        request_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Evaluate a candidate's resume against a job description.

        Args:
            evaluation_input: EvaluationInput with resume and job details
            request_id: Request tracking ID

        Returns:
            Dict with evaluation results and candidate ID

        Raises:
            ValidationError: If input validation fails
            FileProcessingError: If PDF processing fails
            BusinessLogicError: If evaluation fails
        """
        with LogContext(request_id=request_id, operation='evaluate_candidate'):
            try:
                # Validate input
                evaluation_input.validate()

                logger.info(
                    f"Evaluating resume: {evaluation_input.resume_filename}",
                    extra={
                        'filename': evaluation_input.resume_filename,
                        'job_description_length': len(evaluation_input.job_description)
                    }
                )

                # Extract text from PDF
                try:
                    resume_text = extract_text_from_pdf(evaluation_input.resume_bytes)
                    if not resume_text or len(resume_text) < 100:
                        raise FileProcessingError(
                            "Could not extract sufficient text from resume. "
                            "Please ensure the PDF contains readable text."
                        )
                except ValueError as e:
                    raise FileProcessingError(f"Failed to parse PDF: {str(e)}")

                logger.info("Resume text extracted successfully", extra={'text_length': len(resume_text)})

                # Extract candidate information
                logger.info("Extracting candidate information")
                extracted_info = extract_candidate_info(resume_text)
                logger.info(
                    "Candidate info extracted",
                    extra={
                        'name': extracted_info.get('name'),
                        'email': extracted_info.get('email')
                    }
                )

                # Evaluate resume
                logger.info("Running AI evaluation")
                evaluation = evaluate_resume(resume_text, evaluation_input.job_description)

                # Convert Pydantic model to dict
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
                candidate_id = self.db.save_candidate(
                    resume_filename=evaluation_input.resume_filename,
                    resume_text=resume_text,
                    job_description=evaluation_input.job_description,
                    evaluation=result,
                    extracted_info=extracted_info
                )

                if candidate_id:
                    result['candidate_id'] = candidate_id
                    logger.info(f"Candidate saved with ID: {candidate_id}")
                else:
                    logger.warning("Failed to save candidate to database")

                logger.info(
                    "Evaluation completed successfully",
                    extra={'tier': evaluation.tier, 'candidate_id': candidate_id}
                )

                return result

            except (ValidationError, FileProcessingError):
                raise
            except Exception as e:
                logger.error("Failed to evaluate candidate", exc_info=True)
                raise BusinessLogicError(f"Failed to evaluate candidate: {str(e)}")

    def rewrite_resume(
        self,
        rewrite_input: ResumeRewriteInput,
        request_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Rewrite a resume to better match a job description.

        Args:
            rewrite_input: ResumeRewriteInput with resume and job details
            request_id: Request tracking ID

        Returns:
            Dict with improved resume content

        Raises:
            ValidationError: If input validation fails
            BusinessLogicError: If rewriting fails
        """
        with LogContext(request_id=request_id, operation='rewrite_resume'):
            try:
                # Validate input
                rewrite_input.validate()

                logger.info(
                    f"Rewriting resume for job: {rewrite_input.job_title}",
                    extra={
                        'job_title': rewrite_input.job_title,
                        'resume_length': len(rewrite_input.resume_text)
                    }
                )

                # Import here to avoid circular dependency
                from llm_providers import get_provider

                provider = get_provider()
                result = provider.rewrite_resume_for_job(
                    resume_text=rewrite_input.resume_text,
                    job_description=rewrite_input.job_description,
                    job_title=rewrite_input.job_title
                )

                logger.info("Resume rewrite completed successfully")

                return {
                    'improved_summary': result.get('improved_summary', ''),
                    'suggested_bullets': result.get('suggested_bullets', []),
                    'skills_to_highlight': result.get('skills_to_highlight', []),
                    'keywords_to_add': result.get('keywords_to_add', []),
                    'cover_letter_suggestion': result.get('cover_letter_suggestion', '')
                }

            except ValidationError:
                raise
            except Exception as e:
                logger.error("Failed to rewrite resume", exc_info=True)
                raise BusinessLogicError(f"Failed to rewrite resume: {str(e)}")


# Singleton instance
evaluation_service = EvaluationService()
