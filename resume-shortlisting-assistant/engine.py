import os
from io import BytesIO
from pypdf import PdfReader
from pydantic import BaseModel, Field
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from dotenv import load_dotenv

load_dotenv()

# Pydantic Schemas for Structured Output
class EvaluationScore(BaseModel):
    score: int = Field(description="Score out of 100 for this dimension")
    explanation: str = Field(description="Detailed explanation justifying the score. Explain 'Why' the candidate received this score based on their resume compared to the JD.")

class CandidateEvaluation(BaseModel):
    exact_match: EvaluationScore = Field(description="Score based on direct keyword and skill matches between the resume and JD.")
    similarity_match: EvaluationScore = Field(description="Score based on related skills/frameworks and domain knowledge (e.g. AWS Kinesis mapping to Kafka).")
    achievement_impact: EvaluationScore = Field(description="Score measuring quantifiable results, business impact, and achievements.")
    ownership: EvaluationScore = Field(description="Score assessing leadership, architecture design, and end-to-end responsibility.")
    tier: str = Field(description="Candidate classification Tier: 'Tier A' (Fast-track), 'Tier B' (Technical Screen), or 'Tier C' (Needs Evaluation).")
    summary: str = Field(description="A concise summary of the candidate's overall fit for the role.")

class JobPostGeneration(BaseModel):
    description: str = Field(description="Comprehensive job description with responsibilities, qualifications, and requirements")
    requirements: str = Field(description="Key technical skills and qualifications required for the role")

def extract_text_from_pdf(pdf_file: BytesIO) -> str:
    """Extracts text from a loaded PDF BytesIO object."""
    try:
        reader = PdfReader(pdf_file)
        text = ""
        for page in reader.pages:
            extracted_text = page.extract_text()
            if extracted_text:
                text += extracted_text + "\n"
        return text.strip()
    except Exception as e:
        raise ValueError(f"Failed to parse PDF: {str(e)}")

def evaluate_resume(resume_text: str, jd_text: str) -> CandidateEvaluation:
    """Evaluates a resume against a job description using Groq LLM."""

    # Get API key from environment
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY environment variable is not set. Please set it in your .env file.")

    # Initialize the Groq model
    llm = ChatGroq(
        model="openai/gpt-oss-120b",
        temperature=0.0,
        max_tokens=2048,
        api_key=api_key
    )
    
    # Force the LLM to output the structured CandidateEvaluation schema
    structured_llm = llm.with_structured_output(CandidateEvaluation)
    
    # Create the prompt template
    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are an expert technical recruiter and hiring manager. 
Your task is to evaluate a candidate's resume against a job description (JD).
You must provide rigorous, multi-dimensional scores (0-100) and detailed explanations.

Scoring Guidelines:
1. Exact Match: Direct occurrences of required skills & tools.
2. Similarity Match: Semantic understanding of related tech (e.g., if JD asks for Kafka, but candidate has RabbitMQ or AWS Kinesis, give high similarity. If JD asks for React, and candidate has Vue/Angular, give moderate/high similarity based on context).
3. Achievement/Impact: Look for numbers, percentages, optimization times, and revenue impact. If absent, score low.
4. Ownership: Look for keywords like 'led', 'architected', 'designed', 'mentored', 'end-to-end'.

Tier Classification:
- Tier A (Fast-track): Overall strong fit, high scores across the board.
- Tier B (Technical Screen): Good match but might have gaps in some areas.
- Tier C (Needs Evaluation): Weak match, missing core skills and no related experience.

Be very objective and critical."""),
        ("human", "Job Description:\n{jd_text}\n\nCandidate Resume:\n{resume_text}")
    ])
    
    # Chain the prompt and the structured LLM
    chain = prompt | structured_llm
    
    # Execute the evaluation
    result = chain.invoke({"jd_text": jd_text, "resume_text": resume_text})

    return result

def generate_job_post(title: str, location: str = None, additional_info: str = None) -> dict:
    """Generate a comprehensive job post using AI based on job title and optional details."""

    # Get API key from environment
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY environment variable is not set. Please set it in your .env file.")

    # Initialize the Groq model
    llm = ChatGroq(
        model="openai/gpt-oss-120b",
        temperature=0.3,
        max_tokens=2048,
        api_key=api_key
    )

    # Force the LLM to output the structured JobPostGeneration schema
    structured_llm = llm.with_structured_output(JobPostGeneration)

    # Build the additional context
    context = ""
    if location:
        context += f"\nLocation: {location}"
    if additional_info:
        context += f"\nAdditional Information: {additional_info}"

    # Create the prompt template
    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are an expert technical recruiter and job description writer.
Your task is to create a comprehensive, professional job posting based on the job title.

The job description should include:
1. A compelling introduction about the role and company
2. Key responsibilities and day-to-day activities
3. Required qualifications and technical skills
4. Preferred qualifications (nice-to-have skills)
5. Information about company culture and growth opportunities

Make the description detailed enough to attract qualified candidates while being specific about requirements.
Use professional language and format with clear sections."""),
        ("human", "Job Title: {title}{context}\n\nGenerate a comprehensive job posting for this position.")
    ])

    # Chain the prompt and the structured LLM
    chain = prompt | structured_llm

    # Execute the generation
    result = chain.invoke({"title": title, "context": context})

    return {
        "description": result.description,
        "requirements": result.requirements
    }
