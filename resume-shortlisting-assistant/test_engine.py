"""
Unit tests for the resume evaluation engine.

These tests use pytest and mock the LLM API calls to avoid requiring
actual API keys during testing.

Architecture improvements:
- Tests now mock provider abstraction instead of direct API calls
- Configuration validation is tested
- Provider switching is tested

Contributor: shubham21155102
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from io import BytesIO
from engine import (
    extract_text_from_pdf,
    evaluate_resume,
    generate_job_post
)
from llm_providers import (
    EvaluationScore,
    CandidateEvaluation,
    BaseLLMProvider
)


# =============================================================================
# Mock Provider for Testing
# =============================================================================

class MockLLMProvider(BaseLLMProvider):
    """Mock LLM provider for testing purposes."""

    def __init__(self, api_key: str = "test-key", **kwargs):
        super().__init__(api_key, **kwargs)
        self.mock_evaluation = None
        self.mock_job_post = None

    def get_llm(self):
        return MagicMock()

    def evaluate_resume(self, resume_text: str, jd_text: str) -> CandidateEvaluation:
        if self.mock_evaluation:
            return self.mock_evaluation
        return CandidateEvaluation(
            exact_match=EvaluationScore(score=75, explanation="Mock evaluation"),
            similarity_match=EvaluationScore(score=70, explanation="Mock similarity"),
            achievement_impact=EvaluationScore(score=65, explanation="Mock achievement"),
            ownership=EvaluationScore(score=80, explanation="Mock ownership"),
            tier="Tier B",
            summary="Mock candidate summary"
        )

    def generate_job_post(self, title: str, location=None, additional_info=None):
        if self.mock_job_post:
            return self.mock_job_post
        return {
            "description": f"Mock job description for {title}",
            "requirements": "Mock requirements"
        }

    def generate_interview_questions(self, candidate_profile, job_description, num_questions=10):
        return [
            {"question": "Mock question 1", "category": "Technical"},
            {"question": "Mock question 2", "category": "Behavioral"},
        ]


# =============================================================================
# Test Fixtures
# =============================================================================

@pytest.fixture
def mock_provider():
    """Fixture providing a mock LLM provider."""
    provider = MockLLMProvider(api_key="test-key")
    provider.mock_evaluation = CandidateEvaluation(
        exact_match=EvaluationScore(score=85, explanation="Good match"),
        similarity_match=EvaluationScore(score=75, explanation="Related skills"),
        achievement_impact=EvaluationScore(score=70, explanation="Some achievements"),
        ownership=EvaluationScore(score=80, explanation="Leadership shown"),
        tier="Tier A",
        summary="Strong candidate"
    )
    return provider


@pytest.fixture
def tier_b_evaluation():
    """Fixture for Tier B evaluation result."""
    return CandidateEvaluation(
        exact_match=EvaluationScore(score=60, explanation="Moderate match"),
        similarity_match=EvaluationScore(score=55, explanation="Some related skills"),
        achievement_impact=EvaluationScore(score=50, explanation="Limited achievements"),
        ownership=EvaluationScore(score=45, explanation="Some leadership"),
        tier="Tier B",
        summary="Good candidate for technical screen"
    )


# =============================================================================
# PDF Extraction Tests
# =============================================================================

class TestExtractTextFromPDF:
    """Tests for PDF text extraction functionality."""

    def test_extract_text_from_valid_pdf(self):
        """Test extracting text from a valid PDF."""
        mock_pdf_content = b"%PDF-1.4\nTest content\n%%EOF"
        pdf_bytes = BytesIO(mock_pdf_content)

        with patch('engine.PdfReader') as mock_reader_class:
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


# =============================================================================
# Resume Evaluation Tests
# =============================================================================

class TestEvaluateResume:
    """Tests for resume evaluation functionality."""

    @patch.dict('os.environ', {
        'GROQ_API_KEY': 'test-api-key',
        'LLM_PROVIDER': 'groq'
    })
    @patch('llm_providers.get_provider')
    def test_evaluate_resume_with_mock_provider(self, mock_get_provider, mock_provider):
        """Test that evaluate_resume uses the provider abstraction."""
        mock_get_provider.return_value = mock_provider

        result = evaluate_resume("resume text", "jd text")

        assert result.tier == "Tier A"
        assert result.exact_match.score == 85
        assert result.summary == "Strong candidate"

    @patch('llm_providers.get_provider')
    def test_evaluate_resume_tier_b_classification(
        self, mock_get_provider, tier_b_evaluation
    ):
        """Test evaluation with Tier B classification."""
        mock_provider = MockLLMProvider(api_key="test-key")
        mock_provider.mock_evaluation = tier_b_evaluation
        mock_get_provider.return_value = mock_provider

        with patch.dict('os.environ', {'GROQ_API_KEY': 'test-api-key'}):
            result = evaluate_resume("resume text", "jd text")

        assert result.tier == "Tier B"
        assert result.exact_match.score == 60

    @patch('llm_providers.get_provider')
    def test_evaluate_resume_propagates_provider_errors(self, mock_get_provider):
        """Test that provider errors are properly propagated."""
        mock_get_provider.side_effect = ValueError("Provider configuration error")

        with patch.dict('os.environ', {'GROQ_API_KEY': 'test-api-key'}):
            with pytest.raises(ValueError, match="Provider configuration error"):
                evaluate_resume("resume text", "jd text")


# =============================================================================
# Job Post Generation Tests
# =============================================================================

class TestGenerateJobPost:
    """Tests for job post generation functionality."""

    @patch('llm_providers.get_provider')
    def test_generate_job_post_basic(self, mock_get_provider):
        """Test basic job post generation."""
        mock_provider = MockLLMProvider(api_key="test-key")
        mock_get_provider.return_value = mock_provider

        with patch.dict('os.environ', {'GROQ_API_KEY': 'test-api-key'}):
            result = generate_job_post("Software Engineer")

        assert "description" in result
        assert "requirements" in result
        assert "Software Engineer" in result["description"]

    @patch('llm_providers.get_provider')
    def test_generate_job_post_with_location(self, mock_get_provider):
        """Test job post generation with location."""
        mock_provider = MockLLMProvider(api_key="test-key")
        mock_get_provider.return_value = mock_provider

        with patch.dict('os.environ', {'GROQ_API_KEY': 'test-api-key'}):
            result = generate_job_post(
                "Software Engineer",
                location="San Francisco, CA"
            )

        assert result is not None


# =============================================================================
# Model Validation Tests
# =============================================================================

class TestEvaluationScore:
    """Tests for EvaluationScore model."""

    def test_evaluation_score_creation(self):
        """Test creating an EvaluationScore instance."""
        score = EvaluationScore(score=90, explanation="Excellent match")

        assert score.score == 90
        assert score.explanation == "Excellent match"

    def test_evaluation_score_validation(self):
        """Test EvaluationScore validates required fields."""
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


# =============================================================================
# Configuration Tests
# =============================================================================

class TestConfiguration:
    """Tests for configuration management."""

    @patch.dict('os.environ', {
        'GROQ_API_KEY': 'test-key',
        'LLM_PROVIDER': 'groq'
    })
    def test_config_loads_from_env(self):
        """Test that configuration loads from environment variables."""
        from config import get_config
        config = get_config()

        assert config.llm_provider == 'groq'
        assert config.llm.api_key == 'test-key'

    @patch.dict('os.environ', {
        'OPENAI_API_KEY': 'openai-test-key',
        'LLM_PROVIDER': 'openai'
    })
    def test_config_supports_openai_provider(self):
        """Test that configuration supports OpenAI provider."""
        from config import get_config
        config = get_config()

        assert config.llm_provider == 'openai'
        assert config.llm.api_key == 'openai-test-key'
