"""
Flask API server for AI Resume Shortlisting Assistant
This server provides REST API endpoints that the Next.js frontend can call.
"""

from flask import Flask, request, jsonify, make_response
from flask_cors import CORS
from engine import extract_text_from_pdf, evaluate_resume
from database import db, init_database
from resume_parser import extract_candidate_info
import os
from io import BytesIO

app = Flask(__name__)

# Configure CORS for Next.js frontend - Simple setup
CORS(app,
     resources={r"/api/*": {"origins": "*"}},
     methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
     allow_headers=["Content-Type", "Authorization", "Cache-Control"],
     supports_credentials=True,
     max_age=86400)

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

@app.route('/api/statistics', methods=['GET'])
def get_statistics():
    """Get database statistics"""
    try:
        stats = db.get_statistics()
        return jsonify(stats), 200

    except Exception as e:
        return jsonify({'error': f'Failed to fetch statistics: {str(e)}'}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5001))
    debug = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    app.run(host='0.0.0.0', port=port, debug=debug)
