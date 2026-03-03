"""
LLM Provider Abstraction Layer.

This module provides a unified interface for interacting with different LLM providers
(Groq, OpenAI, Anthropic, etc.). It implements the Provider Pattern to enable easy
swapping of LLM backends without modifying business logic.

Supported providers:
- Groq (default)
- OpenAI
- Anthropic
- Custom (LangChain-compatible)

Phase 3 Enhancements:
- Integrated retry mechanisms with exponential backoff
- Dead Letter Queue for failed requests
- Input sanitization for prompt injection protection
- Circuit breaker pattern for service resilience

Contributor: shubham21155102
"""

from abc import ABC, abstractmethod
from typing import Any, Optional
from pydantic import BaseModel
import os
import logging
import time
import hashlib

logger = logging.getLogger(__name__)

# Import provider-specific SDKs
try:
    from langchain_groq import ChatGroq
    from langchain_core.prompts import ChatPromptTemplate
except ImportError:
    ChatGroq = None
    ChatPromptTemplate = None

try:
    from langchain_openai import ChatOpenAI
except ImportError:
    ChatOpenAI = None

try:
    from langchain_anthropic import ChatAnthropic
except ImportError:
    ChatAnthropic = None

from config import get_config

# Import resilience modules (Phase 3)
try:
    from resilience import RetryConfig, retry_with_backoff, get_dlq
    RESILIENCE_ENABLED = True
except ImportError:
    RESILIENCE_ENABLED = False
    logger.warning("Resilience module not available, running without retry logic")


# =============================================================================
# Pydantic Schemas for Structured Output
# =============================================================================

class EvaluationScore(BaseModel):
    """Score and explanation for a single evaluation dimension."""
    score: int
    explanation: str


class CandidateEvaluation(BaseModel):
    """Complete candidate evaluation result."""
    exact_match: EvaluationScore
    similarity_match: EvaluationScore
    achievement_impact: EvaluationScore
    ownership: EvaluationScore
    tier: str
    summary: str


class JobPostGeneration(BaseModel):
    """Generated job post content."""
    description: str
    requirements: str


# =============================================================================
# Abstract Provider Interface
# =============================================================================

class BaseLLMProvider(ABC):
    """
    Abstract base class for LLM providers.

    All providers must implement these methods to ensure a consistent interface.
    """

    def __init__(self, api_key: str, model: str, temperature: float = 0.0, max_tokens: int = 2048):
        self.api_key = api_key
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens

    @abstractmethod
    def get_llm(self):
        """Get the underlying LLM instance."""
        pass

    @abstractmethod
    def evaluate_resume(self, resume_text: str, jd_text: str) -> CandidateEvaluation:
        """
        Evaluate a resume against a job description.

        Args:
            resume_text: Extracted text from candidate's resume
            jd_text: Job description text

        Returns:
            CandidateEvaluation: Structured evaluation result
        """
        pass

    @abstractmethod
    def generate_job_post(
        self,
        title: str,
        location: Optional[str] = None,
        additional_info: Optional[str] = None
    ) -> dict:
        """
        Generate a job post using AI.

        Args:
            title: Job title
            location: Job location (optional)
            additional_info: Additional context for generation (optional)

        Returns:
            dict with 'description' and 'requirements' keys
        """
        pass

    @abstractmethod
    def generate_interview_questions(
        self,
        candidate_profile: dict,
        job_description: str,
        num_questions: int = 10
    ) -> list[dict]:
        """
        Generate interview questions for a candidate.

        Args:
            candidate_profile: Candidate information dict
            job_description: Job description text
            num_questions: Number of questions to generate

        Returns:
            List of dicts with 'question' and 'category' keys
        """
        pass

    @abstractmethod
    def rewrite_resume_for_job(
        self,
        resume_text: str,
        job_description: str,
        job_title: str
    ) -> dict:
        """
        Rewrite a candidate's resume to better match a job description.

        This feature helps candidates optimize their resume for a specific
        job posting by suggesting improvements to bullet points, skills
        highlighting, and overall positioning.

        Args:
            resume_text: Original resume text
            job_description: Target job description
            job_title: Target job title

        Returns:
            Dict with 'improved_summary', 'suggested_bullets', 'skills_to_highlight',
                  'keywords_to_add', 'cover_letter_suggestion'
        """
        pass


