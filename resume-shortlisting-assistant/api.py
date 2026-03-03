"""
Flask API server for AI Resume Shortlisting Assistant
This server provides REST API endpoints that the Next.js frontend can call.

Architecture improvements:
- Configuration managed through centralized config module
- Provider-agnostic LLM interactions
- Global exception handling with standardized error responses
- Request ID tracking for debugging
- Input validation with Pydantic models
- Phase 3: Retry mechanisms with exponential backoff
- Phase 3: Dead Letter Queue for failed requests
- Phase 3: Input sanitization for prompt injection protection

Contributor: shubham21155102
"""

from flask import Flask, request, jsonify, make_response
from flask_cors import CORS
from engine import extract_text_from_pdf, evaluate_resume, generate_job_post
from rate_limiter import rate_limit, ENDPOINT_LIMITS
from database import db, init_database
from resume_parser import extract_candidate_info
from config import get_config
from error_handlers import (
    register_error_handlers,
    init_request_tracking,
    ValidationError,
    NotFoundError,
    ConfigurationError,
    FileProcessingError,
    get_request_id
)
import os
import psycopg2.extras
from io import BytesIO
import logging

# Import input sanitization module (Phase 3)
try:
    from input_sanitizer import (
        sanitize_job_description,
        sanitize_resume_text,
        sanitize_additional_info
    )
    SANITIZATION_ENABLED = True
except ImportError:
    SANITIZATION_ENABLED = False
    logger = logging.getLogger(__name__)
    logger.warning("Input sanitization module not available, running without sanitization checks")

app = Flask(__name__)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load configuration
try:
    config = get_config()
    # Configure CORS using centralized config
    CORS(app, resources={r"/*": {"origins": config.cors_origins}})
except Exception as e:
    logger.warning(f"Warning: Could not load configuration: {e}")
    # Fallback to default origins
    CORS(app, resources={r"/*": {"origins": ["http://localhost:3000", "https://ai-recruit-two.vercel.app"]}})

# Register error handlers and request tracking
register_error_handlers(app)
init_request_tracking(app)

# Add cache control headers to all responses
@app.after_request
def add_headers(response):
    # Prevent caching for all API responses
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

# Initialize database on startup
if not init_database():
    print("⚠️ Warning: Database initialization failed. API will run without database.")

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'ok', 'message': 'API is running'})

@app.route('/api/evaluate', methods=['POST'])
@rate_limit(requests=10, window=60)  # 10 evaluations per minute
def evaluate_candidate():
    """
    Evaluate a candidate's resume against a job description.

    Expected form data:
    - jobDescription: string
    - resume: file (PDF)
    """
    try:
        # Get form data
        job_description = request.form.get('jobDescription')
        resume_file = request.files.get('resume')

        # Validate input
        if not job_description:
            return jsonify({'error': 'Job description is required'}), 400

        if not resume_file:
            return jsonify({'error': 'Resume file is required'}), 400

        # Check API key using centralized config
        try:
            config = get_config()
            if not config.llm.api_key:
                return jsonify({'error': f'{config.llm_provider.upper()}_API_KEY environment variable is missing'}), 500
        except Exception as e:
            return jsonify({'error': f'Configuration error: {str(e)}'}), 500

        # Check file type
        if not resume_file.filename.endswith('.pdf'):
            return jsonify({'error': 'Only PDF files are supported'}), 400

        # Convert file to BytesIO for processing
        pdf_bytes = BytesIO(resume_file.read())

        # Extract text from PDF
        resume_text = extract_text_from_pdf(pdf_bytes)

        # Phase 3: Input sanitization for prompt injection protection
        if SANITIZATION_ENABLED:
            try:
                job_description = sanitize_job_description(job_description)
                resume_text = sanitize_resume_text(resume_text)
                logger.info("Input sanitization completed successfully")
            except ValueError as sanitization_error:
                logger.warning(f"Input sanitization failed: {sanitization_error}")
                return jsonify({
                    'error': f'Input validation failed: {str(sanitization_error)}',
                    'code': 'SANITIZATION_ERROR'
                }), 400

        # Extract candidate information using AI
        print("🔍 Extracting candidate information from resume...")
        extracted_info = extract_candidate_info(resume_text)
        print(f"✅ Extracted info: Name={extracted_info.get('name')}, Email={extracted_info.get('email')}")

        # Evaluate resume
        evaluation = evaluate_resume(resume_text, job_description)

        # Convert Pydantic model to dict
        result = {
            'tier': evaluation.tier,
            'summary': evaluation.summary,
            'exact_match': {
                'score': evaluation.exact_match.score,
                'explanation': evaluation.exact_match.explanation
            },
            'similarity_match': {
                'score': evaluation.similarity_match.score,
                'explanation': evaluation.similarity_match.explanation
            },
            'achievement_impact': {
                'score': evaluation.achievement_impact.score,
                'explanation': evaluation.achievement_impact.explanation
            },
            'ownership': {
                'score': evaluation.ownership.score,
                'explanation': evaluation.ownership.explanation
            },
            'extracted_info': extracted_info  # Include extracted info in response
        }

        # Save to database with extracted info
        candidate_id = db.save_candidate(
            resume_filename=resume_file.filename,
            resume_text=resume_text,
            job_description=job_description,
            evaluation=result,
            extracted_info=extracted_info
        )

        # Add candidate_id to response if saved successfully
        if candidate_id:
            result['candidate_id'] = candidate_id

        return jsonify(result), 200

    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': f'An error occurred during evaluation: {str(e)}'}), 500

