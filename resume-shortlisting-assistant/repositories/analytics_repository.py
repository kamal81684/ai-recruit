"""
Analytics Repository - Database operations for analytics queries.

This module provides repository methods for analytics and reporting queries.

Contributor: shubham21155102 - Repository Pattern Architecture
"""

from typing import List, Dict, Optional, Any, Tuple
from datetime import datetime, timedelta
import psycopg2.extras

from .base_repository import BaseRepository
from structured_logging import get_logger

logger = get_logger(__name__)


class AnalyticsRepository(BaseRepository):
    """
    Repository for analytics database operations.

    Provides methods for generating reports, statistics,
    and analytical insights from the database.
    """

    def __init__(self, connection=None):
        """Initialize analytics repository."""
        super().__init__(connection)

    def save(self, entity: Dict[str, Any]) -> Optional[int]:
        """Not applicable for analytics repository."""
        raise NotImplementedError("Analytics repository doesn't support save operations")

    def update(self, entity_id: int, entity: Dict[str, Any]) -> bool:
        """Not applicable for analytics repository."""
        raise NotImplementedError("Analytics repository doesn't support update operations")

    def get_candidates_over_time(
        self,
        days: int = 30,
        group_by: str = 'day'
    ) -> List[Tuple[str, int]]:
        """
        Get candidate creation trends over time.

        Args:
            days: Number of days to look back
            group_by: Grouping level ('day', 'week', 'month')

        Returns:
            List of (date, count) tuples
        """
        date_format = {
            'day': 'YYYY-MM-DD',
            'week': 'YYYY-"W"WW',
            'month': 'YYYY-MM'
        }.get(group_by, 'YYYY-MM-DD')

        query = f"""
            SELECT DATE_FORMAT(created_at, '{date_format}') as date, COUNT(*) as count
            FROM candidates
            WHERE created_at >= CURRENT_DATE - INTERVAL '{days} days'
            GROUP BY date
            ORDER BY date
        """

        # PostgreSQL uses different syntax
        if group_by == 'day':
            query = f"""
                SELECT DATE(created_at)::text as date, COUNT(*) as count
                FROM candidates
                WHERE created_at >= CURRENT_DATE - INTERVAL '{days} days'
                GROUP BY DATE(created_at)
                ORDER BY date
            """
        elif group_by == 'week':
            query = f"""
                SELECT DATE_TRUNC('week', created_at)::text as date, COUNT(*) as count
                FROM candidates
                WHERE created_at >= CURRENT_DATE - INTERVAL '{days} days'
                GROUP BY DATE_TRUNC('week', created_at)
                ORDER BY date
            """
        elif group_by == 'month':
            query = f"""
                SELECT DATE_TRUNC('month', created_at)::text as date, COUNT(*) as count
                FROM candidates
                WHERE created_at >= CURRENT_DATE - INTERVAL '{days} days'
                GROUP BY DATE_TRUNC('month', created_at)
                ORDER BY date
            """

        cursor = self._get_cursor()
        try:
            cursor.execute(query)
            results = cursor.fetchall()
            return [(row['date'], row['count']) for row in results]
        finally:
            cursor.close()

    def get_score_distribution(
        self,
        score_type: str = 'overall'
    ) -> Dict[str, int]:
        """
        Get distribution of scores across candidates.

        Args:
            score_type: Type of score ('overall', 'exact_match', etc.)

        Returns:
            Dict mapping score ranges to counts
        """
        if score_type == 'overall':
            query = """
                SELECT
                    CASE
                        WHEN (exact_match_score + similarity_match_score + achievement_impact_score + ownership_score) / 4 >= 80 THEN 'A (80-100)'
                        WHEN (exact_match_score + similarity_match_score + achievement_impact_score + ownership_score) / 4 >= 60 THEN 'B (60-79)'
                        WHEN (exact_match_score + similarity_match_score + achievement_impact_score + ownership_score) / 4 >= 40 THEN 'C (40-59)'
                        ELSE 'D (0-39)'
                    END as score_range,
                    COUNT(*) as count
                FROM candidates
                WHERE exact_match_score IS NOT NULL
                GROUP BY score_range
                ORDER BY score_range
            """
        else:
            score_column = f"{score_type}_score"
            query = f"""
                SELECT
                    CASE
                        WHEN {score_column} >= 80 THEN 'A (80-100)'
                        WHEN {score_column} >= 60 THEN 'B (60-79)'
                        WHEN {score_column} >= 40 THEN 'C (40-59)'
                        ELSE 'D (0-39)'
                    END as score_range,
                    COUNT(*) as count
                FROM candidates
                WHERE {score_column} IS NOT NULL
                GROUP BY score_range
                ORDER BY score_range
            """

        results = self._execute_query(query) or []
        return {row['score_range']: row['count'] for row in results}

    def get_skill_coverage(
        self,
        required_skills: List[str]
    ) -> Dict[str, Any]:
        """
        Analyze skill coverage across candidates.

        Args:
            required_skills: List of required skills

        Returns:
            Dict with coverage statistics
        """
        cursor = self._get_cursor()
        try:
            # Get all candidates with skills
            cursor.execute("""
                SELECT id, name, skills
                FROM candidates
                WHERE skills IS NOT NULL AND skills != ''
            """)
            candidates = cursor.fetchall()

            found_skills = set()
            skill_candidates = {skill: [] for skill in required_skills}

            for candidate in candidates:
                skills_text = candidate.get('skills', '').lower()
                for skill in required_skills:
                    if skill.lower() in skills_text:
                        found_skills.add(skill)
                        skill_candidates[skill].append(candidate.get('name', 'Unknown'))

            return {
                'total_required': len(required_skills),
                'total_found': len(found_skills),
                'coverage_percentage': (len(found_skills) / len(required_skills) * 100) if required_skills else 0,
                'found_skills': list(found_skills),
                'missing_skills': [s for s in required_skills if s not in found_skills],
                'skill_candidates': skill_candidates
            }
        finally:
            cursor.close()

    def get_tier_distribution(self) -> Dict[str, Any]:
        """
        Get distribution of candidates by tier with statistics.

        Returns:
            Dict with tier distribution and statistics
        """
        query = """
            SELECT
                tier,
                COUNT(*) as count,
                AVG(exact_match_score) as avg_exact,
                AVG(similarity_match_score) as avg_similarity,
                AVG(achievement_impact_score) as avg_impact,
                AVG(ownership_score) as avg_ownership
            FROM candidates
            WHERE tier IS NOT NULL
            GROUP BY tier
            ORDER BY tier
        """

        results = self._execute_query(query) or []

        tiers = {}
        for row in results:
            tiers[row['tier']] = {
                'count': row['count'],
                'average_scores': {
                    'exact_match': float(round(row['avg_exact'], 2)) if row.get('avg_exact') else 0,
                    'similarity_match': float(round(row['avg_similarity'], 2)) if row.get('avg_similarity') else 0,
                    'achievement_impact': float(round(row['avg_impact'], 2)) if row.get('avg_impact') else 0,
                    'ownership': float(round(row['avg_ownership'], 2)) if row.get('avg_ownership') else 0,
                }
            }

        return tiers

    def get_conversion_funnel(self) -> Dict[str, int]:
        """
        Get candidate conversion funnel statistics.

        Returns:
            Dict with funnel metrics
        """
        # This would track candidates through the hiring process
        # For now, return tier-based funnel
        query = """
            SELECT
                COUNT(*) as total,
                SUM(CASE WHEN tier = 'A' THEN 1 ELSE 0 END) as tier_a,
                SUM(CASE WHEN tier = 'B' THEN 1 ELSE 0 END) as tier_b,
                SUM(CASE WHEN tier = 'C' THEN 1 ELSE 0 END) as tier_c
            FROM candidates
        """

        result = self._execute_query(query, fetch_one=True)

        return {
            'total_evaluated': result['total'] if result else 0,
            'top_tier': result['tier_a'] if result else 0,
            'mid_tier': result['tier_b'] if result else 0,
            'lower_tier': result['tier_c'] if result else 0,
        }

    def get_time_to_hire_metrics(self) -> Dict[str, Any]:
        """
        Get metrics about time-to-hire (placeholder for future implementation).

        Returns:
            Dict with time metrics
        """
        # This would track time from resume submission to hire
        # For now, return basic timing data
        query = """
            SELECT
                MIN(created_at) as first_candidate,
                MAX(created_at) as last_candidate,
                COUNT(*) as total_candidates
            FROM candidates
        """

        result = self._execute_query(query, fetch_one=True)

        return {
            'first_candidate_date': result.get('first_candidate').isoformat() if result and result.get('first_candidate') else None,
            'last_candidate_date': result.get('last_candidate').isoformat() if result and result.get('last_candidate') else None,
            'total_candidates': result.get('total_candidates') if result else 0,
        }

    def get_top_performing_candidates(self, limit: int = 10) -> List[Dict]:
        """
        Get top performing candidates based on overall score.

        Args:
            limit: Maximum results

        Returns:
            List of top candidates
        """
        query = """
            SELECT
                id, name, email, tier,
                (exact_match_score + similarity_match_score + achievement_impact_score + ownership_score) / 4 as overall_score,
                exact_match_score, similarity_match_score,
                achievement_impact_score, ownership_score,
                current_role, location, created_at
            FROM candidates
            WHERE exact_match_score IS NOT NULL
            ORDER BY overall_score DESC
            LIMIT %s
        """

        return self._execute_query(query, (limit,)) or []

    def get_skill_gap_analysis(
        self,
        job_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Analyze skill gaps for a job or across all jobs.

        Args:
            job_id: Optional job ID to analyze

        Returns:
            Dict with skill gap analysis
        """
        if job_id:
            # Get skills from job post
            job_query = "SELECT requirements FROM job_posts WHERE id = %s"
            job_result = self._execute_query(job_query, (job_id,), fetch_one=True)

            if not job_result or not job_result.get('requirements'):
                return {'error': 'Job not found or no requirements specified'}

            # Extract skills from requirements (simple keyword extraction)
            requirements_text = job_result['requirements'].lower()
            # This is a simplified extraction - in production, use NLP
            import re
            potential_skills = re.findall(r'\b[a-z]{3,}\b', requirements_text)

            # Filter to common tech skills (simplified)
            common_skills = ['python', 'javascript', 'java', 'react', 'node', 'sql',
                           'aws', 'docker', 'kubernetes', 'machine learning', 'data']
            required_skills = [s for s in potential_skills if s in common_skills]
        else:
            required_skills = ['python', 'javascript', 'react', 'node', 'sql', 'aws']

        return self.get_skill_coverage(required_skills)


# Singleton instance
analytics_repository = AnalyticsRepository()
