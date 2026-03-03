"""
Fairness Checker - Ethical AI Bias Detection Module.

This module provides bias detection and fairness auditing for AI-powered
recruitment decisions. It helps identify potential discrimination patterns
and promotes diversity and inclusion in hiring.

Features:
- University name bias detection
- Gender and age bias detection
- Demographic distribution analysis
- Fairness metrics calculation
- Audit trail generation

Contributor: shubham21155102 - Enterprise Architecture Phase 7
"""

import re
import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
from collections import Counter

from database import db
from structured_logging import get_logger, LogContext

logger = get_logger(__name__)


class BiasType(Enum):
    """Types of bias that can be detected."""
    UNIVERSITY = "university"
    GENDER = "gender"
    AGE = "age"
    LOCATION = "location"
    EXPERIENCE = "experience"
    SKILL = "skill"


class SeverityLevel(Enum):
    """Severity levels for bias warnings."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class BiasAlert:
    """A single bias detection alert."""
    bias_type: BiasType
    severity: SeverityLevel
    message: str
    affected_count: int
    total_count: int
    percentage: float
    recommendations: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API response."""
        return {
            'bias_type': self.bias_type.value,
            'severity': self.severity.value,
            'message': self.message,
            'affected_count': self.affected_count,
            'total_count': self.total_count,
            'percentage': round(self.percentage, 2),
            'recommendations': self.recommendations,
            'metadata': self.metadata
        }


