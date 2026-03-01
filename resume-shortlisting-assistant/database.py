"""
Database module for AI Resume Shortlisting Assistant
Handles PostgreSQL connection and database operations
"""

import os
import psycopg2
import psycopg2.extras
from datetime import datetime
from typing import List, Dict, Optional
import json

class Database:
    """Database connection and operations manager"""

    def __init__(self):
        self.conn = None
        self.cursor = None

    def connect(self):
        """Establish database connection"""
        try:
            self.conn = psycopg2.connect(
                os.getenv('DATABASE_URL'),
                sslmode='require'
            )
            self.cursor = self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            print("✅ Database connected successfully")
            return True
        except Exception as e:
            print(f"❌ Database connection failed: {e}")
            return False

    def close(self):
        """Close database connection"""
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()
        print("Database connection closed")

    def init_tables(self):
        """Initialize database tables"""
        try:
            # Create candidates table
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS candidates (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(255),
                    email VARCHAR(255),
                    phone VARCHAR(50),
                    resume_filename VARCHAR(255),
                    resume_text TEXT,
                    job_description TEXT,
                    tier VARCHAR(10),
                    summary TEXT,
                    exact_match_score INTEGER,
                    exact_match_explanation TEXT,
                    similarity_match_score INTEGER,
                    similarity_match_explanation TEXT,
                    achievement_impact_score INTEGER,
                    achievement_impact_explanation TEXT,
                    ownership_score INTEGER,
                    ownership_explanation TEXT,
                    location VARCHAR(255),
                    skills TEXT,
                    education TEXT,
                    experience_years INTEGER,
                    "current_role" VARCHAR(255),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Create index for faster queries
            self.cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_candidates_tier ON candidates(tier)
            """)
            self.cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_candidates_created_at ON candidates(created_at DESC)
            """)
            self.cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_candidates_email ON candidates(email)
            """)

            self.conn.commit()
            print("✅ Database tables initialized successfully")
            return True
        except Exception as e:
            print(f"❌ Failed to initialize tables: {e}")
            self.conn.rollback()
            return False

    def save_candidate(
        self,
        resume_filename: str,
        resume_text: str,
        job_description: str,
        evaluation: Dict,
        extracted_info: Dict = None
    ) -> Optional[int]:
        """
        Save candidate and evaluation to database

        Args:
            resume_filename: Name of the resume file
            resume_text: Extracted text from resume
            job_description: Job description used for evaluation
            evaluation: Evaluation result dict
            extracted_info: Dict with name, email, phone, location, skills, education, etc.

        Returns:
            candidate_id if successful, None otherwise
        """
        try:
            # Extract info from extracted_info dict
            name = extracted_info.get('name') if extracted_info else None
            email = extracted_info.get('email') if extracted_info else None
            phone = extracted_info.get('phone') if extracted_info else None
            location = extracted_info.get('location') if extracted_info else None
            skills = extracted_info.get('skills') if extracted_info else None
            education = extracted_info.get('education') if extracted_info else None
            experience_years = extracted_info.get('experience_years') if extracted_info else None
            current_role = extracted_info.get('current_role') if extracted_info else None

            self.cursor.execute("""
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
            """, (
                name, email, phone,
                resume_filename, resume_text, job_description,
                evaluation.get('tier'),
                evaluation.get('summary'),
                evaluation.get('exact_match', {}).get('score'),
                evaluation.get('exact_match', {}).get('explanation'),
                evaluation.get('similarity_match', {}).get('score'),
                evaluation.get('similarity_match', {}).get('explanation'),
                evaluation.get('achievement_impact', {}).get('score'),
                evaluation.get('achievement_impact', {}).get('explanation'),
                evaluation.get('ownership', {}).get('score'),
                evaluation.get('ownership', {}).get('explanation'),
                location, skills, education, experience_years, current_role
            ))

            candidate_id = self.cursor.fetchone()['id']
            self.conn.commit()
            print(f"✅ Candidate saved with ID: {candidate_id}")
            return candidate_id

        except Exception as e:
            print(f"❌ Failed to save candidate: {e}")
            self.conn.rollback()
            return None

    def get_all_candidates(self, limit: int = 50, offset: int = 0) -> List[Dict]:
        """Get all candidates with pagination"""
        try:
            # Create a fresh cursor to avoid state issues
            cursor = self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

            cursor.execute("""
                SELECT
                    id, name, email, phone, resume_filename, tier, summary,
                    exact_match_score, similarity_match_score,
                    achievement_impact_score, ownership_score,
                    location, skills, education, experience_years, "current_role",
                    created_at
                FROM candidates
                ORDER BY created_at DESC
                LIMIT %s OFFSET %s
            """, (limit, offset))

            candidates = cursor.fetchall()
            result = [dict(c) for c in candidates]
            cursor.close()
            return result

        except Exception as e:
            print(f"❌ Failed to fetch candidates: {e}")
            return []

    def get_candidate_by_id(self, candidate_id: int) -> Optional[Dict]:
        """Get a specific candidate by ID"""
        try:
            # Create a fresh cursor to avoid state issues
            cursor = self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

            cursor.execute("""
                SELECT
                    id, name, email, phone, resume_filename, resume_text, job_description,
                    tier, summary,
                    exact_match_score, exact_match_explanation,
                    similarity_match_score, similarity_match_explanation,
                    achievement_impact_score, achievement_impact_explanation,
                    ownership_score, ownership_explanation,
                    location, skills, education, experience_years, "current_role",
                    created_at
                FROM candidates WHERE id = %s
            """, (candidate_id,))

            candidate = cursor.fetchone()
            cursor.close()
            return dict(candidate) if candidate else None

        except Exception as e:
            print(f"❌ Failed to fetch candidate: {e}")
            return None

    def get_candidates_by_tier(self, tier: str) -> List[Dict]:
        """Get candidates filtered by tier"""
        try:
            # Create a fresh cursor to avoid state issues
            cursor = self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

            cursor.execute("""
                SELECT
                    id, name, email, phone, resume_filename, tier, summary,
                    exact_match_score, similarity_match_score,
                    achievement_impact_score, ownership_score,
                    location, skills, education, experience_years, "current_role",
                    created_at
                FROM candidates
                WHERE tier = %s
                ORDER BY created_at DESC
            """, (tier,))

            candidates = cursor.fetchall()
            result = [dict(c) for c in candidates]
            cursor.close()
            return result

        except Exception as e:
            print(f"❌ Failed to fetch candidates by tier: {e}")
            return []

    def delete_candidate(self, candidate_id: int) -> bool:
        """Delete a candidate by ID"""
        try:
            self.cursor.execute("DELETE FROM candidates WHERE id = %s", (candidate_id,))
            self.conn.commit()
            print(f"✅ Candidate {candidate_id} deleted")
            return True

        except Exception as e:
            print(f"❌ Failed to delete candidate: {e}")
            self.conn.rollback()
            return False

    def get_statistics(self) -> Dict:
        """Get database statistics"""
        try:
            # Create a fresh cursor to avoid state issues
            cursor = self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

            # Total candidates
            cursor.execute("SELECT COUNT(*) as total FROM candidates")
            total_result = cursor.fetchone()
            if not total_result:
                cursor.close()
                return {'total_candidates': 0, 'by_tier': {}, 'average_scores': {}}
            total = total_result['total']

            # Candidates by tier
            cursor.execute("""
                SELECT tier, COUNT(*) as count
                FROM candidates
                GROUP BY tier
                ORDER BY tier
            """)
            by_tier_results = cursor.fetchall()
            by_tier = {row['tier']: row['count'] for row in by_tier_results if row.get('tier')}

            # Average scores
            cursor.execute("""
                SELECT
                    AVG(exact_match_score) as avg_exact,
                    AVG(similarity_match_score) as avg_similarity,
                    AVG(achievement_impact_score) as avg_impact,
                    AVG(ownership_score) as avg_ownership
                FROM candidates
            """)
            averages = cursor.fetchone()
            cursor.close()

            if not averages:
                return {
                    'total_candidates': total,
                    'by_tier': by_tier,
                    'average_scores': {
                        'exact_match': 0,
                        'similarity_match': 0,
                        'achievement_impact': 0,
                        'ownership': 0,
                    }
                }

            return {
                'total_candidates': total,
                'by_tier': by_tier,
                'average_scores': {
                    'exact_match': round(averages['avg_exact'], 2) if averages.get('avg_exact') else 0,
                    'similarity_match': round(averages['avg_similarity'], 2) if averages.get('avg_similarity') else 0,
                    'achievement_impact': round(averages['avg_impact'], 2) if averages.get('avg_impact') else 0,
                    'ownership': round(averages['avg_ownership'], 2) if averages.get('avg_ownership') else 0,
                }
            }

        except Exception as e:
            print(f"❌ Failed to fetch statistics: {e}")
            import traceback
            traceback.print_exc()
            return {}


# Singleton instance
db = Database()


def init_database():
    """Initialize database connection and tables"""
    if db.connect():
        db.init_tables()
        return True
    return False
