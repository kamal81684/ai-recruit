"""
Job Repository - Database operations for job posts.

This module provides repository methods for job-related database operations.

Contributor: shubham21155102 - Repository Pattern Architecture
"""

from typing import List, Dict, Optional, Any

from .base_repository import BaseRepository, FilterOptions, QueryResult
from structured_logging import get_logger

logger = get_logger(__name__)


class JobRepository(BaseRepository):
    """
    Repository for job post database operations.

    Provides methods for CRUD operations and specialized queries
    for the job_posts table.
    """

    def __init__(self, connection=None):
        """Initialize job repository."""
        super().__init__(connection)
        self._table_name = "job_posts"

    def save(self, entity: Dict[str, Any]) -> Optional[int]:
        """
        Save a new job post to the database.

        Args:
            entity: Job post data dictionary

        Returns:
            New job post ID or None if failed
        """
        query = """
            INSERT INTO job_posts (title, description, location, requirements, status)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING id
        """

        cursor = self._get_cursor()
        try:
            cursor.execute(query, (
                entity.get('title'),
                entity.get('description'),
                entity.get('location'),
                entity.get('requirements'),
                entity.get('status', 'active')
            ))
            result = cursor.fetchone()
            self.conn.commit()
            return result['id'] if result else None
        except Exception as e:
            self.conn.rollback()
            logger.error(f"Failed to save job post: {e}")
            raise
        finally:
            cursor.close()

    def update(self, entity_id: int, entity: Dict[str, Any]) -> bool:
        """
        Update an existing job post.

        Args:
            entity_id: Job post ID
            entity: Updated job post data

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
        query = f"UPDATE job_posts SET {', '.join(updates)}, updated_at = CURRENT_TIMESTAMP WHERE id = %s"

        return self._execute_update(query, tuple(params))

    def find_by_status(
        self,
        status: str,
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict]:
        """
        Find job posts by status.

        Args:
            status: Job post status
            limit: Maximum results
            offset: Pagination offset

        Returns:
            List of job posts
        """
        filters = FilterOptions(
            where_clause="status = %s",
            where_params=(status,),
            limit=limit,
            offset=offset
        )
        result = self.find_all(filters)
        return result.data

    def find_active(self, limit: int = 50, offset: int = 0) -> List[Dict]:
        """
        Find active job posts.

        Args:
            limit: Maximum results
            offset: Pagination offset

        Returns:
            List of active job posts
        """
        return self.find_by_status('active', limit, offset)

    def search(self, search_term: str, limit: int = 50, offset: int = 0) -> List[Dict]:
        """
        Search job posts by title or description.

        Args:
            search_term: Search term
            limit: Maximum results
            offset: Pagination offset

        Returns:
            List of matching job posts
        """
        query = """
            SELECT * FROM job_posts
            WHERE title ILIKE %s OR description ILIKE %s OR requirements ILIKE %s
            ORDER BY created_at DESC
            LIMIT %s OFFSET %s
        """
        search_pattern = f"%{search_term}%"
        return self._execute_query(query, (search_pattern, search_pattern, search_pattern, limit, offset)) or []

    def get_by_location(self, location: str, limit: int = 50) -> List[Dict]:
        """
        Get job posts by location.

        Args:
            location: Job location
            limit: Maximum results

        Returns:
            List of job posts
        """
        filters = FilterOptions(
            where_clause="location ILIKE %s",
            where_params=(f"%{location}%",),
            limit=limit
        )
        result = self.find_all(filters)
        return result.data

    def get_statistics_by_status(self) -> Dict[str, int]:
        """
        Get job post count by status.

        Returns:
            Dict mapping status to count
        """
        query = """
            SELECT status, COUNT(*) as count
            FROM job_posts
            GROUP BY status
        """
        results = self._execute_query(query) or []
        return {row['status']: row['count'] for row in results}

    def update_status(self, job_id: int, status: str) -> bool:
        """
        Update job post status.

        Args:
            job_id: Job post ID
            status: New status

        Returns:
            True if updated
        """
        return self.update(job_id, {'status': status})


# Singleton instance
job_repository = JobRepository()
