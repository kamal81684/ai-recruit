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

Contributor: shubham21155102
"""

from abc import ABC, abstractmethod
from typing import Any, Optional
from pydantic import BaseModel
import os

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


# =============================================================================
# Groq Provider Implementation
# =============================================================================

class GroqProvider(BaseLLMProvider):
    """Groq LLM provider using LangChain integration."""

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
        """Evaluate resume using Groq LLM."""
        if ChatPromptTemplate is None:
            raise ImportError("langchain-core is not installed")

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
