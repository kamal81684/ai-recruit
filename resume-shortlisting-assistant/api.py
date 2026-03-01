"""
Flask API server for AI Resume Shortlisting Assistant
This server provides REST API endpoints that the Next.js frontend can call.
"""

from flask import Flask, request, jsonify, make_response
from flask_cors import CORS
from engine import extract_text_from_pdf, evaluate_resume, generate_job_post
from database import db, init_database
from resume_parser import extract_candidate_info
import os
import psycopg2.extras
from io import BytesIO

app = Flask(__name__)

# Configure CORS for Next.js frontend - Allow specific origins
CORS(app, resources={r"/*": {"origins": ["http://localhost:3000", "https://ai-recruit-two.vercel.app"]}})

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

        # Check API key
        if not os.getenv('GROQ_API_KEY'):
            return jsonify({'error': 'GROQ_API_KEY environment variable is missing'}), 500

        # Check file type
        if not resume_file.filename.endswith('.pdf'):
            return jsonify({'error': 'Only PDF files are supported'}), 400

        # Convert file to BytesIO for processing
        pdf_bytes = BytesIO(resume_file.read())

        # Extract text from PDF
        resume_text = extract_text_from_pdf(pdf_bytes)

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
def generate_interview_questions(candidate_id):
    """
    Generate AI-powered interview questions for a candidate.
    This will replace any existing questions for this candidate.
    """
    try:
        # Check API key
        if not os.getenv('GROQ_API_KEY'):
            return jsonify({'error': 'GROQ_API_KEY environment variable is missing'}), 500

        # Get candidate data
        candidate = db.get_candidate_by_id(candidate_id)
        if not candidate:
            return jsonify({'error': 'Candidate not found'}), 404

        # Delete existing questions
        db.delete_interview_questions(candidate_id)

        # Generate AI questions based on candidate's profile and job description
        from groq import Groq
        import json

        client = Groq(api_key=os.getenv('GROQ_API_KEY'))

        prompt = f"""You are an expert technical interviewer. Based on the following candidate profile and job description, generate 8-10 targeted interview questions.

CANDIDATE PROFILE:
Name: {candidate.get('name', 'Unknown')}
Current Role: {candidate.get('current_role', 'Unknown')}
Skills: {candidate.get('skills', 'Not specified')}
Experience: {candidate.get('experience_years', 'Unknown')} years
Education: {candidate.get('education', 'Not specified')}

JOB DESCRIPTION:
{candidate.get('job_description', 'Not specified')[:1000]}

CANDIDATE TIER: {candidate.get('tier', 'Unknown')}
EVALUATION SUMMARY: {candidate.get('summary', '')[:500]}

Generate questions that:
1. Test technical depth in their claimed skills
2. Explore their achievements and impact mentioned in the resume
3. Assess cultural fit and soft skills
4. Include both behavioral and technical questions
5. Are tailored to their tier level (harder questions for Tier A, foundational for Tier C)

Return ONLY a valid JSON array with this exact structure:
[
  {{"question": "question text here", "category": "Technical|Behavioral|Cultural"}}
]

Ensure the JSON is valid and properly formatted."""

        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert technical interviewer. Always respond with valid JSON only."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            model="llama-3.3-70b-versatile",
            temperature=0.5,
            max_tokens=2048,
            response_format={"type": "json_object"}
        )

        response_text = chat_completion.choices[0].message.content

        # Parse the response
        try:
            questions_data = json.loads(response_text)

            # Handle different response formats
            if isinstance(questions_data, list):
                questions_list = questions_data
            elif isinstance(questions_data, dict) and 'questions' in questions_data:
                questions_list = questions_data['questions']
            else:
                questions_list = []

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

        except json.JSONDecodeError as e:
            print(f"JSON decode error: {e}")
            print(f"Response text: {response_text}")
            # Fallback: create generic questions
            fallback_questions = [
                {"question": "Can you walk me through your most challenging technical project?", "category": "Technical"},
                {"question": "Describe a time you had to learn a new technology quickly. How did you approach it?", "category": "Behavioral"},
                {"question": "What do you consider your biggest professional achievement?", "category": "Behavioral"},
                {"question": "How do you handle disagreements with team members on technical decisions?", "category": "Cultural"},
            ]
            for q in fallback_questions:
                question_id = db.save_interview_question(candidate_id, q['question'], q['category'])
                q['id'] = question_id
                q['candidate_id'] = candidate_id
                q['created_at'] = None

            return jsonify({'questions': fallback_questions}), 200

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

        # Check API key
        if not os.getenv('GROQ_API_KEY'):
            return jsonify({'error': 'GROQ_API_KEY environment variable is missing'}), 500

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

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5001))
    debug = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    app.run(host='0.0.0.0', port=port, debug=debug)
