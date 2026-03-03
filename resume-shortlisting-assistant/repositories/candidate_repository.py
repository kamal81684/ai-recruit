"""
Candidate Repository - Database operations for candidates.

This module provides repository methods for candidate-related database operations.

Contributor: shubham21155102 - Repository Pattern Architecture
"""

from typing import List, Dict, Optional, Any
from datetime import datetime

from .base_repository import BaseRepository, FilterOptions, QueryResult
from structured_logging import get_logger

logger = get_logger(__name__)


class CandidateRepository(BaseRepository):
    """
    Repository for candidate database operations.

    Provides methods for CRUD operations and specialized queries
    for the candidates table.
    """

    def __init__(self, connection=None):
        """Initialize candidate repository."""
        super().__init__(connection)
        self._table_name = "candidates"

    def save(
        self,
        entity: Dict[str, Any]
    ) -> Optional[int]:
        """
        Save a new candidate to the database.

        Args:
            entity: Candidate data dictionary

        Returns:
            New candidate ID or None if failed
        """
        query = """
            INSERT INTO candidates (
                name, email, phone, resume_filename, resume_text, job_description,
                tier, summary,
                exact_match_score, exact_match_explanation,
                similarity_match_score, similarity_match_explanation,
                achievement_impact_score, achievement_impact_explanation,
                ownership_score, ownership_explanation,
                location, skills, education, experience_years, "current_role"
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """

        cursor = self._get_cursor()
        try:
            cursor.execute(query, (
                entity.get('name'),
                entity.get('email'),
                entity.get('phone'),
                entity.get('resume_filename'),
                entity.get('resume_text'),
                entity.get('job_description'),
                entity.get('tier'),
                entity.get('summary'),
                entity.get('exact_match_score'),
                entity.get('exact_match_explanation'),
                entity.get('similarity_match_score'),
                entity.get('similarity_match_explanation'),
                entity.get('achievement_impact_score'),
                entity.get('achievement_impact_explanation'),
                entity.get('ownership_score'),
                entity.get('ownership_explanation'),
                entity.get('location'),
                entity.get('skills'),
                entity.get('education'),
                entity.get('experience_years'),
                entity.get('current_role')
            ))
            result = cursor.fetchone()
            self.conn.commit()
            return result['id'] if result else None
        except Exception as e:
            self.conn.rollback()
            logger.error(f"Failed to save candidate: {e}")
            raise
        finally:
            cursor.close()

    def update(self, entity_id: int, entity: Dict[str, Any]) -> bool:
        """
        Update an existing candidate.

        Args:
            entity_id: Candidate ID
            entity: Updated candidate data

        Returns:
            True if updated successfully
        """
        updates = []
        params = []

        for key, value in entity.items():
            if key not in ['id', 'created_at'] and value is not None:
                updates.append(f"{key} = %s")
                params.append(value)

        if not updates:
            return False

        params.append(entity_id)
        query = f"UPDATE candidates SET {', '.join(updates)}, updated_at = CURRENT_TIMESTAMP WHERE id = %s"

        return self._execute_update(query, tuple(params))

    def find_by_tier(
        self,
        tier: str,
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict]:
        """
        Find candidates by tier.

        Args:
            tier: Candidate tier (A, B, C)
            limit: Maximum results
            offset: Pagination offset

        Returns:
            List of candidates
        """
        query = """
            SELECT id, name, email, phone, resume_filename, tier, summary,
                   exact_match_score, similarity_match_score,
                   achievement_impact_score, ownership_score,
                   location, skills, education, experience_years, "current_role",
                   created_at
            FROM candidates
            WHERE tier = %s
            ORDER BY created_at DESC
            LIMIT %s OFFSET %s
        """
        return self._execute_query(query, (tier, limit, offset)) or []

    def find_by_email(self, email: str) -> Optional[Dict]:
        """
        Find a candidate by email.

        Args:
            email: Candidate email

        Returns:
            Candidate or None
        """
        query = """
            SELECT * FROM candidates
            WHERE email = %s
            ORDER BY created_at DESC
            LIMIT 1
        """
        return self._execute_query(query, (email,), fetch_one=True)

    def find_by_location(
        self,
        location: str,
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict]:
        """
        Find candidates by location.

        Args:
            location: Candidate location
            limit: Maximum results
            offset: Pagination offset

        Returns:
            List of candidates
        """
        filters = FilterOptions(
            where_clause="location ILIKE %s",
            where_params=(f"%{location}%",),
            limit=limit,
            offset=offset
        )
        result = self.find_all(filters)
        return result.data

    def search_by_skills(
        self,
        skills: List[str],
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict]:
        """
        Find candidates with specific skills.

        Args:
            skills: List of skills to search for
            limit: Maximum results
            offset: Pagination offset

        Returns:
            List of candidates
        """
        # Build OR condition for skills
        skill_conditions = [f"skills ILIKE %s" for _ in skills]
        skill_params = [f"%{skill}%" for skill in skills]

        where_clause = f"({' OR '.join(skill_conditions)})"

        filters = FilterOptions(
            where_clause=where_clause,
            where_params=tuple(skill_params),
            limit=limit,
            offset=offset
        )
        result = self.find_all(filters)
        return result.data

    def search(
        self,
        search_term: str,
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict]:
        """
        Full-text search for candidates.

        Args:
            search_term: Search term
            limit: Maximum results
            offset: Pagination offset

        Returns:
            List of candidates
        """
        query = """
            SELECT id, name, email, phone, resume_filename, tier, summary,
                   exact_match_score, similarity_match_score,
                   achievement_impact_score, ownership_score,
                   location, skills, education, experience_years, "current_role",
                   created_at
            FROM candidates
            WHERE name ILIKE %s
               OR email ILIKE %s
               OR skills ILIKE %s
               OR "current_role" ILIKE %s
               OR location ILIKE %s
            ORDER BY created_at DESC
            LIMIT %s OFFSET %s
        """
        search_pattern = f"%{search_term}%"
        return self._execute_query(
            query,
            (search_pattern, search_pattern, search_pattern, search_pattern, search_pattern, limit, offset)
        ) or []

    def get_recent(
        self,
        days: int = 7,
        limit: int = 50
    ) -> List[Dict]:
        """
        Get recently added candidates.

        Args:
            days: Number of days to look back
            limit: Maximum results

        Returns:
            List of recent candidates
        """
        query = """
            SELECT id, name, email, tier, created_at
            FROM candidates
            WHERE created_at >= CURRENT_DATE - INTERVAL '%s days'
            ORDER BY created_at DESC
            LIMIT %s
        """
        return self._execute_query(query, (days, limit)) or []

    def get_statistics_by_tier(self) -> Dict[str, int]:
        """
        Get candidate count by tier.

        Returns:
            Dict mapping tier to count
        """
        query = """
            SELECT tier, COUNT(*) as count
            FROM candidates
            WHERE tier IS NOT NULL
            GROUP BY tier
            ORDER BY tier
        """
        results = self._execute_query(query) or []
        return {row['tier']: row['count'] for row in results}

    def get_average_scores(self) -> Dict[str, float]:
        """
        Get average scores across all candidates.

        Returns:
            Dict with average scores
        """
        query = """
            SELECT
                AVG(exact_match_score) as avg_exact,
                AVG(similarity_match_score) as avg_similarity,
                AVG(achievement_impact_score) as avg_impact,
                AVG(ownership_score) as avg_ownership
            FROM candidates
        """
        result = self._execute_query(query, fetch_one=True)
        if result:
            return {
                'exact_match': float(round(result['avg_exact'], 2)) if result.get('avg_exact') else 0,
                'similarity_match': float(round(result['avg_similarity'], 2)) if result.get('avg_similarity') else 0,
                'achievement_impact': float(round(result['avg_impact'], 2)) if result.get('avg_impact') else 0,
                'ownership': float(round(result['avg_ownership'], 2)) if result.get('avg_ownership') else 0,
            }
        return {
            'exact_match': 0,
            'similarity_match': 0,
            'achievement_impact': 0,
            'ownership': 0,
        }

    def get_top_locations(self, limit: int = 10) -> List[tuple]:
        """
        Get top candidate locations.

        Args:
            limit: Maximum results

        Returns:
            List of (location, count) tuples
        """
        query = """
            SELECT location, COUNT(*) as count
            FROM candidates
            WHERE location IS NOT NULL AND location != ''
            GROUP BY location
            ORDER BY count DESC
            LIMIT %s
        """
        results = self._execute_query(query, (limit,)) or []
        return [(row['location'], row['count']) for row in results]

    def get_with_interview_questions(self, candidate_id: int) -> Optional[Dict]:
        """
        Get a candidate with their interview questions.

        Args:
            candidate_id: Candidate ID

        Returns:
            Candidate with questions or None
        """
        query = """
            SELECT c.*, iq.question, iq.category as question_category
            FROM candidates c
            LEFT JOIN interview_questions iq ON c.id = iq.candidate_id
            WHERE c.id = %s
            ORDER BY iq.id
        """
        cursor = self._get_cursor()
        try:
            cursor.execute(query, (candidate_id,))
            rows = cursor.fetchall()

            if not rows:
                return None

            # Build candidate with questions
            candidate = dict(rows[0])
            questions = []
            for row in rows:
                if row.get('question'):
                    questions.append({
                        'question': row['question'],
                        'category': row.get('question_category')
                    })
            candidate['interview_questions'] = questions

            return candidate
        finally:
            cursor.close()


# Singleton instance
candidate_repository = CandidateRepository()
