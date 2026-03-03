"""
Interview Question Generator with Gap Analysis.

This module provides intelligent interview question generation based on:
1. The gaps between a candidate's resume and the job description
2. The candidate's tier classification
3. The evaluation scores across different dimensions

The generated questions are specifically designed to:
- Test whether gaps in the resume are genuine skill gaps
- Probe deeper into areas where the candidate scored lower
- Validate the candidate's actual proficiency in claimed skills
- Assess cultural fit and behavioral attributes

Contributor: shubham21155102 - Enterprise Architecture Phase 7
"""

import re
import json
import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum

from llm_providers import get_provider
from prompts import get_interview_questions_prompt
from structured_logging import get_logger, LogContext

logger = get_logger(__name__)


class QuestionCategory(Enum):
    """Categories of interview questions."""
    TECHNICAL = "Technical"
    BEHAVIORAL = "Behavioral"
    CULTURAL = "Cultural"
    GAP_PROBING = "Gap Probing"  # Questions specifically about resume gaps
    ACHIEVEMENT = "Achievement"  # Questions about claimed achievements
    SKILL_VALIDATION = "Skill Validation"  # Validate claimed skills


class QuestionDifficulty(Enum):
    """Difficulty levels for interview questions."""
    FOUNDATIONAL = "Foundational"  # For Tier C candidates
    INTERMEDIATE = "Intermediate"  # For Tier B candidates
    ADVANCED = "Advanced"  # For Tier A candidates
    EXPERT = "Expert"  # Challenging questions even for Tier A


@dataclass
class InterviewQuestion:
    """A single interview question with metadata."""
    question: str
    category: QuestionCategory
    difficulty: QuestionDifficulty
    target_gap: Optional[str] = None  # The specific gap this question addresses
    expected_answer_indicators: List[str] = field(default_factory=list)
    red_flags: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API response."""
        return {
            'question': self.question,
            'category': self.category.value,
            'difficulty': self.difficulty.value,
            'target_gap': self.target_gap,
            'expected_answer_indicators': self.expected_answer_indicators,
            'red_flags': self.red_flags
        }


@dataclass
class SkillGap:
    """A identified skill gap between resume and job description."""
    missing_skill: str
    related_skills: List[str]  # Skills in resume that might be related
    gap_importance: str  # "critical", "important", "nice_to_have"
    suggested_questions: List[str] = field(default_factory=list)


@dataclass
class QuestionGenerationResult:
    """Result of interview question generation."""
    candidate_id: Optional[int]
    candidate_name: str
    tier: str
    questions: List[InterviewQuestion]
    identified_gaps: List[SkillGap]
    question_distribution: Dict[str, int]
    total_questions: int

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API response."""
        return {
            'candidate_id': self.candidate_id,
            'candidate_name': self.candidate_name,
            'tier': self.tier,
            'questions': [q.to_dict() for q in self.questions],
            'identified_gaps': [
                {
                    'missing_skill': g.missing_skill,
                    'related_skills': g.related_skills,
                    'gap_importance': g.gap_importance,
                    'suggested_questions': g.suggested_questions
                }
                for g in self.identified_gaps
            ],
            'question_distribution': self.question_distribution,
            'total_questions': self.total_questions
        }


