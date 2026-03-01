#!/usr/bin/env python3
"""
Test script to verify database queries
"""
import os
import sys

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    import psycopg2
    import psycopg2.extras

    print("Connecting to database...")
    conn = psycopg2.connect(
        os.getenv('DATABASE_URL'),
        sslmode='require'
    )
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    print("\n1. Testing get_all_candidates query:")
    cursor.execute("""
        SELECT
            id, name, email, phone, resume_filename, tier, summary,
            exact_match_score, similarity_match_score,
            achievement_impact_score, ownership_score,
            location, skills, education, experience_years, "current_role",
            created_at
        FROM candidates
        ORDER BY created_at DESC
        LIMIT 10 OFFSET 0
    """)

    candidates = cursor.fetchall()
    print(f"Found {len(candidates)} candidates")

    if candidates:
        print(f"\nFirst candidate raw data:")
        first = dict(candidates[0])
        for key, value in first.items():
            print(f"  {key}: {value}")

    print("\n2. Testing get_statistics query:")
    cursor.execute("SELECT COUNT(*) as total FROM candidates")
    total = cursor.fetchone()
    print(f"Statistics result: {dict(total)}")

    cursor.close()
    conn.close()

except ImportError as e:
    print(f"Error: {e}")
    print("Please install psycopg2-binary: pip install psycopg2-binary")
except Exception as e:
    print(f"Database error: {e}")
    import traceback
    traceback.print_exc()
