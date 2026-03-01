"""
Resume Parser Module
Extracts structured information from resume text using Groq AI
"""

import os
from groq import Groq
from typing import Dict, Optional
import json
import re

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def extract_candidate_info(resume_text: str) -> Dict:
    """
    Extract structured information from resume text

    Args:
        resume_text: Raw text extracted from PDF resume

    Returns:
        Dictionary with extracted candidate information
    """

    prompt = f"""You are a resume parser. Extract the following information from this resume and return ONLY valid JSON:

Resume Text:
{resume_text}

Extract and return JSON with these exact keys:
{{
    "name": "full name (first and last)",
    "email": "email address",
    "phone": "phone number",
    "location": "city, state/country",
    "skills": "comma-separated list of technical skills",
    "education": "highest degree and institution",
    "experience_years": "total years of experience (number only)",
    "current_role": "current job title"
}}

Rules:
- Return ONLY the JSON object, nothing else
- If information is not found, use null for that field
- For phone, format as +XX XXXXXXXXXX
- Extract the most recent/current role
- List key technical skills only

Return the JSON:"""

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "You are a precise resume data extractor. Return only valid JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,
            max_tokens=1000,
            response_format={"type": "json_object"}
        )

        result = response.choices[0].message.content
        extracted_data = json.loads(result)

        # Validate and clean data
        cleaned_data = {
            "name": extract_name(resume_text) or extracted_data.get("name"),
            "email": extract_email(resume_text) or extracted_data.get("email"),
            "phone": extract_phone(resume_text) or extracted_data.get("phone"),
            "location": extracted_data.get("location"),
            "skills": extracted_data.get("skills"),
            "education": extracted_data.get("education"),
            "experience_years": extracted_data.get("experience_years"),
            "current_role": extracted_data.get("current_role")
        }

        return cleaned_data

    except Exception as e:
        print(f"Error extracting candidate info: {e}")
        # Fallback to regex extraction
        return {
            "name": extract_name(resume_text),
            "email": extract_email(resume_text),
            "phone": extract_phone(resume_text),
            "location": None,
            "skills": None,
            "education": None,
            "experience_years": None,
            "current_role": None
        }


def extract_name(text: str) -> Optional[str]:
    """Extract name from resume using regex patterns"""
    lines = text.split('\n')

    # Common patterns for resume headers
    # First non-empty line that's not too long and looks like a name
    for line in lines[:10]:
        line = line.strip()
        if line and len(line.split()) >= 2 and len(line) < 50:
            # Check if it looks like a name (contains letters and spaces, maybe periods)
            if re.match(r'^[A-Z][a-zA-Z\s\.]+$', line):
                return line

    # Try to find name in email's local part
    email = extract_email(text)
    if email:
        local_part = email.split('@')[0]
        # Remove numbers and special characters, capitalize
        name = re.sub(r'[0-9\._]', ' ', local_part).strip().title()
        if len(name.split()) >= 2:
            return name

    return None


def extract_email(text: str) -> Optional[str]:
    """Extract email from resume using regex"""
    # Common email pattern
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    matches = re.findall(email_pattern, text)

    # Return the first valid-looking email
    for email in matches:
        if not email.startswith('.'):  # Skip invalid emails
            return email

    return None


def extract_phone(text: str) -> Optional[str]:
    """Extract phone number from resume using regex"""
    # Multiple phone number patterns
    patterns = [
        r'\+?\d{1,3}[-.\s]?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}',  # +1 (123) 456-7890
        r'\+?\d{1,3}[-.\s]?\d{3}[-.\s]?\d{3}[-.\s]?\d{4}',      # +1 123 456 7890
        r'\d{10}',                                                  # 1234567890
    ]

    for pattern in patterns:
        matches = re.findall(pattern, text)
        if matches:
            phone = matches[0]
            # Clean up the phone number
            phone = re.sub(r'[^\d+]', '', phone)
            if len(phone.replace('+', '')) >= 10:
                return phone

    return None


def extract_skills(text: str) -> Optional[str]:
    """Extract technical skills from resume"""
    # Common tech skills to look for
    skill_keywords = [
        'Python', 'Java', 'JavaScript', 'TypeScript', 'React', 'Node.js',
        'Next.js', 'Django', 'Flask', 'FastAPI', 'Spring Boot', 'AWS',
        'Docker', 'Kubernetes', 'PostgreSQL', 'MongoDB', 'Redis',
        'Git', 'CI/CD', 'REST API', 'GraphQL', 'Microservices',
        'Machine Learning', 'AI', 'Data Science', 'DevOps'
    ]

    found_skills = []
    for skill in skill_keywords:
        if skill.lower() in text.lower():
            found_skills.append(skill)

    return ', '.join(found_skills) if found_skills else None


def extract_location(text: str) -> Optional[str]:
    """Extract location from resume"""
    # Look for common location patterns
    patterns = [
        r'(?:Location|Address|Based in|Located in)[:\s]*([A-Z][a-zA-Z\s,]+(?:?:India|USA|UK|CA|NY|TX|CA))',
        r'([A-Z][a-zA-Z\s]+),\s*(?:India|USA|United States|UK|California|New York|Texas)'
    ]

    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1).strip()

    return None


if __name__ == "__main__":
    # Test with sample resume text
    sample_resume = """
    SHUBHAM KUMAR
    (+91) 6201060889 | shubham.kumar.min21@itbhu.ac.in
    Github: https://github.com/shubham21155102

    EDUCATION
    Indian Institute of Technology (BHU) Varanasi 2021 - 2025

    SKILLS
    Python, JavaScript, TypeScript, React, Node.js, AWS, Docker
    """

    result = extract_candidate_info(sample_resume)
    print(json.dumps(result, indent=2))