class IntelligentQuestionGenerator:
    """
    Generates interview questions based on gap analysis.

    This class analyzes the gaps between a candidate's resume and the
    job description, then generates targeted questions to probe these gaps.
    """

    def __init__(self):
        """Initialize the question generator."""
        self.provider = get_provider()

    def _extract_skills_from_text(self, text: str) -> List[str]:
        """
        Extract skills from text using keyword matching.

        Args:
            text: Text to extract skills from

        Returns:
            List of extracted skills
        """
        # Common technical skill patterns
        skill_patterns = [
            r'\b(Python|JavaScript|TypeScript|Java|C\+\+|Go|Rust|Ruby|PHP|Swift|Kotlin)\b',
            r'\b(React|Angular|Vue|Next\.js|Node\.js|Express|Django|Flask|Spring)\b',
            r'\b(AWS|Azure|GCP|Docker|Kubernetes|Terraform|Ansible)\b',
            r'\b(SQL|NoSQL|MongoDB|PostgreSQL|MySQL|Redis|Elasticsearch)\b',
            r'\b(Machine Learning|AI|Data Science|Deep Learning|NLP|Computer Vision|TensorFlow|PyTorch)\b',
        ]

        skills = set()
        text_lower = text.lower()

        for pattern in skill_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                skills.add(match.lower())

        return list(skills)

    def _identify_gaps(
        self,
        resume_text: str,
        job_description: str,
        extracted_skills: Optional[str] = None
    ) -> List[SkillGap]:
        """
        Identify skill gaps between resume and job description.

        Args:
            resume_text: Candidate's resume text
            job_description: Job description text
            extracted_skills: Comma-separated skills from resume

        Returns:
            List of identified skill gaps
        """
        # Extract skills from both sources
        jd_skills = self._extract_skills_from_text(job_description)

        resume_skills_list = []
        if extracted_skills:
            resume_skills_list = [s.strip().lower() for s in extracted_skills.split(',')]
        else:
            resume_skills_list = self._extract_skills_from_text(resume_text)

        # Find gaps
        gaps = []
        for jd_skill in jd_skills:
            if jd_skill not in resume_skills_list:
                # Check for related skills
                related = []
                for resume_skill in resume_skills_list:
                    # Simple relatedness check - could be enhanced
                    if self._are_skills_related(jd_skill, resume_skill):
                        related.append(resume_skill)

                # Determine importance based on frequency in JD
                jd_lower = job_description.lower()
                count = jd_lower.count(jd_skill.lower())
                if count >= 3:
                    importance = "critical"
                elif count >= 2:
                    importance = "important"
                else:
                    importance = "nice_to_have"

                gaps.append(SkillGap(
                    missing_skill=jd_skill,
                    related_skills=related,
                    gap_importance=importance
                ))

        return gaps

    def _are_skills_related(self, skill1: str, skill2: str) -> bool:
        """
        Check if two skills might be related.

        Args:
            skill1: First skill
            skill2: Second skill

        Returns:
            True if skills might be related
        """
        # Framework relationships
        framework_groups = [
            {'react', 'next.js', 'gatsby', 'vue', 'angular', 'svelte'},
            {'node.js', 'express', 'koa', 'nest.js'},
            {'django', 'flask', 'fastapi'},
            {'tensorflow', 'pytorch', 'keras'},
            {'aws', 'azure', 'gcp'},
        ]

        for group in framework_groups:
            if skill1.lower() in group and skill2.lower() in group:
                return True

        return False

    def _determine_difficulty_from_tier(self, tier: str) -> QuestionDifficulty:
        """
        Determine question difficulty based on candidate tier.

        Args:
            tier: Candidate tier (Tier A, B, C)

        Returns:
            Appropriate difficulty level
        """
        if tier == "Tier A":
            return QuestionDifficulty.ADVANCED
        elif tier == "Tier B":
            return QuestionDifficulty.INTERMEDIATE
        else:
            return QuestionDifficulty.FOUNDATIONAL

    def _generate_gap_probing_questions(
        self,
        gaps: List[SkillGap],
        count: int = 3
    ) -> List[InterviewQuestion]:
        """
        Generate questions specifically targeting identified gaps.

        Args:
            gaps: List of skill gaps
            count: Number of questions to generate

        Returns:
            List of gap-probing interview questions
        """
        questions = []

        # Sort gaps by importance
        critical_gaps = [g for g in gaps if g.gap_importance == "critical"]
        important_gaps = [g for g in gaps if g.gap_importance == "important"]

        prioritized_gaps = critical_gaps + important_gaps

        for gap in prioritized_gaps[:count]:
            if gap.related_skills:
                # Candidate has related skills - ask about transferability
                question_text = (
                    f"I notice you have experience with {', '.join(gap.related_skills)}. "
                    f"How would you approach learning {gap.missing_skill}, and can you describe "
                    f"any situations where your experience with {gap.related_skills[0]} "
                    f"might be applicable to a {gap.missing_skill} context?"
                )
            else:
                # No related skills - ask about learning approach
                question_text = (
                    f"Our role requires experience with {gap.missing_skill}. "
                    f"Could you describe your approach to learning new technologies "
                    f"and give an example of how you've quickly adapted to a new tool or framework?"
                )

            questions.append(InterviewQuestion(
                question=question_text,
                category=QuestionCategory.GAP_PROBING,
                difficulty=QuestionDifficulty.INTERMEDIATE,
                target_gap=gap.missing_skill,
                expected_answer_indicators=[
                    "Growth mindset",
                    "Learning agility",
                    "Transferable skills",
                    "Adaptability"
                ],
                red_flags=[
                    "Resistance to learning",
                    "Overconfidence without evidence",
                    "No concrete learning examples"
                ]
            ))

        return questions

    def _generate_skill_validation_questions(
        self,
        resume_text: str,
        job_description: str,
        tier: str,
        count: int = 3
    ) -> List[InterviewQuestion]:
        """
        Generate questions to validate claimed skills.

        Args:
            resume_text: Candidate's resume
            job_description: Job description
            tier: Candidate tier
            count: Number of questions to generate

        Returns:
            List of skill validation questions
        """
        difficulty = self._determine_difficulty_from_tier(tier)
        questions = []

        # Extract key skills from resume
        resume_skills = self._extract_skills_from_text(resume_text)[:5]

        for skill in resume_skills[:count]:
            if difficulty == QuestionDifficulty.ADVANCED:
                question_text = (
                    f"You've listed {skill} as one of your key skills. Can you describe "
                    f"the most challenging technical problem you've solved using {skill}, "
                    f"and explain your thought process in detail? Please include specific "
                    f"alternatives you considered and why you chose your approach."
                )
            elif difficulty == QuestionDifficulty.INTERMEDIATE:
                question_text = (
                    f"Regarding your experience with {skill}, could you walk me through "
                    f"a project where you used this technology? What was your specific "
                    f"contribution and what were the outcomes?"
                )
            else:
                question_text = (
                    f"I see you have experience with {skill}. Can you tell me about "
                    f"a project where you used this technology and what your role was?"
                )

            questions.append(InterviewQuestion(
                question=question_text,
                category=QuestionCategory.SKILL_VALIDATION,
                difficulty=difficulty,
                target_gap=None,
                expected_answer_indicators=[
                    "Specific examples",
                    "Technical depth",
                    "Problem-solving approach",
                    "Results-oriented"
                ],
                red_flags=[
                    "Vague responses",
                    "Unable to provide details",
                    "Overstated involvement"
                ]
            ))

        return questions

    def _generate_behavioral_questions(
        self,
        count: int = 2
    ) -> List[InterviewQuestion]:
        """
        Generate behavioral interview questions.

        Args:
            count: Number of questions to generate

        Returns:
            List of behavioral questions
        """
        behavioral_questions = [
            "Tell me about a time you had to make a difficult decision with limited information. What was your thought process?",
            "Describe a situation where you had to work with a challenging team member. How did you handle it?",
            "Give an example of a time you identified a problem others had overlooked. What did you do?",
            "Tell me about a project that didn't go as planned. How did you adapt and what did you learn?",
            "Describe a time you had to persuade stakeholders to accept your technical recommendation."
        ]

        questions = []
        for i in range(min(count, len(behavioral_questions))):
            questions.append(InterviewQuestion(
                question=behavioral_questions[i],
                category=QuestionCategory.BEHAVIORAL,
                difficulty=QuestionDifficulty.INTERMEDIATE
            ))

        return questions

    async def generate_questions_with_gap_analysis(
        self,
        candidate_profile: Dict[str, Any],
        job_description: str,
        num_questions: int = 10,
        request_id: Optional[str] = None
    ) -> QuestionGenerationResult:
        """
        Generate interview questions based on comprehensive gap analysis.

        Args:
            candidate_profile: Candidate information
            job_description: Job description
            num_questions: Total number of questions to generate
            request_id: Optional request tracking ID

        Returns:
            QuestionGenerationResult with questions and gap analysis
        """
        with LogContext(request_id=request_id, operation='generate_questions_gap_analysis'):
            logger.info(
                f"Generating {num_questions} questions for candidate: "
                f"{candidate_profile.get('name', 'Unknown')}"
            )

            resume_text = candidate_profile.get('resume_text', '')
            tier = candidate_profile.get('tier', 'Tier C')
            extracted_skills = candidate_profile.get('skills', '')

            # Identify gaps
            gaps = self._identify_gaps(resume_text, job_description, extracted_skills)
            logger.info(f"Identified {len(gaps)} skill gaps")

            # Determine question distribution based on tier and gaps
            gap_questions = self._generate_gap_probing_questions(gaps, count=min(3, len(gaps)))
            skill_questions = self._generate_skill_validation_questions(
                resume_text, job_description, tier, count=min(3, num_questions - len(gap_questions))
            )
            behavioral_questions = self._generate_behavioral_questions(
                count=min(2, num_questions - len(gap_questions) - len(skill_questions))
            )

            # Generate remaining questions using LLM for variety
            remaining_count = num_questions - len(gap_questions) - len(skill_questions) - len(behavioral_questions)

            llm_questions = []
            if remaining_count > 0:
                try:
                    system_msg, human_msg = get_interview_questions_prompt(
                        candidate_profile, job_description, remaining_count
                    )
                    llm_result = self.provider._call_llm_json(system_msg, human_msg)

                    if isinstance(llm_result, list):
                        for item in llm_result:
                            if isinstance(item, dict) and 'question' in item:
                                category_str = item.get('category', 'Technical')
                                try:
                                    category = QuestionCategory(category_str)
                                except ValueError:
                                    category = QuestionCategory.TECHNICAL

                                llm_questions.append(InterviewQuestion(
                                    question=item['question'],
                                    category=category,
                                    difficulty=self._determine_difficulty_from_tier(tier)
                                ))
                except Exception as e:
                    logger.warning(f"LLM question generation failed: {e}")

            # Combine all questions
            all_questions = gap_questions + skill_questions + behavioral_questions + llm_questions

            # Calculate distribution
            distribution = {}
            for q in all_questions:
                cat = q.category.value
                distribution[cat] = distribution.get(cat, 0) + 1

            result = QuestionGenerationResult(
                candidate_id=candidate_profile.get('id'),
                candidate_name=candidate_profile.get('name', 'Unknown'),
                tier=tier,
                questions=all_questions[:num_questions],
                identified_gaps=gaps,
                question_distribution=distribution,
                total_questions=len(all_questions[:num_questions])
            )

            logger.info(
                f"Generated {result.total_questions} questions. "
                f"Distribution: {distribution}"
            )

            return result


# Singleton instance
intelligent_question_generator = IntelligentQuestionGenerator()
