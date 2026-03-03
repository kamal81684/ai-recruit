"""
Base Repository - Abstract base class for all repositories.

This module provides the base repository class with common CRUD operations
and database connection management.

Contributor: shubham21155102 - Repository Pattern Architecture
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Any, TypeVar, Generic
from dataclasses import dataclass
import psycopg2.extras
from database import db
from structured_logging import get_logger

logger = get_logger(__name__)

T = TypeVar('T')


@dataclass
class QueryResult:
    """Standardized query result with metadata."""
    data: List[Any]
    count: int
    limit: Optional[int] = None
    offset: int = 0
    has_more: bool = False


@dataclass
class FilterOptions:
    """Common filter options for queries."""
    limit: int = 50
    offset: int = 0
    order_by: str = 'created_at'
    order_dir: str = 'DESC'
    where_clause: Optional[str] = None
    where_params: Optional[tuple] = None


class BaseRepository(ABC, Generic[T]):
    """
    Abstract base repository class.

    Provides common database operations and enforces
    consistent interface across all repositories.
    """

    def __init__(self, connection=None):
        """
        Initialize repository with database connection.

        Args:
            connection: Optional database connection (uses global db if None)
        """
        self.conn = connection or db.conn
        self._table_name = None

    @property
    def table_name(self) -> str:
        """Get the table name for this repository."""
        if self._table_name is None:
            raise NotImplementedError("Subclasses must define _table_name")
        return self._table_name

    def _get_cursor(self) -> psycopg2.extras.RealDictCursor:
        """Get a new database cursor."""
        return self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    def _execute_query(
        self,
        query: str,
        params: Optional[tuple] = None,
        fetch_one: bool = False
    ) -> Optional[Any]:
        """
        Execute a query and return results.

        Args:
            query: SQL query string
            params: Query parameters
            fetch_one: Whether to fetch one or all results

        Returns:
            Query result(s) or None
        """
        cursor = self._get_cursor()
        try:
            cursor.execute(query, params or ())
            if fetch_one:
                result = cursor.fetchone()
                return dict(result) if result else None
            else:
                results = cursor.fetchall()
                return [dict(row) for row in results]
        finally:
            cursor.close()

    def _execute_update(
        self,
        query: str,
        params: Optional[tuple] = None
    ) -> bool:
        """
        Execute an update/insert/delete query.

        Args:
            query: SQL query string
            params: Query parameters

        Returns:
            True if successful
        """
        cursor = self._get_cursor()
        try:
            cursor.execute(query, params or ())
            self.conn.commit()
            return True
        except Exception as e:
            self.conn.rollback()
            logger.error(f"Database update failed: {e}")
            raise
        finally:
            cursor.close()

    def find_by_id(self, entity_id: int) -> Optional[T]:
        """
        Find an entity by its ID.

        Args:
            entity_id: Entity ID

        Returns:
            Entity or None if not found
        """
        query = f"SELECT * FROM {self.table_name} WHERE id = %s"
        return self._execute_query(query, (entity_id,), fetch_one=True)

    def find_all(
        self,
        filters: Optional[FilterOptions] = None
    ) -> QueryResult:
        """
        Find all entities with optional filtering.

        Args:
            filters: Filter options

        Returns:
            QueryResult with data and metadata
        """
        filters = filters or FilterOptions()

        query = f"SELECT * FROM {self.table_name}"

        if filters.where_clause:
            query += f" WHERE {filters.where_clause}"

        query += f" ORDER BY {filters.order_by} {filters.order_dir}"
        query += f" LIMIT %s OFFSET %s"

        data = self._execute_query(
            query,
            filters.where_params + (filters.limit, filters.offset)
            if filters.where_params else (filters.limit, filters.offset)
        )

        # Check if there are more results
        has_more = len(data) == filters.limit

        return QueryResult(
            data=data or [],
            count=len(data),
            limit=filters.limit,
            offset=filters.offset,
            has_more=has_more
        )

    def count(self, where_clause: Optional[str] = None) -> int:
        """
        Count entities matching optional filter.

        Args:
            where_clause: Optional WHERE clause

        Returns:
            Count of matching entities
        """
        query = f"SELECT COUNT(*) as count FROM {self.table_name}"
        if where_clause:
            query += f" WHERE {where_clause}"

        result = self._execute_query(query, fetch_one=True)
        return result['count'] if result else 0

    def delete(self, entity_id: int) -> bool:
        """
        Delete an entity by ID.

        Args:
            entity_id: Entity ID

        Returns:
            True if deleted
        """
        query = f"DELETE FROM {self.table_name} WHERE id = %s"
        return self._execute_update(query, (entity_id,))

    def exists(self, entity_id: int) -> bool:
        """
        Check if an entity exists.

        Args:
            entity_id: Entity ID

        Returns:
            True if entity exists
        """
        return self.find_by_id(entity_id) is not None

    @abstractmethod
    def save(self, entity: Dict[str, Any]) -> Optional[int]:
        """
        Save a new entity.

        Args:
            entity: Entity data

        Returns:
            New entity ID or None if failed
        """
        pass

    @abstractmethod
    def update(self, entity_id: int, entity: Dict[str, Any]) -> bool:
        """
        Update an existing entity.

        Args:
            entity_id: Entity ID
            entity: Updated entity data

        Returns:
            True if updated
        """
        pass