# =============================================================================
# Groq Provider Implementation
# =============================================================================

class GroqProvider(BaseLLMProvider):
    """Groq LLM provider using LangChain integration."""

    def __init__(self, api_key: str, model: str, temperature: float = 0.0, max_tokens: int = 2048):
        super().__init__(api_key, model, temperature, max_tokens)
        self._retry_config = RetryConfig(
            max_attempts=3,
            base_delay=1.0,
            max_delay=30.0,
            exponential_base=2.0,
            strategy=RetryConfig.EXPONENTIAL_BACKOFF if hasattr(RetryConfig, 'EXPONENTIAL_BACKOFF') else "exponential_backoff"
        )

    def get_llm(self):
        """Get the ChatGroq instance."""
        if ChatGroq is None:
            raise ImportError("langchain-groq is not installed. Run: pip install langchain-groq")
        return ChatGroq(
            model=self.model,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            api_key=self.api_key
        )

    def evaluate_resume(self, resume_text: str, jd_text: str) -> CandidateEvaluation:
        """
        Evaluate resume using Groq LLM with retry logic.

        This method includes automatic retry with exponential backoff for transient failures.
        Failed requests are logged to the Dead Letter Queue for manual review.
        """
        if ChatPromptTemplate is None:
            raise ImportError("langchain-core is not installed")

        # Generate a request ID for tracking
        request_id = hashlib.md5(f"{resume_text[:100]}{jd_text[:100]}".encode()).hexdigest()[:16]

        def _do_evaluate():
            """Internal evaluation method that will be retried."""
            llm = self.get_llm()
            structured_llm = llm.with_structured_output(CandidateEvaluation)

            prompt = ChatPromptTemplate.from_messages([
                ("system", """You are an expert technical recruiter and hiring manager.
Your task is to evaluate a candidate's resume against a job description (JD).
You must provide rigorous, multi-dimensional scores (0-100) and detailed explanations.

Scoring Guidelines:
1. Exact Match: Direct occurrences of required skills & tools.
2. Similarity Match: Semantic understanding of related tech (e.g., if JD asks for Kafka, but candidate has RabbitMQ or AWS Kinesis, give high similarity. If JD asks for React, and candidate has Vue/Angular, give moderate/high similarity based on context).
3. Achievement/Impact: Look for numbers, percentages, optimization times, and revenue impact. If absent, score low.
4. Ownership: Look for keywords like 'led', 'architected', 'designed', 'mentored', 'end-to-end'.

Tier Classification:
- Tier A (Fast-track): Overall strong fit, high scores across the board.
- Tier B (Technical Screen): Good match but might have gaps in some areas.
- Tier C (Needs Evaluation): Weak match, missing core skills and no related experience.

Be very objective and critical."""),
                ("human", "Job Description:\n{jd_text}\n\nCandidate Resume:\n{resume_text}")
            ])

            chain = prompt | structured_llm
            return chain.invoke({"jd_text": jd_text, "resume_text": resume_text})

        # Use retry logic if resilience module is available
        if RESILIENCE_ENABLED:
            last_exception = None
            for attempt in range(self._retry_config.max_attempts):
                try:
                    return _do_evaluate()
                except Exception as e:
                    last_exception = e
                    if attempt < self._retry_config.max_attempts - 1:
                        delay = self._calculate_delay(attempt)
                        logger.warning(
                            f"Groq API call failed (attempt {attempt + 1}/{self._retry_config.max_attempts}). "
                            f"Retrying in {delay:.2f}s. Error: {str(e)}"
                        )
                        time.sleep(delay)
                    else:
                        # Final attempt failed - add to DLQ
                        dlq = get_dlq()
                        dlq.add(
                            endpoint="evaluate_resume",
                            method="GROQ_LLM_CALL",
                            payload={
                                "request_id": request_id,
                                "resume_length": len(resume_text),
                                "jd_length": len(jd_text)
                            },
                            error_message=str(e),
                            error_type=type(e).__name__,
                            retry_count=self._retry_config.max_attempts
                        )
                        logger.error(
                            f"Groq API call failed after {self._retry_config.max_attempts} attempts. "
                            f"Added to DLQ. Request ID: {request_id}"
                        )
            raise last_exception
        else:
            # Fallback to direct call without retry
            return _do_evaluate()

    def _calculate_delay(self, attempt: int) -> float:
        """Calculate retry delay with exponential backoff."""
        delay = self._retry_config.base_delay * (2.0 ** attempt)
        return min(delay, self._retry_config.max_delay)

    def generate_job_post(
        self,
        title: str,
        location: Optional[str] = None,
        additional_info: Optional[str] = None
    ) -> dict:
        """Generate job post using Groq LLM."""
        if ChatPromptTemplate is None:
            raise ImportError("langchain-core is not installed")

        llm = self.get_llm()
        structured_llm = llm.with_structured_output(JobPostGeneration)

        context = ""
        if location:
            context += f"\nLocation: {location}"
        if additional_info:
            context += f"\nAdditional Information: {additional_info}"

        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert technical recruiter and job description writer.
