"""
AI-Generated Candidate Summaries Module.

This module provides AI-powered candidate summaries that help recruiters
quickly understand candidate qualifications without reading full resumes.

Features:
- Executive summaries highlighting key qualifications
- Strengths and concerns identification
- Recommended next steps for recruitment
- Confidence scoring for reliability

Contributor: shubham21155102 - AI-Powered Summaries
"""

from typing import List, Dict, Optional, Any
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum

from config import get_config
from llm_providers import get_provider
from structured_logging import get_logger, LogContext

logger = get_logger(__name__)


class SummaryStrength(Enum):
    """Classification of summary strength."""
    EXCELLENT = "excellent"
    GOOD = "good"
    ADEQUATE = "adequate"
    LIMITED = "limited"


@dataclass
class CandidateSummary:
    """
    AI-generated summary of a candidate's qualifications.

    Attributes:
        candidate_id: Database ID of the candidate
        executive_summary: 2-3 sentence overview of the candidate
        key_strengths: List of identified strengths (3-5 items)
        potential_concerns: List of red flags or areas of concern
        recommended_next_steps: Suggested recruitment actions
        confidence_score: 0-1 score indicating summary reliability
        fit_assessment: Overall fit assessment (excellent/good/adequate/limited)
        experience_summary: Summary of years and type of experience
        education_highlights: Key educational qualifications
        generated_at: Timestamp of summary generation
    """
    candidate_id: int
    executive_summary: str
    key_strengths: List[str]
    potential_concerns: List[str]
    recommended_next_steps: List[str]
    confidence_score: float
    fit_assessment: SummaryStrength
    experience_summary: str
    education_highlights: str
    generated_at: str

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary, handling enums."""
        data = asdict(self)
        data['fit_assessment'] = self.fit_assessment.value
        return data


class CandidateSummaryGenerator:
    """
    Generates AI-powered summaries for candidates.

    Uses LLM providers to create concise, actionable summaries
    that help recruiters make faster decisions.
    """

    def __init__(self):
        """Initialize the summary generator."""
        self.config = get_config()
        self.provider = get_provider()

    def generate_summary(
        self,
        candidate: Dict[str, Any],
        job_description: Optional[str] = None,
        request_id: Optional[str] = None
    ) -> CandidateSummary:
        """
        Generate an AI summary for a candidate.

        Args:
            candidate: Candidate data dictionary
            job_description: Optional job description for context
            request_id: Request tracking ID

        Returns:
            CandidateSummary with generated content

        Raises:
            ValueError: If candidate data is insufficient
        """
        with LogContext(request_id=request_id, operation='generate_summary'):
            try:
                candidate_id = candidate.get('id')
                if not candidate_id:
                    raise ValueError("Candidate ID is required")

                logger.info(f"Generating summary for candidate {candidate_id}")

                # Build context for summary generation
                context = self._build_summary_context(candidate, job_description)

                # Generate summary using LLM
                prompt = self._build_summary_prompt(context)
                response = self._call_llm_for_summary(prompt)

                # Parse response into structured summary
                summary = self._parse_summary_response(candidate_id, response)

                logger.info(
                    f"Summary generated for candidate {candidate_id}",
                    extra={
                        'confidence_score': summary.confidence_score,
                        'fit_assessment': summary.fit_assessment.value
                    }
                )

                return summary

            except Exception as e:
                logger.error(f"Failed to generate summary for candidate: {e}", exc_info=True)
                raise

    def _build_summary_context(
        self,
        candidate: Dict[str, Any],
        job_description: Optional[str]
    ) -> Dict[str, Any]:
        """Build context dictionary for summary generation."""
        return {
            'candidate_name': candidate.get('name', 'Unknown'),
            'email': candidate.get('email'),
            'phone': candidate.get('phone'),
            'location': candidate.get('location'),
            'current_role': candidate.get('current_role'),
            'experience_years': candidate.get('experience_years'),
            'skills': candidate.get('skills'),
            'education': candidate.get('education'),
            'tier': candidate.get('tier'),
            'summary': candidate.get('summary'),
            'scores': {
                'exact_match': candidate.get('exact_match_score'),
                'similarity_match': candidate.get('similarity_match_score'),
                'achievement_impact': candidate.get('achievement_impact_score'),
                'ownership': candidate.get('ownership_score'),
            },
            'job_description': job_description,
            'resume_text': candidate.get('resume_text', '')[:1000],  # First 1000 chars
        }

    def _build_summary_prompt(self, context: Dict[str, Any]) -> str:
        """Build the prompt for LLM summary generation."""
        prompt = f"""You are an expert recruiter providing a concise candidate summary.

CANDIDATE INFORMATION:
- Name: {context['candidate_name']}
- Current Role: {context['current_role'] or 'Not specified'}
- Location: {context['location'] or 'Not specified'}
- Experience: {context['experience_years'] or 'Not specified'} years
- Tier: {context['tier'] or 'Not assessed'}

SKILLS:
{context['skills'] or 'Not specified'}

EDUCATION:
{context['education'] or 'Not specified'}

EXISTING EVALUATION SUMMARY:
{context['summary'] or 'No previous summary'}

MATCH SCORES (out of 100):
- Exact Match: {context['scores']['exact_match'] or 'N/A'}
- Similarity Match: {context['scores']['similarity_match'] or 'N/A'}
- Achievement Impact: {context['scores']['achievement_impact'] or 'N/A'}
- Ownership: {context['scores']['ownership'] or 'N/A'}

JOB DESCRIPTION (for context):
{context['job_description'] or 'Not provided'}

