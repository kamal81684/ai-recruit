"""
Semantic Vector Search Module for AI Resume Shortlisting Assistant.

This module provides semantic search capabilities using vector embeddings,
enabling more intelligent candidate matching beyond simple keyword matching.

Features:
- Vector embedding generation using OpenAI API or local models
- Cosine similarity-based candidate ranking
- Hybrid search combining keyword and semantic matching
- Efficient vector storage and retrieval

Contributor: shubham21155102 - Enterprise-grade Search Architecture
"""

import os
import json
import numpy as np
from typing import List, Dict, Optional, Tuple, Any
from dataclasses import dataclass
import sqlite3
from pathlib import Path

from config import get_config
from structured_logging import get_logger, LogContext

logger = get_logger(__name__)


@dataclass
class SearchResult:
    """Represents a semantic search result."""
    candidate_id: int
    name: Optional[str]
    email: Optional[str]
    similarity_score: float
    match_reasons: List[str]
    tier: Optional[str] = None


@dataclass
class JobEmbedding:
    """Vector embedding for a job description."""
    job_id: Optional[int]
    embedding: np.ndarray
    title: str
    description: str
    required_skills: List[str]
    created_at: str


class VectorEmbeddingGenerator:
    """
    Generates vector embeddings for text using various backends.

    Supports:
    - OpenAI embeddings API (text-embedding-3-small, text-embedding-3-large)
    - Sentence Transformers (local models)
    - TF-IDF with cosine similarity (fallback)
    """

    def __init__(self):
        """Initialize the embedding generator."""
        self.config = get_config()
        self.backend = self._determine_backend()
        self._model = None

    def _determine_backend(self) -> str:
        """Determine the best available embedding backend."""
        # Check for OpenAI API key
        if self.config.llm.provider == 'openai' and self.config.llm.api_key:
            return 'openai'

        # Check for sentence-transformers
        try:
            import sentence_transformers
            return 'sentence-transformers'
        except ImportError:
            pass

        # Fallback to TF-IDF
        return 'tfidf'

    def generate_embedding(self, text: str) -> np.ndarray:
        """
        Generate vector embedding for text.

        Args:
            text: Input text to embed

        Returns:
            Numpy array representing the text embedding
        """
        if self.backend == 'openai':
            return self._generate_openai_embedding(text)
        elif self.backend == 'sentence-transformers':
            return self._generate_sentence_transformer_embedding(text)
        else:
            return self._generate_tfidf_embedding(text)

    def _generate_openai_embedding(self, text: str) -> np.ndarray:
        """Generate embedding using OpenAI API."""
        try:
            from openai import OpenAI

            client = OpenAI(api_key=self.config.llm.api_key)
            response = client.embeddings.create(
                model="text-embedding-3-small",
                input=text[:8191]  # OpenAI limit
            )
            return np.array(response.data[0].embedding)
        except Exception as e:
            logger.error(f"OpenAI embedding failed: {e}")
            # Fallback to TF-IDF
            return self._generate_tfidf_embedding(text)

    def _generate_sentence_transformer_embedding(self, text: str) -> np.ndarray:
        """Generate embedding using sentence-transformers."""
        try:
            from sentence_transformers import SentenceTransformer

            if self._model is None:
                self._model = SentenceTransformer('all-MiniLM-L6-v2')

            return self._model.encode(text)
        except Exception as e:
            logger.error(f"Sentence transformer embedding failed: {e}")
            return self._generate_tfidf_embedding(text)

    def _generate_tfidf_embedding(self, text: str) -> np.ndarray:
        """Generate TF-IDF based embedding as fallback."""
        try:
            from sklearn.feature_extraction.text import TfidfVectorizer

            # Use a simple in-memory vectorizer
            # In production, this should be persisted
            if not hasattr(self, '_tfidf_vectorizer'):
                self._tfidf_vectorizer = TfidfVectorizer(
                    max_features=384,  # Match typical embedding size
                    stop_words='english'
                )
                # Fit on some sample data
                sample_docs = [
                    "software engineer python machine learning",
                    "web developer javascript react nodejs",
                    "data scientist python sql tensorflow",
                    text  # Include current text
                ]
                self._tfidf_vectorizer.fit(sample_docs)

            # Transform and return dense array
            embedding = self._tfidf_vectorizer.transform([text]).toarray()[0]
            return embedding
        except Exception as e:
            logger.error(f"TF-IDF embedding failed: {e}")
            # Return zero vector as last resort
            return np.zeros(384)


