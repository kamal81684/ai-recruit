import os
import json
from engine import evaluate_resume

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--jd", type=str, required=True, help="Job description text")
    parser.add_argument("--resume", type=str, required=True, help="Resume text")
    args = parser.parse_args()

    # Make sure we have the groq API key
    if not os.getenv("GROQ_API_KEY"):
        print("Error: GROQ_API_KEY is not set.")
        exit(1)

    try:
        print("Evaluating...")
        res = evaluate_resume(args.resume, args.jd)
        print("\nEvaluation Successful!")
        print(f"Tier: {res.tier}")
        print(f"Summary: {res.summary}")
        print("\n=== Scores ===")
        print(f"Exact Match: {res.exact_match.score} - {res.exact_match.explanation}")
        print(f"Similarity: {res.similarity_match.score} - {res.similarity_match.explanation}")
        print(f"Achievement: {res.achievement_impact.score} - {res.achievement_impact.explanation}")
        print(f"Ownership: {res.ownership.score} - {res.ownership.explanation}")
    except Exception as e:
        print(f"Failed: {e}")