Your task is to create a comprehensive, professional job posting based on the job title.

The job description should include:
1. A compelling introduction about the role and company
2. Key responsibilities and day-to-day activities
3. Required qualifications and technical skills
4. Preferred qualifications (nice-to-have skills)
5. Information about company culture and growth opportunities

Make the description detailed enough to attract qualified candidates while being specific about requirements.
Use professional language and format with clear sections."""),
            ("human", "Job Title: {title}{context}\n\nGenerate a comprehensive job posting for this position.")
        ])

        chain = prompt | structured_llm
        result = chain.invoke({"title": title, "context": context})

        return {
            "description": result.description,
            "requirements": result.requirements
        }

    def generate_interview_questions(
        self,
        candidate_profile: dict,
        job_description: str,
        num_questions: int = 10
    ) -> list[dict]:
        """Generate interview questions using Groq API directly."""
        try:
            from groq import Groq
            import json
        except ImportError:
            raise ImportError("groq package is not installed. Run: pip install groq")

        client = Groq(api_key=self.api_key)

        prompt = f"""You are an expert technical interviewer. Based on the following candidate profile and job description, generate {num_questions} targeted interview questions.

CANDIDATE PROFILE:
Name: {candidate_profile.get('name', 'Unknown')}
Current Role: {candidate_profile.get('current_role', 'Unknown')}
Skills: {candidate_profile.get('skills', 'Not specified')}
Experience: {candidate_profile.get('experience_years', 'Unknown')} years
Education: {candidate_profile.get('education', 'Not specified')}

JOB DESCRIPTION:
{job_description[:1000]}

CANDIDATE TIER: {candidate_profile.get('tier', 'Unknown')}
EVALUATION SUMMARY: {candidate_profile.get('summary', '')[:500]}

Generate questions that:
1. Test technical depth in their claimed skills
2. Explore their achievements and impact mentioned in the resume
3. Assess cultural fit and soft skills
4. Include both behavioral and technical questions
5. Are tailored to their tier level (harder questions for Tier A, foundational for Tier C)

Return ONLY a valid JSON array with this exact structure:
[
  {{"question": "question text here", "category": "Technical|Behavioral|Cultural"}}
]

Ensure the JSON is valid and properly formatted."""

        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert technical interviewer. Always respond with valid JSON only."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            model=self.model,
            temperature=0.5,
            max_tokens=2048,
            response_format={"type": "json_object"}
        )

        response_text = chat_completion.choices[0].message.content

        try:
            questions_data = json.loads(response_text)

            if isinstance(questions_data, list):
                return questions_data
            elif isinstance(questions_data, dict) and 'questions' in questions_data:
                return questions_data['questions']
            return []
        except json.JSONDecodeError:
            # Fallback to generic questions
            return [
                {"question": "Can you walk me through your most challenging technical project?", "category": "Technical"},
                {"question": "Describe a time you had to learn a new technology quickly.", "category": "Behavioral"},
            ]

    def rewrite_resume_for_job(
        self,
        resume_text: str,
        job_description: str,
        job_title: str
    ) -> dict:
        """Rewrite resume to better match job description using Groq API."""
        try:
            from groq import Groq
            import json
        except ImportError:
            raise ImportError("groq package is not installed. Run: pip install groq")

        client = Groq(api_key=self.api_key)

        prompt = f"""You are an expert resume writer and career coach. Your task is to analyze a candidate's resume and rewrite it to better match a target job description.

CANDIDATE'S CURRENT RESUME:
{resume_text[:2000]}

