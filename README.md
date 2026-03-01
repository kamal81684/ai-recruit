# AI Resume Shortlisting Assistant

An AI-powered resume evaluation system that compares candidate resumes against job descriptions and provides multi-dimensional scoring with explainability using Llama 3 via Groq API.

## 🖼️ Screenshots

### Home Page - Resume Upload Form
![Home Page](screenshots/home.png)

### Resume Upload with Job Description
![Upload Form Filled](screenshots/resume-upload-filled.png)

### Candidates Dashboard
![Candidates Dashboard](screenshots/candidates.png)

### Evaluation Results - Summary & Tier
![Results Summary](screenshots/results-summary.png)

### Evaluation Results - Multi-dimensional Scores
![Results Scores](screenshots/results-scores.png)

### Candidate Profile - Full Details
![Candidate Profile](screenshots/candidate-profile.png)

## 🎯 Features

## Project Structure

```
kamal-assignment/
├── resume-shortlisting-assistant/    # Backend (Python)
│   ├── app.py                        # Streamlit frontend
│   ├── api.py                        # Flask REST API server
│   ├── engine.py                     # Core evaluation logic
│   ├── requirements.txt              # Python dependencies
│   └── venv/                         # Python virtual environment
│
├── frontend/                         # Frontend (Next.js)
│   ├── app/                          # Next.js app directory
│   │   ├── page.tsx                  # Main application page
│   │   └── layout.tsx                # Root layout
│   ├── package.json                  # Node.js dependencies
│   └── README.md                     # Frontend documentation
│
├── start.sh                          # Quick start script
└── README.md                         # This file
```

## Features

- **Multi-dimensional Scoring (0-100):**
  - Exact Match: Direct keyword and skill matches
  - Similarity Match: Semantic understanding of related technologies
  - Achievement/Impact: Measuring quantifiable results
  - Ownership: Assessing leadership and responsibilities

- **Tier Classification:**
  - Tier A: Fast-track hire
  - Tier B: Technical screen recommended
  - Tier C: Needs further evaluation

- **Explainability:** Detailed explanations for every score

## 🐳 Docker Deployment

### Using Docker Compose (Recommended)

**Quick start:**
```bash
docker-compose up -d
```

This will start both the backend and frontend containers.

**Access the application:**
- Frontend: http://localhost:3000
- Backend API: http://localhost:5001

**Stop the containers:**
```bash
docker-compose down
```

### Manual Docker Build

**Backend:**
```bash
cd resume-shortlisting-assistant
docker build -t ai-recruit-backend .
docker run -p 5001:5001 \
  -e GROQ_API_KEY=your_key_here \
  -e DATABASE_URL=your_db_url \
  ai-recruit-backend
```

**Frontend:**
```bash
cd frontend
docker build -t ai-recruit-frontend .
docker run -p 3000:3000 ai-recruit-frontend
```

### GitHub Container Registry

Images are automatically built and pushed to GitHub Container Registry:

- **Backend:** `ghcr.io/kamal81684/ai-recruit-backend:latest`
- **Frontend:** `ghcr.io/kamal81684/ai-recruit-frontend:latest`

**Pull and run:**
```bash
# Pull images
docker pull ghcr.io/kamal81684/ai-recruit-backend:latest
docker pull ghcr.io/kamal81684/ai-recruit-frontend:latest

# Run with Docker Compose
docker-compose up -d
```

### CI/CD Pipeline

GitHub Actions automatically:
1. Runs tests on every push
2. Builds Docker images for multiple architectures (amd64, arm64)
3. Pushes to GitHub Container Registry
4. Triggers on push to `main` branch

See `.github/workflows/` for pipeline configurations.

## Quick Start

### Option 1: Using Test Script (Verify Integration First)

```bash
./test-integration.sh
```

This will check if:
- Flask backend is running
- Next.js frontend is configured
- API connection is working

### Option 2: Manual Setup

#### Step 1 - Start Flask Backend

```bash
cd resume-shortlisting-assistant
source venv/bin/activate
python api.py
```

Backend runs on: **http://localhost:5001**

#### Step 2 - Start Next.js Frontend (in new terminal)

```bash
cd frontend
npm install
npm run dev
```

Frontend runs on: **http://localhost:3000**

#### Step 3 - Open Your Browser

Navigate to **http://localhost:3000**

You should see:
- A green "Backend Connected" status indicator
- The AI Resume Shortlisting Assistant interface

### Option 3: Streamlit Frontend (Original)

```bash
cd resume-shortlisting-assistant
source venv/bin/activate
streamlit run app.py
```

Open [http://localhost:8501](http://localhost:8501)

## Prerequisites

- Python 3.9+
- Node.js 18+
- Groq API Key (get free at [console.groq.com](https://console.groq.com))

## Environment Setup

1. **Set up Python backend:**
   ```bash
   cd resume-shortlisting-assistant
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Configure API Key:**
   ```bash
   # Create .env file
   echo "GROQ_API_KEY=your_api_key_here" > .env
   ```

3. **Set up Next.js frontend:**
   ```bash
   cd frontend
   npm install
   ```

## Tech Stack

| Component | Technology |
|-----------|------------|
| Frontend | Next.js 15, React, TypeScript, Tailwind CSS |
| Backend API | Flask, Python 3.9+ |
| AI/LLM | Groq (Llama 3 70B) |
| PDF Parsing | pypdf |
| Structured Output | Pydantic |
| Prompt Management | LangChain |

## Architecture

```
┌─────────────────┐         ┌──────────────────────┐         ┌─────────────────┐
│  Next.js App    │────────▶│  Flask API Server    │────────▶│  Groq LLM API   │
│  (port 3000)    │  HTTP   │  (port 5001)         │         │                 │
└─────────────────┘         └──────────────────────┘         └─────────────────┘
       Frontend                    Backend                         AI
```

## API Endpoints

### Flask API Server (port 5001)

- `GET /health` - Health check
- `POST /api/evaluate` - Evaluate a resume

**Request:**
```
POST /api/evaluate
Content-Type: multipart/form-data

{
  "jobDescription": "string",
  "resume": "file (PDF)"
}
```

**Response:**
```json
{
  "tier": "Tier A",
  "summary": "...",
  "exact_match": { "score": 85, "explanation": "..." },
  "similarity_match": { "score": 78, "explanation": "..." },
  "achievement_impact": { "score": 72, "explanation": "..." },
  "ownership": { "score": 80, "explanation": "..." }
}
```

## Development

### Running Tests

```bash
cd resume-shortlisting-assistant
python test_engine.py
```

### Adding New Features

1. Modify `engine.py` for evaluation logic changes
2. Modify `api.py` for API changes
3. Modify `frontend/app/page.tsx` for UI changes

## Troubleshooting

**Flask API not responding:**
- Ensure the venv is activated
- Check that port 5001 is not in use
- Verify GROQ_API_KEY is set

**Next.js build errors:**
- Run `npm install` to ensure dependencies are installed
- Clear Next.js cache: `rm -rf .next`

**Streamlit issues:**
- Update streamlit: `pip install --upgrade streamlit`
- Clear cache: `rm -rf .streamlit`

## License

MIT