class SemanticSearchEngine:
    """
    Semantic search engine for candidate matching.

    Provides intelligent candidate matching using vector embeddings
    and cosine similarity, going beyond simple keyword matching.
    """

    def __init__(self, db_path: Optional[Path] = None):
        """
        Initialize the semantic search engine.

        Args:
            db_path: Path to vector database (defaults to data/vectors.db)
        """
        self.db_path = db_path or Path(__file__).parent.parent / 'data' / 'vectors.db'
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        self.embedding_generator = VectorEmbeddingGenerator()
        self._init_vector_db()

        logger.info("Semantic search engine initialized", extra={'db_path': str(self.db_path)})

    def _init_vector_db(self):
        """Initialize the vector database schema."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Create job embeddings table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS job_embeddings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                job_id INTEGER,
                title TEXT,
                description TEXT,
                required_skills TEXT,
                embedding BLOB,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Create candidate embeddings table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS candidate_embeddings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                candidate_id INTEGER UNIQUE,
                name TEXT,
                skills TEXT,
                resume_text TEXT,
                embedding BLOB,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Create indexes for faster lookup
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_job_embeddings_job_id ON job_embeddings(job_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_candidate_embeddings_candidate_id ON candidate_embeddings(candidate_id)")

        conn.commit()
        conn.close()

    def _serialize_embedding(self, embedding: np.ndarray) -> bytes:
        """Serialize numpy array to bytes for storage."""
        return embedding.tobytes()

    def _deserialize_embedding(self, blob: bytes) -> np.ndarray:
        """Deserialize bytes to numpy array."""
        return np.frombuffer(blob, dtype=np.float32)

    def index_job(
        self,
        job_id: Optional[int],
        title: str,
        description: str,
        required_skills: List[str] = None
    ) -> JobEmbedding:
        """
        Index a job for semantic search.

        Args:
            job_id: Job post ID
            title: Job title
            description: Job description
            required_skills: List of required skills

        Returns:
            JobEmbedding with generated vector
        """
        import datetime

        # Combine job text for embedding
        job_text = f"{title}. {description}"
        if required_skills:
            job_text += f" Skills: {', '.join(required_skills)}"

        # Generate embedding
        embedding = self.embedding_generator.generate_embedding(job_text)

        # Store in database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT OR REPLACE INTO job_embeddings
            (job_id, title, description, required_skills, embedding, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            job_id,
            title,
            description,
            json.dumps(required_skills or []),
            self._serialize_embedding(embedding.astype(np.float32)),
            datetime.datetime.now().isoformat()
        ))

        conn.commit()
        conn.close()

        logger.info(f"Indexed job {job_id} for semantic search")

        return JobEmbedding(
            job_id=job_id,
            embedding=embedding,
            title=title,
            description=description,
            required_skills=required_skills or [],
            created_at=datetime.datetime.now().isoformat()
        )

    def index_candidate(
        self,
        candidate_id: int,
        name: Optional[str],
        skills: Optional[str],
        resume_text: Optional[str]
    ) -> bool:
        """
        Index a candidate for semantic search.

        Args:
            candidate_id: Candidate ID
            name: Candidate name
            skills: Candidate skills (comma-separated)
            resume_text: Full resume text

        Returns:
            True if indexed successfully
        """
        import datetime

        # Combine candidate text for embedding
        candidate_text = f"{name or ''}. "
        if skills:
            candidate_text += f"Skills: {skills}. "
        if resume_text:
            # Use first 2000 chars to avoid token limits
            candidate_text += resume_text[:2000]

        # Generate embedding
        embedding = self.embedding_generator.generate_embedding(candidate_text)

        # Store in database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT OR REPLACE INTO candidate_embeddings
            (candidate_id, name, skills, resume_text, embedding, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            candidate_id,
            name,
            skills,
            resume_text,
            self._serialize_embedding(embedding.astype(np.float32)),
            datetime.datetime.now().isoformat()
        ))

        conn.commit()
        conn.close()

        logger.info(f"Indexed candidate {candidate_id} for semantic search")
        return True

    def find_similar_candidates(
        self,
        job_id: Optional[int],
        job_description: Optional[str] = None,
        job_title: Optional[str] = None,
        limit: int = 20,
        threshold: float = 0.5
    ) -> List[SearchResult]:
        """
        Find candidates similar to a job using semantic search.

        Args:
            job_id: Job post ID (if indexed)
            job_description: Job description text (for ad-hoc search)
            job_title: Job title (for ad-hoc search)
            limit: Maximum results to return
            threshold: Minimum similarity threshold (0-1)

        Returns:
            List of SearchResult candidates ranked by similarity
        """
        import datetime

        # Get job embedding
        job_embedding: Optional[np.ndarray] = None

        if job_id:
            # Try to get cached embedding
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(
                "SELECT embedding, title, description FROM job_embeddings WHERE job_id = ?",
                (job_id,)
            )
            row = cursor.fetchone()
            conn.close()

            if row:
                job_embedding = self._deserialize_embedding(row[0])
                logger.info(f"Using cached embedding for job {job_id}")

        # Generate embedding if not cached
        if job_embedding is None:
            job_text = f"{job_title or ''}. {job_description or ''}"
            job_embedding = self.embedding_generator.generate_embedding(job_text)

        # Get all candidate embeddings
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT candidate_id, name, skills, embedding FROM candidate_embeddings")
        candidates = cursor.fetchall()
        conn.close()

        # Calculate similarities
        results = []
        for candidate_id, name, skills, embedding_blob in candidates:
            candidate_embedding = self._deserialize_embedding(embedding_blob)

            # Calculate cosine similarity
            similarity = self._cosine_similarity(job_embedding, candidate_embedding)

            if similarity >= threshold:
                # Generate match reasons
                match_reasons = self._generate_match_reasons(
                    job_description or '',
                    skills or '',
                    similarity
                )

                results.append(SearchResult(
                    candidate_id=candidate_id,
                    name=name,
                    email=None,  # Not stored in vector DB
                    similarity_score=similarity,
                    match_reasons=match_reasons
                ))

        # Sort by similarity descending
        results.sort(key=lambda x: x.similarity_score, reverse=True)

        return results[:limit]

    def _cosine_similarity(self, a: np.ndarray, b: np.ndarray) -> float:
        """Calculate cosine similarity between two vectors."""
        try:
            return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))
        except:
            return 0.0

    def _generate_match_reasons(
        self,
        job_description: str,
        candidate_skills: str,
        similarity_score: float
    ) -> List[str]:
        """Generate human-readable match reasons."""
        reasons = []

        if similarity_score > 0.8:
            reasons.append("Strong semantic alignment with job requirements")
        elif similarity_score > 0.6:
            reasons.append("Good semantic match to job description")
        else:
            reasons.append("Partial semantic match")

        # Check for skill overlap (simple keyword match)
        if candidate_skills:
            job_lower = job_description.lower()
            skills_list = [s.strip().lower() for s in candidate_skills.split(',')]

            matching_skills = [s for s in skills_list if s in job_lower]
            if matching_skills:
                reasons.append(f"Matches key skills: {', '.join(matching_skills[:3])}")

        return reasons

    def get_candidate_embedding(
        self,
        candidate_id: int
    ) -> Optional[np.ndarray]:
        """Get cached embedding for a candidate."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT embedding FROM candidate_embeddings WHERE candidate_id = ?",
            (candidate_id,)
        )
        row = cursor.fetchone()
        conn.close()

        if row:
            return self._deserialize_embedding(row[0])
        return None

    def batch_index_candidates(
        self,
        candidates: List[Dict[str, Any]]
    ) -> int:
        """
        Batch index multiple candidates.

        Args:
            candidates: List of candidate dictionaries

        Returns:
            Number of candidates indexed
        """
        indexed = 0
        for candidate in candidates:
            try:
                if self.index_candidate(
                    candidate_id=candidate.get('id'),
                    name=candidate.get('name'),
                    skills=candidate.get('skills'),
                    resume_text=candidate.get('resume_text')
                ):
                    indexed += 1
            except Exception as e:
                logger.error(f"Failed to index candidate {candidate.get('id')}: {e}")

        logger.info(f"Batch indexed {indexed}/{len(candidates)} candidates")
        return indexed

    def clear_job_embeddings(self, job_id: Optional[int] = None) -> int:
        """Clear embeddings for a specific job or all jobs."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        if job_id:
            cursor.execute("DELETE FROM job_embeddings WHERE job_id = ?", (job_id,))
        else:
            cursor.execute("DELETE FROM job_embeddings")

        deleted = cursor.rowcount
        conn.commit()
        conn.close()

        return deleted


# Singleton instance
semantic_search = SemanticSearchEngine()