@app.route('/api/candidates', methods=['GET'])
def get_candidates():
    """
    Get all candidates with pagination.

    Query params:
    - limit: number of results (default: 50)
    - offset: pagination offset (default: 0)
    - tier: filter by tier (optional)
    """
    try:
        limit = int(request.args.get('limit', 50))
        offset = int(request.args.get('offset', 0))
        tier = request.args.get('tier')

        print(f"\n{'='*60}")
        print(f"🌐 API CALLED: {request.method} {request.path}")
        print(f"📋 Query params: limit={limit}, offset={offset}, tier={tier}")
        print(f"🔗 Headers: {dict(request.headers)}")
        print(f"🌐 Origin: {request.headers.get('Origin')}")
        print(f"🌐 Referer: {request.headers.get('Referer')}")

        if tier:
            candidates = db.get_candidates_by_tier(tier)
        else:
            candidates = db.get_all_candidates(limit=limit, offset=offset)

        print(f"📊 Retrieved {len(candidates)} candidates from DB")
        if candidates:
            print(f"📊 First candidate keys: {candidates[0].keys() if candidates[0] else 'N/A'}")
            print(f"📊 First candidate: {candidates[0]}")

        result = {'candidates': candidates, 'count': len(candidates)}
        print(f"📤 Returning response: {result}")
        print(f"{'='*60}\n")

        response = jsonify(result)
        response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
        return response, 200

    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Failed to fetch candidates: {str(e)}'}), 500

@app.route('/api/candidates/<int:candidate_id>', methods=['GET'])
def get_candidate(candidate_id):
    """Get a specific candidate by ID"""
    try:
        candidate = db.get_candidate_by_id(candidate_id)

        if not candidate:
            return jsonify({'error': 'Candidate not found'}), 404

        return jsonify(candidate), 200

    except Exception as e:
        return jsonify({'error': f'Failed to fetch candidate: {str(e)}'}), 500

@app.route('/api/candidates/<int:candidate_id>', methods=['DELETE'])
def delete_candidate(candidate_id):
    """Delete a candidate by ID"""
    try:
        success = db.delete_candidate(candidate_id)

        if success:
            return jsonify({'message': 'Candidate deleted successfully'}), 200
        else:
            return jsonify({'error': 'Failed to delete candidate'}), 500

    except Exception as e:
        return jsonify({'error': f'Failed to delete candidate: {str(e)}'}), 500

@app.route('/api/candidates/<int:candidate_id>/interview-questions', methods=['GET'])
def get_interview_questions(candidate_id):
    """Get interview questions for a specific candidate"""
    try:
        questions = db.get_interview_questions(candidate_id)
        return jsonify({'questions': questions}), 200

    except Exception as e:
        return jsonify({'error': f'Failed to fetch interview questions: {str(e)}'}), 500

