import streamlit as st
from engine import extract_text_from_pdf, evaluate_resume
import os

st.set_page_config(page_title="AI Resume Shortlisting Assistant", page_icon="📄", layout="wide")

st.title("📄 AI Resume Shortlisting & Interview Assistant")
st.markdown("""
Upload a candidate's resume (PDF) and provide the Job Description. The AI will evaluate the candidate 
across four dimensions (Exact Match, Similarity, Achievement, Ownership) and classify them into a Tier.
""")

# Input Form
with st.container():
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("1. Job Description")
        jd_input = st.text_area("Paste the complete Job Description here:", height=300)
        
    with col2:
        st.subheader("2. Candidate Resume")
        resume_pdf = st.file_uploader("Upload Resume (PDF)", type=["pdf"])

    if st.button("Evaluate Candidate", type="primary"):
        if not jd_input or not resume_pdf:
            st.error("Please provide both a Job Description and a Resume.")
        elif not os.getenv("GROQ_API_KEY"):
            st.error("GROQ_API_KEY environment variable is missing. Please set it to proceed.")
        else:
            with st.spinner("Analyzing candidate profile... This may take a few seconds."):
                try:
                    # 1. Parse PDF
                    resume_text = extract_text_from_pdf(resume_pdf)
                    
                    # 2. Evaluate with LLM
                    evaluation = evaluate_resume(resume_text, jd_input)
                    
                    st.success("Analysis Complete!")
                    
                    # 3. Display Results
                    st.markdown("---")
                    st.header("Evaluation Results")
                    
                    # Tier and Summary
                    tier_color = "green" if evaluation.tier == "Tier A" else "orange" if evaluation.tier == "Tier B" else "red"
                    st.markdown(f"### Tier Classification: <span style='color:{tier_color}'>**{evaluation.tier}**</span>", unsafe_allow_html=True)
                    st.info(f"**Summary:** {evaluation.summary}")
                    
                    # Scores
                    st.subheader("Multi-dimensional Scores")
                    
                    # Define columns for metrics
                    m1, m2, m3, m4 = st.columns(4)
                    m1.metric("Exact Match", f"{evaluation.exact_match.score}/100")
                    m2.metric("Similarity Match", f"{evaluation.similarity_match.score}/100")
                    m3.metric("Achievement/Impact", f"{evaluation.achievement_impact.score}/100")
                    m4.metric("Ownership", f"{evaluation.ownership.score}/100")
                    
                    # Detailed Explanations
                    st.subheader("Explainability (The 'Why')")
                    
                    with st.expander("Exact Match Analysis", expanded=True):
                        st.write(evaluation.exact_match.explanation)
                        
                    with st.expander("Semantic Similarity Analysis", expanded=True):
                        st.write(evaluation.similarity_match.explanation)
                        
                    with st.expander("Achievement & Impact Analysis", expanded=True):
                        st.write(evaluation.achievement_impact.explanation)
                        
                    with st.expander("Ownership Analysis", expanded=True):
                        st.write(evaluation.ownership.explanation)

                except Exception as e:
                    st.error(f"An error occurred during evaluation: {str(e)}")
