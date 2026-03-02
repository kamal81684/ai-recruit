"""
Centralized LLM Prompts Module.

This module contains all prompts used throughout the application.
Centralizing prompts makes them easier to:
1. Maintain and update
2. Test (A/B testing, prompt optimization)
3. Version control
4. Reuse across different components

Contributor: shubham21155102
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class PromptTemplate:
    """Base class for prompt templates."""
    system_message: str
    human_template: str

    def format(self, **kwargs) -> str:
        """Format the human template with provided variables."""
        return self.human_template.format(**kwargs)


@dataclass
class ChatPrompt:
    """Complete chat prompt with system and human messages."""
    system: str
    human: str

    def format_human(self, **kwargs) -> str:
        """Format the human message template."""
        return self.human.format(**kwargs) if "{" in self.human else self.human


# =============================================================================
# Resume Evaluation Prompts
# =============================================================================

RESUME_EVALUATION_SYSTEM = """You are an expert technical recruiter and hiring manager.
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

Be very objective and critical."""

RESUME_EVALUATION_HUMAN = """Job Description:
{jd_text}

Candidate Resume:
{resume_text}"""

RESUME_EVALUATION_PROMPT = ChatPrompt(
    system=RESUME_EVALUATION_SYSTEM,
    human=RESUME_EVALUATION_HUMAN
)


# =============================================================================
# Job Post Generation Prompts
# =============================================================================

JOB_POST_GENERATION_SYSTEM = """You are an expert technical recruiter and job description writer.
Your task is to create a comprehensive, professional job posting based on the job title.

The job description should include:
1. A compelling introduction about the role and company
2. Key responsibilities and day-to-day activities
3. Required qualifications and technical skills
4. Preferred qualifications (nice-to-have skills)
5. Information about company culture and growth opportunities

Make the description detailed enough to attract qualified candidates while being specific about requirements.
Use professional language and format with clear sections."""

JOB_POST_GENERATION_HUMAN = "Job Title: {title}{context}\n\nGenerate a comprehensive job posting for this position."

JOB_POST_GENERATION_PROMPT = ChatPrompt(
    system=JOB_POST_GENERATION_SYSTEM,
    human=JOB_POST_GENERATION_HUMAN
)


# =============================================================================
# Interview Question Generation Prompts
# =============================================================================

INTERVIEW_QUESTIONS_SYSTEM = """You are an expert technical interviewer. Always respond with valid JSON only."""

INTERVIEW_QUESTIONS_HUMAN_TEMPLATE = """You are an expert technical interviewer. Based on the following candidate profile and job description, generate {num_questions} targeted interview questions.

CANDIDATE PROFILE:
Name: {name}
Current Role: {current_role}
Skills: {skills}
Experience: {experience_years} years
Education: {education}

JOB DESCRIPTION:
{job_description}

CANDIDATE TIER: {tier}
EVALUATION SUMMARY: {summary}

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


def format_interview_questions_prompt(
    candidate_profile: dict,
    job_description: str,
    num_questions: int = 10
) -> str:
    """
    Format the interview questions generation prompt.

    Args:
        candidate_profile: Candidate information dictionary
        job_description: Job description text
        num_questions: Number of questions to generate

    Returns:
        Formatted prompt string
    """
    return INTERVIEW_QUESTIONS_HUMAN_TEMPLATE.format(
        name=candidate_profile.get('name', 'Unknown'),
        current_role=candidate_profile.get('current_role', 'Unknown'),
        skills=candidate_profile.get('skills', 'Not specified'),
        experience_years=candidate_profile.get('experience_years', 'Unknown'),
        education=candidate_profile.get('education', 'Not specified'),
        job_description=job_description[:1000],
        tier=candidate_profile.get('tier', 'Unknown'),
        summary=candidate_profile.get('summary', '')[:500],
        num_questions=num_questions
    )


# =============================================================================
# Candidate Information Extraction Prompts
# =============================================================================

CANDIDATE_INFO_EXTRACTION_SYSTEM = """You are an expert resume parser and information extractor.
Your task is to extract key information from a candidate's resume text.

Extract the following information if present:
- Name: Full name of the candidate
- Email: Email address
- Phone: Phone number
- Location: City, State or Country
- Skills: List of technical skills (comma-separated)
- Education: Highest degree or institution
- Experience Years: Total years of experience (as a number)
- Current Role: Most recent job title

Return the information as a valid JSON object. If a field is not found, use null or an empty string.
Be accurate and only extract information that is clearly present in the resume."""

CANDIDATE_INFO_EXTRACTION_HUMAN = """Extract key information from the following resume text:

{resume_text}

Return a valid JSON object with keys: name, email, phone, location, skills, education, experience_years, current_role."""

CANDIDATE_INFO_EXTRACTION_PROMPT = ChatPrompt(
    system=CANDIDATE_INFO_EXTRACTION_SYSTEM,
    human=CANDIDATE_INFO_EXTRACTION_HUMAN
)


# =============================================================================
# Prompt Registry
# =============================================================================

class PromptRegistry:
    """
    Registry for managing prompts.

    This allows for easy prompt versioning, A/B testing, and dynamic updates.
    """

    _prompts = {
        'resume_evaluation': RESUME_EVALUATION_PROMPT,
        'job_post_generation': JOB_POST_GENERATION_PROMPT,
        'candidate_info_extraction': CANDIDATE_INFO_EXTRACTION_PROMPT,
    }

    @classmethod
    def get(cls, name: str) -> Optional[ChatPrompt]:
        """Get a prompt by name."""
        return cls._prompts.get(name)

    @classmethod
    def register(cls, name: str, prompt: ChatPrompt):
        """Register a new prompt."""
        cls._prompts[name] = prompt

    @classmethod
    def list_prompts(cls) -> list[str]:
        """List all registered prompt names."""
        return list(cls._prompts.keys())


# =============================================================================
# Convenience Functions
# =============================================================================

def get_resume_evaluation_prompt() -> ChatPrompt:
    """Get the resume evaluation prompt."""
    return PromptRegistry.get('resume_evaluation')


def get_job_post_generation_prompt() -> ChatPrompt:
    """Get the job post generation prompt."""
    return PromptRegistry.get('job_post_generation')


def get_candidate_info_extraction_prompt() -> ChatPrompt:
    """Get the candidate info extraction prompt."""
    return PromptRegistry.get('candidate_info_extraction')


def get_interview_questions_prompt(
    candidate_profile: dict,
    job_description: str,
    num_questions: int = 10
) -> tuple[str, str]:
    """
    Get the interview questions generation prompt.

    Returns:
        Tuple of (system_message, formatted_human_message)
    """
    return (
        INTERVIEW_QUESTIONS_SYSTEM,
        format_interview_questions_prompt(candidate_profile, job_description, num_questions)
    )