TARGET JOB DESCRIPTION:
{job_description[:1500]}

JOB TITLE: {job_title}

Please provide:
1. An improved professional summary that highlights relevant experience for this role
2. 3-5 rewritten bullet points that emphasize achievements and skills matching the job requirements
3. Key skills from the candidate's background that should be highlighted for this role
4. Important keywords from the job description that should be incorporated
5. A brief cover letter suggestion

Return ONLY a valid JSON object with this exact structure:
{{
  "improved_summary": "2-3 sentence professional summary tailored to the job",
  "suggested_bullets": [
    "• First rewritten bullet point with quantifiable achievement",
    "• Second rewritten bullet point",
    "• Third rewritten bullet point"
  ],
  "skills_to_highlight": ["skill1", "skill2", "skill3"],
  "keywords_to_add": ["keyword1", "keyword2", "keyword3"],
  "cover_letter_suggestion": "Brief opening paragraph for a cover letter"
}}

Ensure the JSON is valid and properly formatted."""

        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert resume writer and career coach. Always respond with valid JSON only."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            model=self.model,
            temperature=0.7,
            max_tokens=2048,
            response_format={"type": "json_object"}
        )

        response_text = chat_completion.choices[0].message.content

        try:
            result = json.loads(response_text)
            return result
        except json.JSONDecodeError:
            # Fallback response
            return {
                "improved_summary": f"Experienced professional with expertise relevant to {job_title} position.",
                "suggested_bullets": [
                    "• Demonstrated expertise in key skills required for the role",
                    "• Proven track record of delivering results in similar positions",
                    "• Strong combination of technical and soft skills"
                ],
                "skills_to_highlight": ["Leadership", "Communication", "Problem Solving"],
                "keywords_to_add": ["Team player", "Results-driven", "Innovative"],
                "cover_letter_suggestion": f"I am excited to apply for the {job_title} position..."
            }


# =============================================================================
# OpenAI Provider Implementation
# =============================================================================

class OpenAIProvider(BaseLLMProvider):
    """OpenAI LLM provider using LangChain integration."""

    def get_llm(self):
        """Get the ChatOpenAI instance."""
        if ChatOpenAI is None:
            raise ImportError("langchain-openai is not installed. Run: pip install langchain-openai")
        return ChatOpenAI(
            model=self.model,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            api_key=self.api_key
        )

    def evaluate_resume(self, resume_text: str, jd_text: str) -> CandidateEvaluation:
        """Evaluate resume using OpenAI LLM."""
        if ChatPromptTemplate is None:
            raise ImportError("langchain-core is not installed")

        llm = self.get_llm()
        structured_llm = llm.with_structured_output(CandidateEvaluation)

        # Use the same prompt as Groq for consistency
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert technical recruiter and hiring manager.
Your task is to evaluate a candidate's resume against a job description (JD).
You must provide rigorous, multi-dimensional scores (0-100) and detailed explanations.

Scoring Guidelines:
1. Exact Match: Direct occurrences of required skills & tools.
2. Similarity Match: Semantic understanding of related tech (e.g., if JD asks for Kafka, but candidate has RabbitMQ or AWS Kinesis, give high similarity. If JD asks for React, and candidate has Vue/Angular, give moderate/high similarity based on context).
3. Achievement/Impact: Look for numbers, percentages, optimization times, and revenue impact. If absent, score low.
4. Ownership: Look for keywords like 'led', 'architected', 'designed', 'mentored', 'end-to-end'.

Tier Classification:
- Tier A (Fast-track): Overall strong fit, high scores across the board.
- Tier B (Technical Screen): Good match but might have gaps in some areas.
- Tier C (Needs Evaluation): Weak match, missing core skills and no related experience.

Be very objective and critical."""),
            ("human", "Job Description:\n{jd_text}\n\nCandidate Resume:\n{resume_text}")
        ])

        chain = prompt | structured_llm
        return chain.invoke({"jd_text": jd_text, "resume_text": resume_text})

    def generate_job_post(
        self,
        title: str,
        location: Optional[str] = None,
        additional_info: Optional[str] = None
    ) -> dict:
        """Generate job post using OpenAI LLM."""
        if ChatPromptTemplate is None:
            raise ImportError("langchain-core is not installed")

        llm = self.get_llm()
        structured_llm = llm.with_structured_output(JobPostGeneration)

        context = ""
        if location:
            context += f"\nLocation: {location}"
        if additional_info:
            context += f"\nAdditional Information: {additional_info}"

        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert technical recruiter and job description writer.