@dataclass
class FairnessAudit:
    """Complete fairness audit report."""
    audit_id: str
    timestamp: datetime
    candidate_pool_size: int
    alerts: List[BiasAlert]
    demographics: Dict[str, Any]
    fairness_scores: Dict[str, float]
    overall_fairness_score: float
    passed_threshold: bool

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API response."""
        return {
            'audit_id': self.audit_id,
            'timestamp': self.timestamp.isoformat(),
            'candidate_pool_size': self.candidate_pool_size,
            'alerts': [alert.to_dict() for alert in self.alerts],
            'demographics': self.demographics,
            'fairness_scores': self.fairness_scores,
            'overall_fairness_score': round(self.overall_fairness_score, 2),
            'passed_threshold': self.passed_threshold
        }


# Patterns for bias detection
UNIVERSITY_PATTERNS = [
    r'\b(IIT|IIM|NIT|BITS|Stanford|MIT|Harvard|Yale|Princeton|Columbia|Carnegie\s*Mellon)\b',
    r'\b(University\s+of\s+(California|Cambridge|Oxford|Michigan|Texas))\b',
]

GENDER_INDICATORS = {
    'pronouns': ['he', 'him', 'his', 'she', 'her', 'hers'],
    'titles': ['mr', 'mrs', 'ms', 'miss'],
}

# Common age-related patterns that may indicate bias
AGE_PATTERNS = [
    r'\b(\d+)\s*-\s*(\d+)\s*(years?|yrs?)?\b',
    r'\b(over|under|young|recent\s*grad|entry\s*level|senior\s*level)\b',
]


class FairnessChecker:
    """
    Main fairness checker class for bias detection and auditing.

    This class analyzes candidate pools and job descriptions to detect
    potential bias patterns and provide recommendations for fairer hiring.
    """

    def __init__(self, threshold: float = 0.7):
        """
        Initialize the fairness checker.

        Args:
            threshold: Minimum fairness score threshold (0.0 to 1.0)
        """
        self.threshold = threshold
        self.db = db

    def analyze_candidate_pool(
        self,
        job_id: Optional[int] = None,
        time_window: Optional[int] = None,
        request_id: Optional[str] = None
    ) -> FairnessAudit:
        """
        Analyze the candidate pool for potential biases.

        Args:
            job_id: Optional job ID to filter candidates
            time_window: Optional time window in days (from now)
            request_id: Optional request tracking ID

        Returns:
            FairnessAudit: Complete audit report
        """
        with LogContext(request_id=request_id, operation='fairness_audit'):
            audit_id = f"audit_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

            logger.info(f"Starting fairness audit: {audit_id}")

            # Get candidate data
            candidates = self._get_candidates(job_id, time_window)

            if not candidates:
                return FairnessAudit(
                    audit_id=audit_id,
                    timestamp=datetime.now(),
                    candidate_pool_size=0,
                    alerts=[],
                    demographics={},
                    fairness_scores={},
                    overall_fairness_score=0.0,
                    passed_threshold=False
                )

            logger.info(f"Analyzing {len(candidates)} candidates")

            # Run all bias detection checks
            alerts: List[BiasAlert] = []

            # University bias detection
            university_alert = self._check_university_bias(candidates)
            if university_alert:
                alerts.append(university_alert)

            # Location bias detection
            location_alert = self._check_location_bias(candidates)
            if location_alert:
                alerts.append(location_alert)

            # Experience bias detection
            experience_alert = self._check_experience_bias(candidates)
            if experience_alert:
                alerts.append(experience_alert)

            # Skill diversity check
            skill_alert = self._check_skill_diversity(candidates)
            if skill_alert:
                alerts.append(skill_alert)

            # Calculate demographics
            demographics = self._calculate_demographics(candidates)

            # Calculate fairness scores
            fairness_scores = self._calculate_fairness_scores(candidates, alerts)

            # Calculate overall fairness score
            overall_score = self._calculate_overall_fairness(fairness_scores)

            audit = FairnessAudit(
                audit_id=audit_id,
                timestamp=datetime.now(),
                candidate_pool_size=len(candidates),
                alerts=alerts,
                demographics=demographics,
                fairness_scores=fairness_scores,
                overall_fairness_score=overall_score,
                passed_threshold=overall_score >= self.threshold
            )

            logger.info(
                f"Fairness audit complete. Score: {overall_score:.2f}, "
                f"Alerts: {len(alerts)}, Passed: {audit.passed_threshold}"
            )

            return audit

    def _get_candidates(
        self,
        job_id: Optional[int],
        time_window: Optional[int]
    ) -> List[Dict[str, Any]]:
        """Get candidates from database with optional filtering."""
        try:
            cursor = self.db.conn.cursor(cursor_factory=dict)

            query = "SELECT * FROM candidates WHERE 1=1"
            params = []

            if job_id:
                query += " AND job_id = %s"
                params.append(job_id)

            if time_window:
                cutoff_date = datetime.now() - timedelta(days=time_window)
                query += " AND created_at >= %s"
                params.append(cutoff_date)

            query += " ORDER BY created_at DESC"

            cursor.execute(query, params)
            candidates = cursor.fetchall()
            cursor.close()

            return candidates

        except Exception as e:
            logger.error(f"Failed to fetch candidates: {e}")
            return []

    def _check_university_bias(self, candidates: List[Dict]) -> Optional[BiasAlert]:
        """Check for university name bias in the candidate pool."""
        total = len(candidates)
        if total < 10:
            return None  # Not enough data

        university_counts = Counter()
        total_mentioned = 0

        for candidate in candidates:
            education = str(candidate.get('education', '')).lower()
            if any(re.search(pattern.lower(), education) for pattern in UNIVERSITY_PATTERNS):
                total_mentioned += 1
                for pattern in UNIVERSITY_PATTERNS:
                    match = re.search(pattern, education, re.IGNORECASE)
                    if match:
                        university_counts[match.group()] += 1

        if total_mentioned == 0:
            return None

        top_university_pct = (university_counts.most_common(1)[0][1] / total) * 100

        # Check if top university represents too large a portion
        if top_university_pct > 40:
            top_uni = university_counts.most_common(1)[0][0]

            severity = SeverityLevel.CRITICAL if top_university_pct > 60 else SeverityLevel.HIGH

            return BiasAlert(
                bias_type=BiasType.UNIVERSITY,
                severity=severity,
                message=f"Candidate pool shows strong bias toward graduates from {top_uni} "
                       f"({top_university_pct:.1f}% of all candidates mention this institution).",
                affected_count=university_counts[top_uni],
                total_count=total,
                percentage=top_university_pct,
                recommendations=[
                    "Consider expanding recruitment to universities beyond top-tier institutions",
                    "Implement blind resume screening for the initial review phase",
                    "Focus on skills and experience rather than university prestige",
                    "Set targets for diversity in educational backgrounds"
                ],
                metadata={
                    'top_universities': dict(university_counts.most_common(5)),
                    'total_with_university_mentioned': total_mentioned
                }
            )

        return None

    def _check_location_bias(self, candidates: List[Dict]) -> Optional[BiasAlert]:
        """Check for geographic location bias."""
        total = len(candidates)
        if total < 10:
            return None

        location_counts = Counter()
        valid_locations = 0

        for candidate in candidates:
            location = candidate.get('location')
            if location and location.strip():
                location_counts[location.strip()] += 1
                valid_locations += 1

        if valid_locations < total * 0.5:
            return None

        top_location_pct = (location_counts.most_common(1)[0][1] / valid_locations) * 100

        if top_location_pct > 70:
            top_loc = location_counts.most_common(1)[0][0]

            return BiasAlert(
                bias_type=BiasType.LOCATION,
                severity=SeverityLevel.MEDIUM,
                message=f"Candidate pool heavily concentrated in {top_loc} "
                       f"({top_location_pct:.1f}% of candidates with valid locations).",
                affected_count=location_counts[top_loc],
                total_count=valid_locations,
                percentage=top_location_pct,
                recommendations=[
                    "Consider remote work options to expand geographic diversity",
                    "Advertise in different geographic regions",
                    "Partner with organizations in underrepresented areas",
                    "Review if location requirements are truly necessary"
                ],
                metadata={
                    'top_locations': dict(location_counts.most_common(5))
                }
            )

        return None

    def _check_experience_bias(self, candidates: List[Dict]) -> Optional[BiasAlert]:
        """Check for experience level bias."""
        total = len(candidates)
        if total < 10:
            return None

        entry_level = 0
        senior_level = 0

        for candidate in candidates:
            exp_years = candidate.get('experience_years')
            if exp_years is not None:
                try:
                    years = float(exp_years)
                    if years <= 3:
                        entry_level += 1
                    elif years >= 7:
                        senior_level += 1
                except (ValueError, TypeError):
                    pass

        if entry_level + senior_level < total * 0.5:
            return None

        entry_pct = (entry_level / total) * 100
        senior_pct = (senior_level / total) * 100

        # Check for imbalance
        if entry_pct < 15 and senior_pct > 50:
            return BiasAlert(
                bias_type=BiasType.EXPERIENCE,
                severity=SeverityLevel.MEDIUM,
                message=f"Candidate pool shows significant experience bias: "
                       f"{senior_pct:.1f}% senior level vs {entry_pct:.1f}% entry level.",
                affected_count=senior_level,
                total_count=total,
                percentage=senior_pct,
                recommendations=[
                    "Consider revising job requirements to focus on skills rather than years",
                    "Include growth potential and learning ability in evaluation criteria",
                    "Partner with programs for early-career talent",
                    "Review if senior-level requirements are necessary for all roles"
                ],
                metadata={
                    'entry_level_count': entry_level,
                    'senior_level_count': senior_level,
                    'entry_percentage': entry_pct,
                    'senior_percentage': senior_pct
                }
            )

        return None

    def _check_skill_diversity(self, candidates: List[Dict]) -> Optional[BiasAlert]:
        """Check for skill diversity in the candidate pool."""
        total = len(candidates)
        if total < 10:
            return None

        skill_counts = Counter()
        total_with_skills = 0

        for candidate in candidates:
            skills = candidate.get('skills')
            if skills and skills.strip():
                total_with_skills += 1
                # Extract individual skills (comma, pipe, or newline separated)
                skill_list = re.split(r'[,|\n]', skills)
                for skill in skill_list:
                    skill_clean = skill.strip().lower()
                    if skill_clean and len(skill_clean) > 2:
                        skill_counts[skill_clean] += 1

        if total_with_skills < total * 0.5 or not skill_counts:
            return None

        # Check if a small number of skills dominates
        top_3_count = sum(count for _, count in skill_counts.most_common(3))
        top_3_pct = (top_3_count / sum(skill_counts.values())) * 100

        if top_3_pct > 80:
            top_skills = [s for s, _ in skill_counts.most_common(3)]

            return BiasAlert(
                bias_type=BiasType.SKILL,
                severity=SeverityLevel.LOW,
                message=f"Low skill diversity detected. Top 3 skills ({', '.join(top_skills)}) "
                       f"represent {top_3_pct:.1f}% of all skill mentions.",
                affected_count=top_3_count,
                total_count=sum(skill_counts.values()),
                percentage=top_3_pct,
                recommendations=[
                    "Consider broadening the skill requirements",
                    "Focus on transferable skills and learning potential",
                    "Include candidates with adjacent or complementary skill sets",
                    "Review if all required skills are truly necessary"
                ],
                metadata={
                    'top_skills': dict(skill_counts.most_common(10)),
                    'unique_skills': len(skill_counts)
                }
            )

        return None

    def _calculate_demographics(self, candidates: List[Dict]) -> Dict[str, Any]:
        """Calculate demographic distribution statistics."""
        demographics = {
            'total_candidates': len(candidates),
            'with_email': 0,
            'with_phone': 0,
            'with_location': 0,
            'with_skills': 0,
            'tier_distribution': Counter(),
            'location_distribution': Counter(),
        }

        for candidate in candidates:
            if candidate.get('email'):
                demographics['with_email'] += 1
            if candidate.get('phone'):
                demographics['with_phone'] += 1
            if candidate.get('location'):
                demographics['with_location'] += 1
                demographics['location_distribution'][candidate['location']] += 1
            if candidate.get('skills'):
                demographics['with_skills'] += 1

            tier = candidate.get('tier', 'Unknown')
            demographics['tier_distribution'][tier] += 1

        # Convert Counter to dict
        demographics['tier_distribution'] = dict(demographics['tier_distribution'])
        demographics['location_distribution'] = dict(
            demographics['location_distribution'].most_common(10)
        )

        return demographics

    def _calculate_fairness_scores(
        self,
        candidates: List[Dict],
        alerts: List[BiasAlert]
    ) -> Dict[str, float]:
        """Calculate individual fairness scores."""
        scores = {
            'university_fairness': 1.0,
            'location_fairness': 1.0,
            'experience_fairness': 1.0,
            'skill_diversity': 1.0,
        }

        for alert in alerts:
            penalty = alert.percentage / 100
            if alert.bias_type == BiasType.UNIVERSITY:
                scores['university_fairness'] = max(0.0, 1.0 - penalty)
            elif alert.bias_type == BiasType.LOCATION:
                scores['location_fairness'] = max(0.0, 1.0 - (penalty / 2))
            elif alert.bias_type == BiasType.EXPERIENCE:
                scores['experience_fairness'] = max(0.0, 1.0 - (penalty / 3))
            elif alert.bias_type == BiasType.SKILL:
                scores['skill_diversity'] = max(0.0, 1.0 - (penalty / 4))

        return scores

    def _calculate_overall_fairness(self, fairness_scores: Dict[str, float]) -> float:
        """Calculate overall fairness score from individual scores."""
        if not fairness_scores:
            return 0.0

        return sum(fairness_scores.values()) / len(fairness_scores)

    def check_job_description_fairness(
        self,
        job_description: str,
        request_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Check a job description for potential bias indicators.

        Args:
            job_description: The job description text to analyze
            request_id: Optional request tracking ID

        Returns:
            Dict with analysis results and recommendations
        """
        with LogContext(request_id=request_id, operation='job_fairness_check'):
            logger.info("Checking job description for bias")

            jd_lower = job_description.lower()
            issues = []
            score = 1.0

            # Check for gender-coded language
            masculine_words = ['aggressive', 'ambitious', 'competitive', 'dominant', 'leader']
            feminine_words = ['collaborative', 'cooperative', 'supportive', 'understanding']

            masculine_count = sum(1 for word in masculine_words if word in jd_lower)
            feminine_count = sum(1 for word in feminine_words if word in jd_lower)

            if masculine_count > feminine_count + 2:
                issues.append({
                    'type': 'gender_coding',
                    'severity': 'medium',
                    'message': 'Job description uses predominantly masculine-coded language',
                    'recommendation': 'Consider balancing with more inclusive terminology'
                })
                score -= 0.1

            # Check for age-related bias
            age_indicators = ['recent graduate', 'young', 'energetic', 'digital native']
            found_age = [word for word in age_indicators if word in jd_lower]

            if found_age:
                issues.append({
                    'type': 'age_bias',
                    'severity': 'low',
                    'message': f'Found age-related terms: {", ".join(found_age)}',
                    'recommendation': 'Focus on skills and experience rather than age indicators'
                })
                score -= 0.05

            # Check for excessive requirements
            years_patterns = re.findall(r'(\d+)\+?\s*years?', jd_lower)
            if years_patterns:
                max_years = max(int(y) for y in years_patterns)
                if max_years > 10:
                    issues.append({
                        'type': 'experience_requirements',
                        'severity': 'medium',
                        'message': f'Job requires up to {max_years}+ years of experience',
                        'recommendation': 'Consider if experience requirements could be reduced or focused on skills'
                    })
                    score -= 0.1

            # Check for degree requirements that may exclude candidates
            degree_patterns = [
                r'(bachelor|master|phd|degree|university|college)\s+(required|must)',
                r'graduate\s+of'
            ]
            for pattern in degree_patterns:
                if re.search(pattern, jd_lower):
                    issues.append({
                        'type': 'education_requirements',
                        'severity': 'low',
                        'message': 'Job description may have strict education requirements',
                        'recommendation': 'Consider if equivalent experience could be substituted'
                    })
                    score -= 0.05
                    break

            return {
                'fairness_score': max(0.0, score),
                'issues': issues,
                'recommendations': [
                    'Use gender-neutral language in job postings',
                    'Focus on skills and competencies rather than demographics',
                    'Consider alternative experience pathways',
                    'Include language welcoming diverse candidates'
                ],
                'passed': score >= 0.7
            }


# Singleton instance
fairness_checker = FairnessChecker()
