"""
Unit tests for the resume evaluation engine.

These tests use pytest and mock the Groq API calls to avoid requiring
actual API keys during testing.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from io import BytesIO
from engine import (
    extract_text_from_pdf,
    EvaluationScore,
    CandidateEvaluation,
    evaluate_resume
)


# Mock result for tests
MOCK_EVALUATION_TIER_A = CandidateEvaluation(
    exact_match=EvaluationScore(score=85, explanation="Good match"),
    similarity_match=EvaluationScore(score=75, explanation="Related skills"),
    achievement_impact=EvaluationScore(score=70, explanation="Some achievements"),
    ownership=EvaluationScore(score=80, explanation="Leadership shown"),
    tier="Tier A",
    summary="Strong candidate"
)

MOCK_EVALUATION_TIER_B = CandidateEvaluation(
    exact_match=EvaluationScore(score=60, explanation="Moderate match"),
    similarity_match=EvaluationScore(score=55, explanation="Some related skills"),
    achievement_impact=EvaluationScore(score=50, explanation="Limited achievements"),
    ownership=EvaluationScore(score=45, explanation="Some leadership"),
    tier="Tier B",
    summary="Good candidate for technical screen"
)


class TestExtractTextFromPDF:
    """Tests for PDF text extraction functionality."""

    def test_extract_text_from_valid_pdf(self):
        """Test extracting text from a valid PDF."""
        # Create a mock PDF content
        mock_pdf_content = b"%PDF-1.4\nTest content\n%%EOF"
        pdf_bytes = BytesIO(mock_pdf_content)

        with patch('engine.PdfReader') as mock_reader_class:
            # Setup mock reader
            mock_reader = MagicMock()
            mock_page = MagicMock()
            mock_page.extract_text.return_value = "Sample resume text"
            mock_reader.pages = [mock_page]
            mock_reader_class.return_value = mock_reader

            result = extract_text_from_pdf(pdf_bytes)

            assert result == "Sample resume text"

    def test_extract_text_from_multiple_pages(self):
        """Test extracting text from a multi-page PDF."""
        pdf_bytes = BytesIO(b"%PDF-1.4\n%%EOF")

        with patch('engine.PdfReader') as mock_reader_class:
            mock_reader = MagicMock()
            mock_page1 = MagicMock()
            mock_page1.extract_text.return_value = "Page 1 content"
            mock_page2 = MagicMock()
            mock_page2.extract_text.return_value = "Page 2 content"
            mock_reader.pages = [mock_page1, mock_page2]
            mock_reader_class.return_value = mock_reader

            result = extract_text_from_pdf(pdf_bytes)

            assert result == "Page 1 content\nPage 2 content"

    def test_extract_text_from_pdf_with_empty_page(self):
        """Test extracting text when a page returns None."""
        pdf_bytes = BytesIO(b"%PDF-1.4\n%%EOF")

        with patch('engine.PdfReader') as mock_reader_class:
            mock_reader = MagicMock()
            mock_page1 = MagicMock()
            mock_page1.extract_text.return_value = "Valid content"
            mock_page2 = MagicMock()
            mock_page2.extract_text.return_value = None
            mock_reader.pages = [mock_page1, mock_page2]
            mock_reader_class.return_value = mock_reader

            result = extract_text_from_pdf(pdf_bytes)

            assert result == "Valid content"

    def test_extract_text_from_pdf_raises_error_on_failure(self):
        """Test that PDF parsing errors raise ValueError."""
        pdf_bytes = BytesIO(b"invalid content")

        with patch('engine.PdfReader') as mock_reader_class:
            mock_reader_class.side_effect = Exception("PDF parsing error")

            with pytest.raises(ValueError, match="Failed to parse PDF"):
                extract_text_from_pdf(pdf_bytes)


class TestEvaluateResume:
    """Tests for resume evaluation functionality."""

    def test_evaluate_resume_raises_error_without_api_key(self):
        """Test that evaluate_resume raises ValueError when GROQ_API_KEY is not set."""
        with patch.dict('os.environ', {}, clear=True):
            with pytest.raises(ValueError, match="GROQ_API_KEY environment variable is not set"):
                evaluate_resume("sample resume", "sample jd")

    @patch('engine.ChatPromptTemplate')
    @patch('engine.ChatGroq')
    @patch.dict('os.environ', {'GROQ_API_KEY': 'test-api-key'})
    def test_evaluate_resume_calls_groq_api(self, mock_chat_groq, mock_prompt_template):
        """Test that evaluate_resume properly calls Groq API."""
        # Setup mock LLM
        mock_llm = MagicMock()
        mock_chat_groq.return_value = mock_llm

        # Setup mock structured LLM
        mock_structured_llm = MagicMock()

        # Create a mock chain that returns our result
        mock_chain = MagicMock()
        mock_chain.invoke.return_value = MOCK_EVALUATION_TIER_A

        # The chain is created by: prompt | structured_llm
        # We need to mock the | operator on the prompt
        mock_prompt_instance = MagicMock()
        mock_prompt_instance.__or__.return_value = mock_chain
        mock_prompt_template.from_messages.return_value = mock_prompt_instance

        mock_llm.with_structured_output.return_value = mock_structured_llm

        result = evaluate_resume("resume text", "jd text")

        # Verify the result
        assert result.tier == "Tier A"
        assert result.exact_match.score == 85
        assert result.summary == "Strong candidate"

        # Verify LLM was called with correct parameters
        mock_chat_groq.assert_called_once()
        call_kwargs = mock_chat_groq.call_args.kwargs
        assert call_kwargs['model'] == "openai/gpt-oss-120b"
        assert call_kwargs['temperature'] == 0.0
        assert call_kwargs['api_key'] == 'test-api-key'

    @patch('engine.ChatPromptTemplate')
    @patch('engine.ChatGroq')
    @patch.dict('os.environ', {'GROQ_API_KEY': 'test-api-key'})
    def test_evaluate_resume_tier_b_classification(self, mock_chat_groq, mock_prompt_template):
        """Test evaluation with Tier B classification."""
        # Setup mock LLM
        mock_llm = MagicMock()
        mock_chat_groq.return_value = mock_llm

        # Setup mock structured LLM
        mock_structured_llm = MagicMock()

        # Create a mock chain that returns our result
        mock_chain = MagicMock()
        mock_chain.invoke.return_value = MOCK_EVALUATION_TIER_B

        # Mock the | operator on the prompt
        mock_prompt_instance = MagicMock()
        mock_prompt_instance.__or__.return_value = mock_chain
        mock_prompt_template.from_messages.return_value = mock_prompt_instance

        mock_llm.with_structured_output.return_value = mock_structured_llm

        result = evaluate_resume("resume text", "jd text")

        assert result.tier == "Tier B"
        assert result.exact_match.score == 60


class TestEvaluationScore:
    """Tests for EvaluationScore model."""

    def test_evaluation_score_creation(self):
        """Test creating an EvaluationScore instance."""
        score = EvaluationScore(score=90, explanation="Excellent match")

        assert score.score == 90
        assert score.explanation == "Excellent match"

    def test_evaluation_score_defaults(self):
        """Test EvaluationScore with missing fields."""
        # Pydantic should raise error for missing required fields
        with pytest.raises(Exception):
            EvaluationScore(score=90)


class TestCandidateEvaluation:
    """Tests for CandidateEvaluation model."""

    def test_candidate_evaluation_complete(self):
        """Test creating a complete CandidateEvaluation."""
        evaluation = CandidateEvaluation(
            exact_match=EvaluationScore(score=80, explanation="Good"),
            similarity_match=EvaluationScore(score=70, explanation="Decent"),
            achievement_impact=EvaluationScore(score=75, explanation="Achievements"),
            ownership=EvaluationScore(score=85, explanation="Leadership"),
            tier="Tier A",
            summary="Strong overall"
        )

        assert evaluation.tier == "Tier A"
        assert len(evaluation.summary) > 0
        assert evaluation.exact_match.score == 80

    def test_candidate_evaluation_tier_validation(self):
        """Test that tier values are valid."""
        valid_tiers = ["Tier A", "Tier B", "Tier C"]

        for tier in valid_tiers:
            evaluation = CandidateEvaluation(
                exact_match=EvaluationScore(score=50, explanation="test"),
                similarity_match=EvaluationScore(score=50, explanation="test"),
                achievement_impact=EvaluationScore(score=50, explanation="test"),
                ownership=EvaluationScore(score=50, explanation="test"),
                tier=tier,
                summary="test"
            )
            assert evaluation.tier == tier
