#!/usr/bin/env python3
"""
Check database table structure
"""
import os
import psycopg2
import psycopg2.extras

print("Connecting to database...")
conn = psycopg2.connect(
    os.getenv('DATABASE_URL'),
    sslmode='require'
)
cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

print("\n1. Checking table structure:")
cursor.execute("""
    SELECT column_name, data_type
    FROM information_schema.columns
    WHERE table_name = 'candidates'
    ORDER BY ordinal_position
""")

columns = cursor.fetchall()
print(f"Found {len(columns)} columns:")
for col in columns:
    print(f"  - {col['column_name']}: {col['data_type']}")

print("\n2. Testing direct query:")
cursor.execute("""
    SELECT
        id, name, email, phone, resume_filename, tier, summary,
        exact_match_score, similarity_match_score,
        achievement_impact_score, ownership_score,
        location, skills, education, experience_years, "current_role",
        created_at
    FROM candidates
    LIMIT 1
""")

result = cursor.fetchall()
print(f"Query returned {len(result)} rows")
if result:
    print(f"First row keys: {result[0].keys()}")
    print(f"First row: {dict(result[0])}")

print("\n3. Testing COUNT query:")
cursor.execute("SELECT COUNT(*) as total FROM candidates")
count_result = cursor.fetchone()
print(f"COUNT result: {dict(count_result)}")

cursor.close()
conn.close()