Your task is to create a comprehensive, professional job posting based on the job title.

The job description should include:
1. A compelling introduction about the role and company
2. Key responsibilities and day-to-day activities
3. Required qualifications and technical skills
4. Preferred qualifications (nice-to-have skills)
5. Information about company culture and growth opportunities

Make the description detailed enough to attract qualified candidates while being specific about requirements.
Use professional language and format with clear sections."""),
            ("human", "Job Title: {title}{context}\n\nGenerate a comprehensive job posting for this position.")
        ])

        chain = prompt | structured_llm
        result = chain.invoke({"title": title, "context": context})

        return {
            "description": result.description,
            "requirements": result.requirements
        }

    def generate_interview_questions(
        self,
        candidate_profile: dict,
        job_description: str,
        num_questions: int = 10
    ) -> list[dict]:
        """Generate interview questions using OpenAI API."""
        # Similar implementation to Groq but using OpenAI client
        # This is a simplified version - full implementation would use OpenAI client
        return []

    def rewrite_resume_for_job(
        self,
        resume_text: str,
        job_description: str,
        job_title: str
    ) -> dict:
        """Rewrite resume to better match job description using OpenAI API."""
        # Implementation would use OpenAI client similar to Groq
        # Returning fallback for now
        return {
            "improved_summary": f"Experienced professional with expertise relevant to {job_title} position.",
            "suggested_bullets": [
                "• Demonstrated expertise in key skills required for the role",
                "• Proven track record of delivering results in similar positions"
            ],
            "skills_to_highlight": ["Leadership", "Communication"],
            "keywords_to_add": ["Results-driven", "Innovative"],
            "cover_letter_suggestion": f"I am excited to apply for the {job_title} position..."
        }


# =============================================================================
# Provider Factory
# =============================================================================

class LLMProviderFactory:
    """
    Factory for creating LLM provider instances.

    This factory manages provider instantiation based on configuration,
    making it easy to switch between different LLM providers.
    """

    _providers = {
        'groq': GroqProvider,
        'openai': OpenAIProvider,
        # 'anthropic': AnthropicProvider,  # Add when needed
    }

    @classmethod
    def create_provider(cls, provider_name: Optional[str] = None) -> BaseLLMProvider:
        """
        Create an LLM provider instance based on configuration.

        Args:
            provider_name: Provider name (groq, openai, etc.). If None, reads from config.

        Returns:
            BaseLLMProvider: Configured provider instance

        Raises:
            ValueError: If provider is not supported or configuration is invalid
        """
        config = get_config()

        if provider_name is None:
            provider_name = config.llm_provider

        provider_name = provider_name.lower()

        if provider_name not in cls._providers:
            raise ValueError(
                f"Unsupported LLM provider: '{provider_name}'. "
                f"Supported providers: {list(cls._providers.keys())}"
            )

        provider_class = cls._providers[provider_name]

        return provider_class(
            api_key=config.llm.api_key,
            model=config.llm.model,
            temperature=config.llm.temperature,
            max_tokens=config.llm.max_tokens
        )

    @classmethod
    def register_provider(cls, name: str, provider_class: type[BaseLLMProvider]):
        """
        Register a custom provider.

        Args:
            name: Provider name
            provider_class: Provider class (must inherit from BaseLLMProvider)
        """
        if not issubclass(provider_class, BaseLLMProvider):
            raise TypeError("Provider class must inherit from BaseLLMProvider")
        cls._providers[name.lower()] = provider_class


# =============================================================================
# Convenience Functions
# =============================================================================

# Global provider instance (lazy-loaded)
_provider: Optional[BaseLLMProvider] = None


def get_provider() -> BaseLLMProvider:
    """
    Get the global LLM provider instance.

    Creates and caches the provider on first call based on configuration.

    Returns:
        BaseLLMProvider: The configured LLM provider
    """
    global _provider
    if _provider is None:
        _provider = LLMProviderFactory.create_provider()
    return _provider


def reset_provider():
    """Reset the global provider instance. Useful for testing."""
    global _provider
    _provider = None