@app.route('/api/candidates/<int:candidate_id>/interview-questions', methods=['POST'])
@rate_limit(requests=10, window=60)  # 10 interview question generations per minute
def generate_interview_questions(candidate_id):
    """
    Generate AI-powered interview questions for a candidate.
    This will replace any existing questions for this candidate.
    """
    try:
        # Check API key using centralized config
        try:
            config = get_config()
            if not config.llm.api_key:
                return jsonify({'error': f'{config.llm_provider.upper()}_API_KEY environment variable is missing'}), 500
        except Exception as e:
            return jsonify({'error': f'Configuration error: {str(e)}'}), 500

        # Get candidate data
        candidate = db.get_candidate_by_id(candidate_id)
        if not candidate:
            return jsonify({'error': 'Candidate not found'}), 404

        # Delete existing questions
        db.delete_interview_questions(candidate_id)

        # Generate AI questions using the provider abstraction
        from llm_providers import get_provider
        import json

        provider = get_provider()
        questions_list = provider.generate_interview_questions(
            candidate_profile=candidate,
            job_description=candidate.get('job_description', 'Not specified'),
            num_questions=10
        )

        # Save questions to database
        saved_questions = []
        for q in questions_list:
            if isinstance(q, dict) and 'question' in q:
                category = q.get('category', 'General')
                question_id = db.save_interview_question(candidate_id, q['question'], category)
                if question_id:
                    saved_questions.append({
                        'id': question_id,
                        'candidate_id': candidate_id,
                        'question': q['question'],
                        'category': category,
                        'created_at': None
                    })

        return jsonify({'questions': saved_questions}), 200

    except Exception as e:
        print(f"Error generating interview questions: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Failed to generate interview questions: {str(e)}'}), 500

@app.route('/api/statistics', methods=['GET'])
def get_statistics():
    """Get database statistics"""
    try:
        stats = db.get_statistics()
        return jsonify(stats), 200

    except Exception as e:
        return jsonify({'error': f'Failed to fetch statistics: {str(e)}'}), 500

@app.route('/api/jobs', methods=['GET'])
def get_job_posts():
    """
    Get all job posts with optional status filter.

    Query params:
    - status: filter by status (optional: 'active', 'inactive', etc.)
    - limit: number of results (default: 50)
    - offset: pagination offset (default: 0)
    """
    try:
        status = request.args.get('status')
        limit = int(request.args.get('limit', 50))
        offset = int(request.args.get('offset', 0))

        job_posts = db.get_all_job_posts(status=status, limit=limit, offset=offset)

        return jsonify({'job_posts': job_posts, 'count': len(job_posts)}), 200

    except Exception as e:
        return jsonify({'error': f'Failed to fetch job posts: {str(e)}'}), 500

@app.route('/api/jobs', methods=['POST'])
def create_job_post():
    """
    Create a new job post.

    Expected JSON body:
    - title: string (required)
    - description: string (required)
    - location: string (optional)
    - requirements: string (optional)
    - status: string (optional, default: 'active')
    """
    try:
        data = request.get_json()

        if not data:
            return jsonify({'error': 'Request body is required'}), 400

        title = data.get('title')
        description = data.get('description')

        if not title or not description:
            return jsonify({'error': 'Title and description are required'}), 400

        location = data.get('location')
        requirements = data.get('requirements')
        status = data.get('status', 'active')

        job_id = db.save_job_post(
            title=title,
            description=description,
            location=location,
            requirements=requirements,
            status=status
        )

        if job_id:
            return jsonify({
                'message': 'Job post created successfully',
                'job_id': job_id
            }), 201
        else:
            return jsonify({'error': 'Failed to create job post'}), 500

    except Exception as e:
        return jsonify({'error': f'Failed to create job post: {str(e)}'}), 500

@app.route('/api/jobs/<int:job_id>', methods=['GET'])
def get_job_post(job_id):
    """Get a specific job post by ID"""
    try:
        job_post = db.get_job_post_by_id(job_id)

        if not job_post:
            return jsonify({'error': 'Job post not found'}), 404

        return jsonify(job_post), 200

    except Exception as e:
        return jsonify({'error': f'Failed to fetch job post: {str(e)}'}), 500

@app.route('/api/jobs/<int:job_id>', methods=['PUT'])
def update_job_post(job_id):
    """
    Update a job post.

    Expected JSON body (all optional):
    - title: string
    - description: string
    - location: string
    - requirements: string
    - status: string
    """
    try:
        data = request.get_json()

        if not data:
            return jsonify({'error': 'Request body is required'}), 400

        title = data.get('title')
        description = data.get('description')
        location = data.get('location')
        requirements = data.get('requirements')
        status = data.get('status')

        success = db.update_job_post(
            job_id=job_id,
            title=title,
            description=description,
            location=location,
            requirements=requirements,
            status=status
        )

        if success:
            return jsonify({'message': 'Job post updated successfully'}), 200
        else:
            return jsonify({'error': 'Failed to update job post or no changes provided'}), 500

    except Exception as e:
        return jsonify({'error': f'Failed to update job post: {str(e)}'}), 500

@app.route('/api/jobs/<int:job_id>', methods=['DELETE'])
def delete_job_post(job_id):
    """Delete a job post by ID"""
    try:
        success = db.delete_job_post(job_id)

        if success:
            return jsonify({'message': 'Job post deleted successfully'}), 200
        else:
            return jsonify({'error': 'Failed to delete job post'}), 500

    except Exception as e:
        return jsonify({'error': f'Failed to delete job post: {str(e)}'}), 500

@app.route('/api/analytics', methods=['GET'])
def get_analytics():
    """Get comprehensive analytics data"""
    try:
        cursor = db.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

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
        candidates_over_time = [(row['date'].strftime('%Y-%m-%d'), row['count']) for row in cursor.fetchall()]

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

        return jsonify({
            'by_tier': by_tier,
            'candidates_over_time': candidates_over_time,
            'active_jobs': active_jobs,
            'avg_scores_by_tier': avg_scores_by_tier,
            'top_locations': top_locations,
            'recent_candidates': recent_candidates,
            'total_candidates': sum(by_tier.values()),
        }), 200

    except Exception as e:
        return jsonify({'error': f'Failed to fetch analytics: {str(e)}'}), 500

@app.route('/api/jobs/generate-ai', methods=['POST'])
@rate_limit(requests=5, window=60)  # 5 job generations per minute
def generate_ai_job_post():
    """
    Generate a job post using AI based on title and optional details.

    Expected JSON body:
    - title: string (required)
    - location: string (optional)
    - additional_info: string (optional) - any extra context for the AI
    """
    try:
        data = request.get_json()

        if not data:
            return jsonify({'error': 'Request body is required'}), 400

        title = data.get('title')

        if not title:
            return jsonify({'error': 'Title is required'}), 400

        location = data.get('location')
        additional_info = data.get('additional_info')

        # Check API key using centralized config
        try:
            config = get_config()
            if not config.llm.api_key:
                return jsonify({'error': f'{config.llm_provider.upper()}_API_KEY environment variable is missing'}), 500
        except Exception as e:
            return jsonify({'error': f'Configuration error: {str(e)}'}), 500

        # Generate job post using AI
        generated = generate_job_post(
            title=title,
            location=location,
            additional_info=additional_info
        )

        return jsonify({
            'description': generated['description'],
            'requirements': generated['requirements']
        }), 200

    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': f'Failed to generate job post: {str(e)}'}), 500

@app.route('/api/analytics/skill-gap', methods=['POST'])
def analyze_skill_gap():
    """
    Analyze skill gaps in the candidate pool for a given job.

    This feature helps hiring managers understand which skills are
    missing from their candidate pool and provides recommendations
    for addressing these gaps.

    Expected JSON body:
    - job_skills: list of strings (required) - skills required for the position
    """
    try:
        data = request.get_json()

        if not data:
            raise ValidationError('Request body is required')

        job_skills = data.get('job_skills')

        if not job_skills or not isinstance(job_skills, list):
            raise ValidationError('job_skills must be a non-empty list')

        if len(job_skills) < 1:
            raise ValidationError('At least one skill is required')

        logger.info(f"Analyzing skill gap for {len(job_skills)} skills")

        cursor = db.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

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
            return jsonify({
                'missing_skills': job_skills,
                'coverage_percentage': 0.0,
                'candidate_count': 0,
                'recommendations': [
                    'No candidates found in database. Start by uploading resumes.',
                ]
            }), 200

        # Analyze skill coverage
        job_skills_lower = [s.lower().strip() for s in job_skills]
        found_skills = set()
        skill_to_candidates = {skill: [] for skill in job_skills_lower}

        for candidate in candidates:
            candidate_skills = candidate.get('skills', '').lower()
            for skill in job_skills_lower:
                # Check if skill is mentioned in candidate's skills
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
        for skill in missing_skills[:3]:  # Limit to top 3
            recommendations.append(
                f"Consider posting job ads on platforms specializing in {skill} talent, "
                f"or reach out to professional communities for this skill."
            )

        return jsonify({
            'missing_skills': missing_skills,
            'coverage_percentage': round(coverage_percentage, 1),
            'candidate_count': len(candidates),
            'found_skills': list(found_skills),
            'recommendations': recommendations
        }), 200

    except ValidationError as e:
        raise e
    except Exception as e:
        logger.error(f"Failed to analyze skill gap: {e}")
        raise

@app.route('/api/candidates/ranking', methods=['GET'])
def get_candidates_ranking():
    """
    Get candidates ranked by their match score (leaderboard).

    Query params:
    - limit: number of results (default: 20)
    - tier: filter by tier (optional)
    - sort_by: sorting method (default: 'overall_score')
      Options: 'overall_score', 'exact_match', 'similarity_match', 'achievement_impact', 'ownership'
    - order: sort order (default: 'desc')
      Options: 'asc', 'desc'

    Returns a ranked list of candidates with their positions and scores.
    """
    try:
        limit = int(request.args.get('limit', 20))
        tier = request.args.get('tier')
        sort_by = request.args.get('sort_by', 'overall_score')
        order = request.args.get('order', 'desc')

        # Validate sort_by parameter
        valid_sort_options = [
            'overall_score', 'exact_match', 'similarity_match',
            'achievement_impact', 'ownership'
        ]
        if sort_by not in valid_sort_options:
            return jsonify({
                'error': f'Invalid sort_by option. Must be one of: {", ".join(valid_sort_options)}'
            }), 400

        # Validate order parameter
        if order not in ['asc', 'desc']:
            return jsonify({'error': 'Invalid order option. Must be "asc" or "desc"'}), 400

        # Get candidates with their scores
        cursor = db.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

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

        if tier:
            base_query += " WHERE tier = %s"
            params.append(tier)

        # Execute query
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
            # Filter out any None or invalid values
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
        reverse = (order == 'desc')
        ranked_candidates.sort(key=lambda x: x.get(sort_by, 0), reverse=reverse)

        # Apply limit
        ranked_candidates = ranked_candidates[:limit]

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

        return jsonify({
            'ranked_candidates': ranked_candidates,
            'count': len(ranked_candidates),
            'statistics': avg_scores,
            'filters': {
                'tier': tier,
                'sort_by': sort_by,
                'order': order
            }
        }), 200

    except Exception as e:
        logger.error(f"Failed to get candidates ranking: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Failed to get candidates ranking: {str(e)}'}), 500

@app.route('/api/resume/rewrite', methods=['POST'])
@rate_limit(requests=5, window=60)  # 5 rewrites per minute
def rewrite_resume():
    """
    Rewrite a resume to better match a job description.

    This endpoint helps candidates optimize their resume for a specific
    job by providing AI-powered suggestions for improvements.

    Expected JSON body:
    - resume_text: string (required) - Original resume text
    - job_description: string (required) - Target job description
    - job_title: string (required) - Target job title
    """
    try:
        data = request.get_json()

        if not data:
            return jsonify({'error': 'Request body is required'}), 400

        resume_text = data.get('resume_text')
        job_description = data.get('job_description')
        job_title = data.get('job_title')

        if not resume_text or not job_description or not job_title:
            return jsonify({
                'error': 'resume_text, job_description, and job_title are required'
            }), 400

        # Check API key using centralized config
        try:
            config = get_config()
            if not config.llm.api_key:
                return jsonify({
                    'error': f'{config.llm_provider.upper()}_API_KEY environment variable is missing'
                }), 500
        except Exception as e:
            return jsonify({'error': f'Configuration error: {str(e)}'}), 500

        # Phase 3: Input sanitization
        if SANITIZATION_ENABLED:
            try:
                job_description = sanitize_job_description(job_description)
                resume_text = sanitize_resume_text(resume_text)
                logger.info("Input sanitization completed successfully for resume rewrite")
            except ValueError as sanitization_error:
                logger.warning(f"Input sanitization failed: {sanitization_error}")
                return jsonify({
                    'error': f'Input validation failed: {str(sanitization_error)}',
                    'code': 'SANITIZATION_ERROR'
                }), 400

        # Generate resume rewrite using the provider abstraction
        from llm_providers import get_provider

        provider = get_provider()
        result = provider.rewrite_resume_for_job(
            resume_text=resume_text,
            job_description=job_description,
            job_title=job_title
        )

        return jsonify({
            'improved_summary': result.get('improved_summary', ''),
            'suggested_bullets': result.get('suggested_bullets', []),
            'skills_to_highlight': result.get('skills_to_highlight', []),
            'keywords_to_add': result.get('keywords_to_add', []),
            'cover_letter_suggestion': result.get('cover_letter_suggestion', '')
        }), 200

    except Exception as e:
        logger.error(f"Error rewriting resume: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Failed to rewrite resume: {str(e)}'}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5001))
    debug = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    app.run(host='0.0.0.0', port=port, debug=debug)
