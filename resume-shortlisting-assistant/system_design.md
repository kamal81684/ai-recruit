# AI Resume Shortlisting & Interview Assistant System - Architecture Document

## 1. System Architecture

The system is designed as a modular pipeline encompassing parsing, evaluation, and user interface layers. The core components include:

- **Frontend (Streamlit):** Defines the UI where users (recruiters) can upload resumes (PDF) and the Job Description (text). It displays the extracted candidate information, multi-dimensional scores, tier classification, and explainability metrics.
- **Parser Engine (PyPDF2 / pdfplumber):** Extracts unstructured text from uploaded PDF resumes. It cleans and standardizes the text data before passing it to the AI engine.
- **Evaluation & Scoring Engine (Groq / Llama-3):** Uses LangChain and Pydantic to instruct the LLM to compare the resume text against the Job Description. It outputs structured JSON containing four multi-dimensional scores (Exact Match, Semantic Similarity, Impact/Achievements, Ownership), alongside contextual explanations.
- **Data Strategy Layer:** Converts the unstructured parser output into a clean textual representation and feeds it into the LLM context limits efficiently, ensuring correct extraction of key entities (skills, experiences, education).

## 2. Data Strategy

1. **Ingestion & Extraction:** 
   PDFs are ingested through the Streamlit interface. The `PyPDF2` library extracts raw text. The text is stripped of excessive whitespace and non-ASCII characters to reduce noise.
2. **Structuring Data:**
   Instead of using traditional NLP tools like spaCy for NER, the system leverages the Instruction-Tuning capabilities of LLMs via Groq. A strict output schema is defined using Pydantic (`ResumeEvaluation` model), enforcing the LLM to output valid JSON with specific fields for scores, reasoning, and tiering.
3. **Handling Unstructured to Structured:**
   The prompt engineering strictly requires the LLM to act as an expert technical recruiter, extracting candidate details and mapping them directly to the JD requirements.

## 3. AI Strategy

- **Language Model Provider:** Groq API provides ultra-low latency inference, which is crucial for processing resumes quickly. We will utilize a capable model like `llama3-70b-8192` or `mixtral-8x7b-32768` (depending on max context and availability) for its strong reasoning and JSON formatting capabilities.
- **Semantic Similarity without Embeddings (Prompt-based Reasoning):** 
  To address semantic similarity (e.g., matching AWS Kinesis to Kafka), traditional vector embeddings can be used. However, with the speed of Groq and the contextual power of Llama-3, we instruct the LLM explicitly in the system prompt to "Identify related technologies and semantic matches (e.g., consider AWS Kinesis as a strong similarity match for a Kafka requirement, or React for Vue)." 
  The LLM naturally understands these relationships without needing an external vector database for a single resume vs. single JD comparison.
- **Scoring Breakdown:**
  1. **Exact Match:** Direct keyword and skill matches.
  2. **Similarity Match:** Related skills/frameworks and domain knowledge.
  3. **Achievement / Impact:** Measuring quantifiable results (e.g., "Increased revenue by 20%").
  4. **Ownership:** Assessing leadership, architecture design, and end-to-end responsibility.

## 4. Scalability (10,000+ Resumes / Day)

While the implemented solution handles one resume interactively, scaling to 10,000+ resumes per day requires an event-driven architecture:
1. **Asynchronous Processing:** Resumes uploaded to cloud storage (S3) trigger an event (SQS / Kafka).
2. **Distributed Workers:** Celery or AWS Lambda workers pick up the tasks, parse the PDF, and make asynchronous calls to the Groq API.
3. **Database Integration:** 
   - Store unstructured data and parsed text in a document store (MongoDB / PostgreSQL JSONB).
   - Use **Pinecone / Weaviate** (Vector DB) if semantic search across the entire resume database is required (e.g., "Find all candidates similar to this JD").
4. **Rate Limiting:** Groq API limits must be managed by implementing backoff strategies and grouping batch requests if supported.

---
*Note: This design document aligns with the implementation of **Option A: The Evaluation & Scoring Engine (Core)**.*
