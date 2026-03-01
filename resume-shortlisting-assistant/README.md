# AI Resume Shortlisting & Interview Assistant System

This project is an AI-powered resume shortlisting and evaluation engine, designed to compare candidate resumes against Job Descriptions (JDs) and provide multi-dimensional scoring with explainability using Large Language Models (LLMs).

This implementation focuses on **Option A: The Evaluation & Scoring Engine (Core)** of the assignment.

## Features

- **PDF Parsing:** Extracts raw unstructured text from candidate resumes uploaded as PDFs.
- **LLM-Powered Evaluation:** Leverages Llama-3 70B via the Groq API for ultra-fast, high-quality reasoning.
- **Multi-dimensional Scoring (0-100):**
  - **Exact Match:** Direct keyword and skill matches.
  - **Similarity Match:** Semantic understanding of related technologies (e.g., considering AWS Kinesis similar to Kafka).
  - **Achievement/Impact:** Measuring quantifiable results and business impact.
  - **Ownership:** Assessing leadership, architectural design, and end-to-end responsibilities.
- **Tier Classification:** Classifies candidates into Tier A (Fast-track), Tier B (Technical Screen), or Tier C (Needs Evaluation).
- **Explainability (The "Why"):** The system doesn't just output a single score; it justifies every score based on explicit evidence from the resume mapped to the JD.
- **Interactive UI:** Built with Streamlit for an intuitive user experience.

## Tech Stack

- **Language:** Python 3.10+
- **AI Framework:** LangChain (`langchain-groq`, `langchain-core`)
- **LLM Provider:** Groq (`llama3-70b-8192`)
- **Data Validation:** Pydantic (Structured Output JSON parsing)
- **PDF Extraction:** PyPDF2
- **UI Framework:** Streamlit
- **API Server:** Flask, Flask-CORS

## Setup Instructions

1. **Clone the Repository:**
   ```bash
   git clone <repo_url>
   cd resume-shortlisting-assistant
   ```

2. **Set up a Virtual Environment (Recommended):**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set Environment Variables:**
   You must have a Groq API Key to run the inference.
   Create a `.env` file in the root directory:
   ```env
   GROQ_API_KEY=your_groq_api_key_here
   ```
   Or export it to your terminal session:
   ```bash
   export GROQ_API_KEY=your_groq_api_key_here
   ```

## Running the Application

### 1. Streamlit UI
To start the interactive web application:
```bash
streamlit run app.py
```
This will open a browser window where you can paste a Job Description and upload a candidate's PDF resume.

### 2. Flask API Server (for Next.js Frontend)
To start the REST API server for the Next.js frontend:
```bash
python api.py
```
The API will run on `http://localhost:5001`

### 3. Command Line Testing
If you want to test the raw evaluation engine without the UI, you can use the test script:
```bash
python test_engine.py --jd "We need a Python developer with Django experience." --resume "I am a backend engineer with 5 years experience in Python and Flask."
```

## Architecture & System Design
Please refer to the `system_design.md` file located in the root directory for a comprehensive overview of the system architecture, data flow, and scaling strategies for handling 10,000+ resumes per day.
