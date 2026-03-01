# AI Resume Shortlisting Assistant - Frontend

This is the **Next.js** frontend for the AI Resume Shortlisting Assistant.

## Integration Status

✅ **Backend Integration Complete**
- Flask API server at `http://localhost:5001`
- Frontend configured to call backend
- Health check status indicator in UI
- Error handling for backend connection issues

## Project Structure

```
kamal-assignment/
├── resume-shortlisting-assistant/  # Backend
│   ├── api.py                     # Flask API server
│   ├── engine.py                  # Core evaluation logic
│   └── requirements.txt           # Python dependencies
│
└── frontend/                       # Next.js frontend (this directory)
    ├── app/
    │   └── page.tsx              # Main UI with API integration
    ├── .env.local                 # Backend URL configuration
    └── package.json
```

## Quick Start

### 1. Start Backend

```bash
cd ../resume-shortlisting-assistant
source venv/bin/activate
python api.py
```

Backend runs on: **http://localhost:5001**

### 2. Start Frontend (in new terminal)

```bash
cd frontend
npm install
npm run dev
```

Frontend runs on: **http://localhost:3000**

### 3. Verify Integration

You should see:
- 🟢 **Green status indicator**: Backend connected
- 🟡 **Yellow status indicator**: Checking backend
- 🔴 **Red status indicator**: Backend disconnected

## Configuration

The backend URL is configured in `.env.local`:

```env
NEXT_PUBLIC_API_URL=http://localhost:5001
```

To use a different backend URL, update this file.

## Architecture

```
┌─────────────────┐         ┌──────────────────────┐         ┌─────────────────┐
│  Next.js App    │────────▶│  Flask API Server    │────────▶│  Groq LLM API   │
│  (port 3000)    │  HTTP   │  (port 5001)         │         │                 │
└─────────────────┘         └──────────────────────┘         └─────────────────┘
       Frontend                    Backend                         AI
```

## Features

- Upload candidate resumes (PDF format)
- Input job descriptions
- AI-powered evaluation across 4 dimensions:
  - Exact Match
  - Similarity Match
  - Achievement/Impact
  - Ownership
- Automatic tier classification (Tier A/B/C)
- Detailed explanations for each score

## Tech Stack

- **Frontend**: Next.js 15, React, TypeScript, Tailwind CSS
- **Backend**: Flask, Python
- **LLM**: Groq (Llama 3 70B)
- **PDF Parsing**: pypdf
- **Structured Output**: Pydantic
