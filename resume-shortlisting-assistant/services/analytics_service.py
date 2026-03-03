"""
Analytics Service - Business logic for analytics operations.

This service handles all analytics-related business rules, including
statistics, skill gap analysis, and candidate ranking.

Contributor: shubham21155102 - Service Layer Architecture
"""

from typing import List, Dict, Optional, Any
from dataclasses import dataclass

from database import db
from error_handlers import ValidationError, BusinessLogicError
from structured_logging import get_logger, LogContext
import psycopg2.extras

logger = get_logger(__name__)


@dataclass
class RankingFilter:
    """Filter parameters for candidate ranking"""
    tier: Optional[str] = None
    sort_by: str = 'overall_score'
    order: str = 'desc'
    limit: int = 20

    def validate(self):
        """Validate ranking filter parameters."""
        valid_sort_options = [
            'overall_score', 'exact_match', 'similarity_match',
            'achievement_impact', 'ownership'
        ]
        if self.sort_by not in valid_sort_options:
            raise ValidationError(
                f"Invalid sort_by option. Must be one of: {', '.join(valid_sort_options)}"
            )

        if self.order not in ['asc', 'desc']:
            raise ValidationError("Invalid order option. Must be 'asc' or 'desc'")


class AnalyticsService:
    """
    Service layer for analytics operations.

    This class encapsulates all business logic related to analytics,
    including statistics, skill gap analysis, and candidate ranking.
    """

    def __init__(self):
        self.db = db

    def get_statistics(self, request_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get database statistics.

        Args:
            request_id: Request tracking ID

        Returns:
            Dict with various statistics
        """
        with LogContext(request_id=request_id, operation='get_statistics'):
            try:
                logger.info("Fetching system statistics")

                stats = self.db.get_statistics()

                logger.info("Statistics retrieved successfully")

                return stats

            except Exception as e:
                logger.error("Failed to fetch statistics", exc_info=True)
                raise BusinessLogicError(f"Failed to fetch statistics: {str(e)}")

    def get_analytics(self, request_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get comprehensive analytics data.

        Args:
            request_id: Request tracking ID

        Returns:
            Dict with analytics data including trends and metrics
        """
        with LogContext(request_id=request_id, operation='get_analytics'):
            try:
                logger.info("Fetching comprehensive analytics")

                cursor = self.db.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

                # Candidates by tier
                cursor.execute("""
                    SELECT tier, COUNT(*) as count
                    FROM candidates
                    GROUP BY tier
                    ORDER BY tier
                """)
                by_tier = {row['tier']: row['count'] for row in cursor.fetchall() if row.get('tier')}

                # Candidates over time (last 30 days)
                cursor.execute("""
                    SELECT DATE(created_at) as date, COUNT(*) as count
                    FROM candidates
                    WHERE created_at >= CURRENT_DATE - INTERVAL '30 days'
                    GROUP BY DATE(created_at)
                    ORDER BY date
                """)
                candidates_over_time = [
                    (row['date'].strftime('%Y-%m-%d'), row['count'])
                    for row in cursor.fetchall()
                ]

                # Active job posts count
                cursor.execute("SELECT COUNT(*) as count FROM job_posts WHERE status = 'active'")
                active_jobs = cursor.fetchone()['count']

                # Average scores by tier
                cursor.execute("""
                    SELECT tier,
                           AVG(exact_match_score) as avg_exact,
                           AVG(similarity_match_score) as avg_similarity,
                           AVG(achievement_impact_score) as avg_impact,
                           AVG(ownership_score) as avg_ownership
                    FROM candidates
                    GROUP BY tier
                    ORDER BY tier
                """)
                avg_scores_by_tier = {}
                for row in cursor.fetchall():
                    if row.get('tier'):
                        avg_scores_by_tier[row['tier']] = {
                            'exact_match': float(round(row['avg_exact'], 2)) if row.get('avg_exact') else 0,
                            'similarity_match': float(round(row['avg_similarity'], 2)) if row.get('avg_similarity') else 0,
                            'achievement_impact': float(round(row['avg_impact'], 2)) if row.get('avg_impact') else 0,
                            'ownership': float(round(row['avg_ownership'], 2)) if row.get('avg_ownership') else 0,
                        }

                # Top locations
                cursor.execute("""
                    SELECT location, COUNT(*) as count
                    FROM candidates
                    WHERE location IS NOT NULL AND location != ''
                    GROUP BY location
                    ORDER BY count DESC
                    LIMIT 10
                """)
                top_locations = [(row['location'], row['count']) for row in cursor.fetchall()]

                # Recent candidates (last 7 days)
                cursor.execute("""
                    SELECT id, name, email, tier, created_at
                    FROM candidates
                    WHERE created_at >= CURRENT_DATE - INTERVAL '7 days'
                    ORDER BY created_at DESC
                    LIMIT 10
                """)
                recent_candidates = [dict(row) for row in cursor.fetchall()]

                cursor.close()

                logger.info("Analytics retrieved successfully")

                return {
                    'by_tier': by_tier,
                    'candidates_over_time': candidates_over_time,
                    'active_jobs': active_jobs,
                    'avg_scores_by_tier': avg_scores_by_tier,
                    'top_locations': top_locations,
                    'recent_candidates': recent_candidates,
                    'total_candidates': sum(by_tier.values()),
                }

            except Exception as e:
                logger.error("Failed to fetch analytics", exc_info=True)
                raise BusinessLogicError(f"Failed to fetch analytics: {str(e)}")

    def analyze_skill_gap(
        self,
        job_skills: List[str],
        request_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Analyze skill gaps in the candidate pool.

        Args:
            job_skills: List of required skills
            request_id: Request tracking ID

        Returns:
            Dict with skill gap analysis results

        Raises:
            ValidationError: If input validation fails
        """
        with LogContext(request_id=request_id, operation='skill_gap_analysis'):
            try:
                if not job_skills or not isinstance(job_skills, list):
                    raise ValidationError('job_skills must be a non-empty list')

                if len(job_skills) < 1:
                    raise ValidationError('At least one skill is required')

                logger.info(f"Analyzing skill gap for {len(job_skills)} skills")

                cursor = self.db.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

                # Get all candidates with their skills
                cursor.execute("""
                    SELECT id, name, skills, tier
                    FROM candidates
                    WHERE skills IS NOT NULL AND skills != ''
                    ORDER BY tier
                """)
                candidates = cursor.fetchall()
                cursor.close()

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
                skill_to_candidates = {skill: [] for skill in job_skills_lower}

                for candidate in candidates:
                    candidate_skills = candidate.get('skills', '').lower()
                    for skill in job_skills_lower:
                        if skill in candidate_skills:
                            found_skills.add(skill)
                            skill_to_candidates[skill].append(candidate.get('name', 'Unknown'))

                missing_skills = [s for s in job_skills_lower if s not in found_skills]
                coverage_percentage = (len(found_skills) / len(job_skills_lower)) * 100

                # Generate recommendations
                recommendations = []
                if coverage_percentage < 50:
                    recommendations.append(
                        f"Low skill coverage ({coverage_percentage:.1f}%). Consider targeting "
                        f"recruitment efforts towards candidates with these missing skills."
                    )
                elif coverage_percentage < 80:
                    recommendations.append(
                        f"Moderate skill coverage ({coverage_percentage:.1f}%). Some skills gaps exist."
                    )
                else:
                    recommendations.append(
                        f"Good skill coverage ({coverage_percentage:.1f}%). Candidate pool has most required skills."
                    )

                if missing_skills:
                    recommendations.append(
                        f"Missing skills: {', '.join(missing_skills)}. "
                        f"Consider sourcing candidates with expertise in these areas."
                    )

                # Add specific skill sourcing recommendations
                for skill in missing_skills[:3]:
                    recommendations.append(
                        f"Consider posting job ads on platforms specializing in {skill} talent, "
                        f"or reach out to professional communities for this skill."
                    )

                logger.info(
                    "Skill gap analysis completed",
                    extra={'coverage_percentage': coverage_percentage}
                )

                return {
                    'missing_skills': missing_skills,
                    'coverage_percentage': round(coverage_percentage, 1),
                    'candidate_count': len(candidates),
                    'found_skills': list(found_skills),
                    'recommendations': recommendations
                }

            except ValidationError:
                raise
            except Exception as e:
                logger.error("Failed to analyze skill gap", exc_info=True)
                raise BusinessLogicError(f"Failed to analyze skill gap: {str(e)}")

    def get_candidates_ranking(
        self,
        filters: RankingFilter,
        request_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get candidates ranked by their match score.

        Args:
            filters: RankingFilter with sort and filter parameters
            request_id: Request tracking ID

        Returns:
            Dict with ranked candidates and statistics

        Raises:
            ValidationError: If filter validation fails
        """
        with LogContext(request_id=request_id, operation='get_ranking'):
            try:
                # Validate filters
                filters.validate()

                logger.info(
                    "Fetching candidates ranking",
                    extra={
                        'sort_by': filters.sort_by,
                        'order': filters.order,
                        'tier': filters.tier,
                        'limit': filters.limit
                    }
                )

                # Get candidates with their scores
                cursor = self.db.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

                # Build query based on tier filter
                base_query = """
                    SELECT
                        id, name, email, phone, location, skills, education,
                        current_role, experience_years, tier, summary,
                        exact_match_score, similarity_match_score,
                        achievement_impact_score, ownership_score,
                        resume_filename, created_at
                    FROM candidates
                """
                params = []

                if filters.tier:
                    base_query += " WHERE tier = %s"
                    params.append(filters.tier)

                cursor.execute(base_query, params)
                candidates = cursor.fetchall()
                cursor.close()

                # Calculate overall score for each candidate
                ranked_candidates = []
                for candidate in candidates:
                    scores = [
                        candidate.get('exact_match_score', 0) or 0,
                        candidate.get('similarity_match_score', 0) or 0,
                        candidate.get('achievement_impact_score', 0) or 0,
                        candidate.get('ownership_score', 0) or 0
                    ]
                    valid_scores = [s for s in scores if s is not None and isinstance(s, (int, float))]
                    overall_score = sum(valid_scores) / len(valid_scores) if valid_scores else 0

                    ranked_candidates.append({
                        'id': candidate['id'],
                        'name': candidate.get('name', 'Unknown'),
                        'email': candidate.get('email'),
                        'current_role': candidate.get('current_role'),
                        'location': candidate.get('location'),
                        'tier': candidate.get('tier'),
                        'overall_score': round(overall_score, 2),
                        'exact_match_score': candidate.get('exact_match_score', 0) or 0,
                        'similarity_match_score': candidate.get('similarity_match_score', 0) or 0,
                        'achievement_impact_score': candidate.get('achievement_impact_score', 0) or 0,
                        'ownership_score': candidate.get('ownership_score', 0) or 0,
                        'resume_filename': candidate.get('resume_filename'),
                        'created_at': candidate.get('created_at').isoformat() if candidate.get('created_at') else None
                    })

                # Sort candidates based on sort_by parameter
                reverse = (filters.order == 'desc')
                ranked_candidates.sort(key=lambda x: x.get(filters.sort_by, 0), reverse=reverse)

                # Apply limit
                ranked_candidates = ranked_candidates[:filters.limit]

                # Assign rankings
                for idx, candidate in enumerate(ranked_candidates, 1):
                    candidate['rank'] = idx

                # Calculate statistics
                if ranked_candidates:
                    avg_scores = {
                        'overall_score': round(sum(c['overall_score'] for c in ranked_candidates) / len(ranked_candidates), 2),
                        'exact_match': round(sum(c['exact_match_score'] for c in ranked_candidates) / len(ranked_candidates), 2),
                        'similarity_match': round(sum(c['similarity_match_score'] for c in ranked_candidates) / len(ranked_candidates), 2),
                        'achievement_impact': round(sum(c['achievement_impact_score'] for c in ranked_candidates) / len(ranked_candidates), 2),
                        'ownership': round(sum(c['ownership_score'] for c in ranked_candidates) / len(ranked_candidates), 2),
                    }
                else:
                    avg_scores = {
                        'overall_score': 0,
                        'exact_match': 0,
                        'similarity_match': 0,
                        'achievement_impact': 0,
                        'ownership': 0,
                    }

                logger.info(
                    "Candidates ranking retrieved",
                    extra={'count': len(ranked_candidates)}
                )

                return {
                    'ranked_candidates': ranked_candidates,
                    'count': len(ranked_candidates),
                    'statistics': avg_scores,
                    'filters': {
                        'tier': filters.tier,
                        'sort_by': filters.sort_by,
                        'order': filters.order
                    }
                }

            except ValidationError:
                raise
            except Exception as e:
                logger.error("Failed to get candidates ranking", exc_info=True)
                raise BusinessLogicError(f"Failed to get candidates ranking: {str(e)}")


# Singleton instance
analytics_service = AnalyticsService()