TASK: Provide a JSON-formatted summary with the following structure:
{{
    "executive_summary": "2-3 sentences capturing who this candidate is and their overall fit",
    "key_strengths": ["3-5 specific strengths based on their skills, experience, and scores"],
    "potential_concerns": ["2-3 potential red flags or areas requiring clarification"],
    "recommended_next_steps": ["2-3 specific actions for the recruiter (e.g., 'Schedule technical screen', 'Verify experience claims')"],
    "confidence_score": 0.0-1.0 indicating how confident you are in this assessment,
    "experience_summary": "1-2 sentences summarizing their professional experience",
    "education_highlights": "1-2 sentences highlighting key education"
}}

Focus on being concise, specific, and actionable. The confidence score should be lower if resume information is sparse.
"""

        return prompt

    def _call_llm_for_summary(self, prompt: str) -> str:
        """Call the LLM provider to generate summary."""
        try:
            # Use the provider's raw LLM call capability
            # This is a simplified approach - in production, you might want
            # to add a dedicated method to the provider
            import json

            # Try to use the configured provider
            from llm_providers import get_provider
            provider = get_provider()

            # For now, we'll use a direct OpenAI call if available
            if hasattr(provider, 'client') and provider.client:
                response = provider.client.chat.completions.create(
                    model=provider.model,
                    messages=[
                        {"role": "system", "content": "You are an expert recruiter providing candidate summaries. Always respond with valid JSON."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.3,
                    response_format={"type": "json_object"}
                )
                return response.choices[0].message.content
            else:
                # Fallback: generate a basic summary
                return self._generate_fallback_summary(prompt)

        except Exception as e:
            logger.warning(f"LLM call failed, using fallback: {e}")
            return self._generate_fallback_summary(prompt)

    def _generate_fallback_summary(self, prompt: str) -> str:
        """Generate a basic summary when LLM is unavailable."""
        # Extract basic info from prompt
        import re

        # Try to extract name
        name_match = re.search(r'- Name: (.+)', prompt)
        name = name_match.group(1) if name_match else "Candidate"

        # Try to extract tier
        tier_match = re.search(r'- Tier: (.+)', prompt)
        tier = tier_match.group(1) if tier_match else "Not assessed"

        # Generate basic summary based on tier
        if "Tier A" in tier or "A" in tier:
            fit = "excellent"
            summary = f"{name} is a strong candidate with excellent qualifications and high match scores."
            strengths = ["High match scores across all dimensions", "Strong alignment with requirements"]
            confidence = 0.8
        elif "Tier B" in tier or "B" in tier:
            fit = "good"
            summary = f"{name} shows good potential with solid qualifications and reasonable match scores."
            strengths = ["Good overall match", "Relevant skills and experience"]
            confidence = 0.7
        else:
            fit = "adequate"
            summary = f"{name} may have some relevant qualifications but requires further review."
            strengths = ["Some relevant skills present"]
            confidence = 0.5

        import json
        return json.dumps({
            "executive_summary": summary,
            "key_strengths": strengths,
            "potential_concerns": ["Review full resume for detailed assessment"],
            "recommended_next_steps": ["Review complete resume", "Conduct phone screen"],
            "confidence_score": confidence,
            "experience_summary": "Experience details require full resume review",
            "education_highlights": "Education details require full resume review"
        })

    def _parse_summary_response(
        self,
        candidate_id: int,
        response: str
    ) -> CandidateSummary:
        """Parse LLM response into CandidateSummary object."""
        try:
            import json

            data = json.loads(response)

            # Determine fit assessment from confidence and content
            confidence = float(data.get('confidence_score', 0.5))
            if confidence >= 0.8:
                fit = SummaryStrength.EXCELLENT
            elif confidence >= 0.6:
                fit = SummaryStrength.GOOD
            elif confidence >= 0.4:
                fit = SummaryStrength.ADEQUATE
            else:
                fit = SummaryStrength.LIMITED

            return CandidateSummary(
                candidate_id=candidate_id,
                executive_summary=data.get('executive_summary', 'Summary not available'),
                key_strengths=data.get('key_strengths', []),
                potential_concerns=data.get('potential_concerns', []),
                recommended_next_steps=data.get('recommended_next_steps', []),
                confidence_score=min(max(confidence, 0.0), 1.0),
                fit_assessment=fit,
                experience_summary=data.get('experience_summary', ''),
                education_highlights=data.get('education_highlights', ''),
                generated_at=datetime.now().isoformat()
            )

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse summary JSON: {e}")
            # Return minimal summary
            return CandidateSummary(
                candidate_id=candidate_id,
                executive_summary="AI summary generation failed. Please review resume directly.",
                key_strengths=[],
                potential_concerns=["Summary generation failed"],
                recommended_next_steps=["Review resume manually"],
                confidence_score=0.0,
                fit_assessment=SummaryStrength.LIMITED,
                experience_summary="Not available",
                education_highlights="Not available",
                generated_at=datetime.now().isoformat()
            )


def generate_candidate_summary(
    candidate: Dict[str, Any],
    job_description: Optional[str] = None,
    request_id: Optional[str] = None
) -> CandidateSummary:
    """
    Convenience function to generate a candidate summary.

    Args:
        candidate: Candidate data dictionary
        job_description: Optional job description for context
        request_id: Request tracking ID

    Returns:
        CandidateSummary with generated content
    """
    generator = CandidateSummaryGenerator()
    return generator.generate_summary(candidate, job_description, request_id)


# Export public API
__all__ = [
    'CandidateSummary',
    'SummaryStrength',
    'CandidateSummaryGenerator',
    'generate_candidate_summary',
]
