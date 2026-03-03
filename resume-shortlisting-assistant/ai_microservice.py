"""
AI Microservice Abstraction Layer.

This module provides a microservice architecture for AI inference,
allowing the AI model (parsing PDFs, calculating similarity scores)
to be deployed as a standalone FastAPI service.

Architecture benefits:
- Independent scaling of AI resources (GPU vs CPU)
- Prevents heavy NLP tasks from blocking web requests
- Enables horizontal scaling of AI workers
- Provides health monitoring and circuit breaker patterns

Contributor: shubham21155102 - Enterprise Architecture Phase 7
"""

import os
import asyncio
import logging
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import json
from functools import wraps
import time

try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False

from structured_logging import get_logger, LogContext

logger = get_logger(__name__)


class ServiceStatus(Enum):
    """Status of the AI microservice."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNAVAILABLE = "unavailable"
    CIRCUIT_OPEN = "circuit_open"


@dataclass
class ServiceEndpoint:
    """Configuration for an AI service endpoint."""
    url: str
    name: str = "ai_service"
    timeout: float = 30.0
    max_retries: int = 3
    health_check_path: str = "/health"
    enabled: bool = True


@dataclass
class ServiceMetrics:
    """Metrics for the AI service."""
    request_count: int = 0
    success_count: int = 0
    failure_count: int = 0
    avg_response_time: float = 0.0
    last_request_time: Optional[datetime] = None
    circuit_breaker_trips: int = 0
    circuit_breaker_last_opened: Optional[datetime] = None


class CircuitBreaker:
    """
    Circuit breaker pattern implementation for AI service calls.

    Prevents cascading failures by stopping calls to a failing service
    after a threshold of failures is reached.
    """

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0,
        expected_exception: Exception = Exception
    ):
        """
        Initialize the circuit breaker.

        Args:
            failure_threshold: Number of failures before opening circuit
            recovery_timeout: Seconds to wait before attempting recovery
            expected_exception: Exception type that counts as failure
        """
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        self.failure_count = 0
        self.last_failure_time: Optional[datetime] = None
        self.state = ServiceStatus.HEALTHY

    def call(self, func: Callable, *args, **kwargs):
        """
        Execute a function through the circuit breaker.

        Args:
            func: Function to execute
            *args: Positional arguments
            **kwargs: Keyword arguments

        Returns:
            Function result

        Raises:
            Exception: If circuit is open or function fails
        """
        if self.state == ServiceStatus.CIRCUIT_OPEN:
            if self._should_attempt_reset():
                self.state = ServiceStatus.DEGRADED
                logger.info("Circuit breaker attempting recovery")
            else:
                raise Exception("Circuit breaker is OPEN")

        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except self.expected_exception as e:
            self._on_failure()
            raise e

    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt recovery."""
        if self.last_failure_time is None:
            return True
        elapsed = (datetime.now() - self.last_failure_time).total_seconds()
        return elapsed >= self.recovery_timeout

    def _on_success(self):
        """Handle successful call."""
        self.failure_count = 0
        self.state = ServiceStatus.HEALTHY

    def _on_failure(self):
        """Handle failed call."""
        self.failure_count += 1
        self.last_failure_time = datetime.now()

        if self.failure_count >= self.failure_threshold:
            self.state = ServiceStatus.CIRCUIT_OPEN
            logger.warning(
                f"Circuit breaker opened after {self.failure_count} failures"
            )


class AIMicroserviceClient:
    """
    Client for communicating with the AI microservice.

    This client handles:
    - Service discovery and health checks
    - Load balancing across multiple instances
    - Circuit breaker pattern for resilience
    - Retry logic with exponential backoff
    - Request/response logging
    """

    def __init__(self, endpoints: List[ServiceEndpoint]):
        """
        Initialize the AI microservice client.

        Args:
            endpoints: List of service endpoints
        """
        self.endpoints = [e for e in endpoints if e.enabled]
        self.current_endpoint_index = 0
        self.metrics = ServiceMetrics()

        # Circuit breaker for each endpoint
        self.circuit_breakers = {
            endpoint.url: CircuitBreaker()
            for endpoint in self.endpoints
        }

        self._client = None

    def _get_client(self):
        """Get or create HTTP client."""
        if not HTTPX_AVAILABLE:
            raise RuntimeError("httpx is required for AI microservice client")

        if self._client is None:
            self._client = httpx.AsyncClient(timeout=30.0)
        return self._client

    def _get_next_endpoint(self) -> Optional[ServiceEndpoint]:
        """Get the next available endpoint using round-robin."""
        if not self.endpoints:
            return None

        # Find healthy endpoint
        for _ in range(len(self.endpoints)):
            endpoint = self.endpoints[self.current_endpoint_index]
            self.current_endpoint_index = (self.current_endpoint_index + 1) % len(self.endpoints)

            circuit_breaker = self.circuit_breakers[endpoint.url]
            if circuit_breaker.state != ServiceStatus.CIRCUIT_OPEN:
                return endpoint

        return None

    async def check_health(self) -> Dict[str, ServiceStatus]:
        """
        Check health of all endpoints.

        Returns:
            Dict mapping endpoint URLs to their status
        """
        client = self._get_client()
        statuses = {}

        for endpoint in self.endpoints:
            try:
                url = f"{endpoint.url}{endpoint.health_check_path}"
                response = await client.get(url, timeout=5.0)
                statuses[endpoint.url] = (
                    ServiceStatus.HEALTHY if response.status_code == 200
                    else ServiceStatus.DEGRADED
                )
            except Exception as e:
                logger.error(f"Health check failed for {endpoint.url}: {e}")
                statuses[endpoint.url] = ServiceStatus.UNAVAILABLE

        return statuses

    async def evaluate_resume(
        self,
        resume_text: str,
        job_description: str,
        request_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Evaluate a resume against a job description.

        Args:
            resume_text: Extracted resume text
            job_description: Job description text
            request_id: Optional request tracking ID

        Returns:
            Evaluation result dictionary
        """
        endpoint = self._get_next_endpoint()
        if not endpoint:
            raise Exception("No healthy AI service endpoints available")

        with LogContext(request_id=request_id, operation='ai_evaluate_resume'):
            client = self._get_client()
            url = f"{endpoint.url}/api/v1/evaluate"

            payload = {
                "resume_text": resume_text,
                "job_description": job_description
            }

            return await self._make_request(endpoint, url, payload)

    async def generate_interview_questions(
        self,
        candidate_profile: Dict[str, Any],
        job_description: str,
        num_questions: int = 10,
        request_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Generate interview questions for a candidate.

        Args:
            candidate_profile: Candidate profile data
            job_description: Job description text
            num_questions: Number of questions to generate
            request_id: Optional request tracking ID

        Returns:
            List of question dictionaries
        """
        endpoint = self._get_next_endpoint()
        if not endpoint:
            raise Exception("No healthy AI service endpoints available")

        with LogContext(request_id=request_id, operation='ai_generate_questions'):
            client = self._get_client()
            url = f"{endpoint.url}/api/v1/generate-questions"

            payload = {
                "candidate_profile": candidate_profile,
                "job_description": job_description,
                "num_questions": num_questions
            }

            result = await self._make_request(endpoint, url, payload)
            return result.get("questions", [])

    async def rewrite_resume(
        self,
        resume_text: str,
        job_description: str,
        job_title: str,
        request_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Rewrite a resume to better match a job description.

        Args:
            resume_text: Original resume text
            job_description: Target job description
            job_title: Target job title
            request_id: Optional request tracking ID

        Returns:
            Improved resume content
        """
        endpoint = self._get_next_endpoint()
        if not endpoint:
            raise Exception("No healthy AI service endpoints available")

        with LogContext(request_id=request_id, operation='ai_rewrite_resume'):
            client = self._get_client()
            url = f"{endpoint.url}/api/v1/rewrite-resume"

            payload = {
                "resume_text": resume_text,
                "job_description": job_description,
                "job_title": job_title
            }

            return await self._make_request(endpoint, url, payload)

    async def _make_request(
        self,
        endpoint: ServiceEndpoint,
        url: str,
        payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Make a request to the AI service with retry logic.

        Args:
            endpoint: Service endpoint
            url: Full request URL
            payload: Request payload

        Returns:
            Response data
        """
        circuit_breaker = self.circuit_breakers[endpoint.url]
        client = self._get_client()

        async def _do_request():
            start_time = time.time()
            self.metrics.request_count += 1

            try:
                response = await client.post(url, json=payload, timeout=endpoint.timeout)
                response.raise_for_status()
                result = response.json()

                elapsed = time.time() - start_time
                self.metrics.success_count += 1
                self.metrics.last_request_time = datetime.now()

                # Update average response time
                total = self.metrics.avg_response_time * (self.metrics.success_count - 1)
                self.metrics.avg_response_time = (total + elapsed) / self.metrics.success_count

                logger.debug(f"AI service request completed in {elapsed:.2f}s")
                return result

            except Exception as e:
                elapsed = time.time() - start_time
                self.metrics.failure_count += 1
                logger.error(f"AI service request failed after {elapsed:.2f}s: {e}")
                raise

        # Use circuit breaker
        return circuit_breaker.call(_do_request)

    def get_metrics(self) -> Dict[str, Any]:
        """
        Get service metrics.

        Returns:
            Metrics dictionary
        """
        return {
            "request_count": self.metrics.request_count,
            "success_count": self.metrics.success_count,
            "failure_count": self.metrics.failure_count,
            "avg_response_time": round(self.metrics.avg_response_time, 3),
            "success_rate": (
                self.metrics.success_count / self.metrics.request_count
                if self.metrics.request_count > 0 else 0
            ),
            "endpoints": [
                {
                    "url": e.url,
                    "name": e.name,
                    "status": self.circuit_breakers[e.url].state.value
                }
                for e in self.endpoints
            ]
        }

    async def close(self):
        """Close the HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None


# =============================================================================
# Fallback to Local AI Processing
# =============================================================================

class LocalAIService:
    """
    Fallback local AI service when microservice is unavailable.

    This provides the same interface but uses the local LLM provider
    instead of calling the microservice.
    """

    def __init__(self):
        """Initialize the local AI service."""
        from llm_providers import get_provider
        self.provider = get_provider()

    async def evaluate_resume(
        self,
        resume_text: str,
        job_description: str,
        request_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Evaluate resume using local LLM provider."""
        # Run in thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            lambda: self.provider.evaluate_resume(resume_text, job_description)
        )

        # Convert to dict
        return {
            'tier': result.tier,
            'summary': result.summary,
            'exact_match': {
                'score': result.exact_match.score,
                'explanation': result.exact_match.explanation
            },
            'similarity_match': {
                'score': result.similarity_match.score,
                'explanation': result.similarity_match.explanation
            },
            'achievement_impact': {
                'score': result.achievement_impact.score,
                'explanation': result.achievement_impact.explanation
            },
            'ownership': {
                'score': result.ownership.score,
                'explanation': result.ownership.explanation
            }
        }

    async def generate_interview_questions(
        self,
        candidate_profile: Dict[str, Any],
        job_description: str,
        num_questions: int = 10,
        request_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Generate interview questions using local LLM provider."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            lambda: self.provider.generate_interview_questions(
                candidate_profile, job_description, num_questions
            )
        )

    async def rewrite_resume(
        self,
        resume_text: str,
        job_description: str,
        job_title: str,
        request_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Rewrite resume using local LLM provider."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            lambda: self.provider.rewrite_resume_for_job(
                resume_text, job_description, job_title
            )
        )


# =============================================================================
# Service Manager
# =============================================================================

class AIServiceManager:
    """
    Manager for AI service with fallback to local processing.

    Automatically falls back to local LLM if microservice is unavailable.
    """

    def __init__(self, microservice_endpoints: Optional[List[ServiceEndpoint]] = None):
        """
        Initialize the AI service manager.

        Args:
            microservice_endpoints: Optional list of microservice endpoints
        """
        self.microservice_client: Optional[AIMicroserviceClient] = None
        self.local_service = LocalAIService()
        self.use_microservice = False

        if microservice_endpoints and HTTPX_AVAILABLE:
            self.microservice_client = AIMicroserviceClient(microservice_endpoints)
            self.use_microservice = True
            logger.info(f"AI microservice client initialized with {len(microservice_endpoints)} endpoints")

    async def evaluate_resume(
        self,
        resume_text: str,
        job_description: str,
        request_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Evaluate resume with automatic fallback."""
        if self.use_microservice and self.microservice_client:
            try:
                return await self.microservice_client.evaluate_resume(
                    resume_text, job_description, request_id
                )
            except Exception as e:
                logger.warning(f"Microservice failed, falling back to local: {e}")
                self.use_microservice = False

        # Fallback to local
        return await self.local_service.evaluate_resume(
            resume_text, job_description, request_id
        )

    async def generate_interview_questions(
        self,
        candidate_profile: Dict[str, Any],
        job_description: str,
        num_questions: int = 10,
        request_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Generate interview questions with automatic fallback."""
        if self.use_microservice and self.microservice_client:
            try:
                return await self.microservice_client.generate_interview_questions(
                    candidate_profile, job_description, num_questions, request_id
                )
            except Exception as e:
                logger.warning(f"Microservice failed, falling back to local: {e}")
                self.use_microservice = False

        return await self.local_service.generate_interview_questions(
            candidate_profile, job_description, num_questions, request_id
        )

    async def rewrite_resume(
        self,
        resume_text: str,
        job_description: str,
        job_title: str,
        request_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Rewrite resume with automatic fallback."""
        if self.use_microservice and self.microservice_client:
            try:
                return await self.microservice_client.rewrite_resume(
                    resume_text, job_description, job_title, request_id
                )
            except Exception as e:
                logger.warning(f"Microservice failed, falling back to local: {e}")
                self.use_microservice = False

        return await self.local_service.rewrite_resume(
            resume_text, job_description, job_title, request_id
        )

    def get_metrics(self) -> Dict[str, Any]:
        """Get service metrics."""
        if self.microservice_client:
            return self.microservice_client.get_metrics()
        return {"status": "local_only"}

    async def close(self):
        """Close resources."""
        if self.microservice_client:
            await self.microservice_client.close()


# =============================================================================
# Singleton Instance
# =============================================================================

_ai_service_manager: Optional[AIServiceManager] = None


def get_ai_service() -> AIServiceManager:
    """
    Get the global AI service manager instance.

    Returns:
        AIServiceManager instance
    """
    global _ai_service_manager

    if _ai_service_manager is None:
        # Initialize from environment if configured
        endpoints_str = os.getenv('AI_MICROSERVICE_ENDPOINTS')
        if endpoints_str:
            endpoints = [
                ServiceEndpoint(url=url.strip())
                for url in endpoints_str.split(',')
            ]
            _ai_service_manager = AIServiceManager(endpoints)
        else:
            _ai_service_manager = AIServiceManager()

    return _ai_service_manager


# =============================================================================
# Standalone FastAPI Microservice
# =============================================================================

def create_fastapi_app():
    """
    Create a FastAPI application for the AI microservice.

    This can be run as a standalone service.

    Returns:
        FastAPI application instance
    """
    try:
        from fastapi import FastAPI, HTTPException
        from fastapi.middleware.cors import CORSMiddleware
        from pydantic import BaseModel
        import uvicorn

        # Pydantic models
        class EvaluateRequest(BaseModel):
            resume_text: str
            job_description: str

        class GenerateQuestionsRequest(BaseModel):
            candidate_profile: dict
            job_description: str
            num_questions: int = 10

        class RewriteRequest(BaseModel):
            resume_text: str
            job_description: str
            job_title: str

        # Create FastAPI app
        app = FastAPI(
            title="AI Resume Service",
            description="Microservice for AI-powered resume analysis",
            version="1.0.0"
        )

        # CORS middleware
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_methods=["*"],
            allow_headers=["*"],
        )

        # Import LLM provider
        from llm_providers import get_provider
        provider = get_provider()

        @app.get("/health")
        async def health_check():
            """Health check endpoint."""
            return {"status": "healthy", "service": "ai_resume_service"}

        @app.post("/api/v1/evaluate")
        async def evaluate(request: EvaluateRequest):
            """Evaluate resume endpoint."""
            try:
                result = provider.evaluate_resume(
                    request.resume_text,
                    request.job_description
                )
                return {
                    'tier': result.tier,
                    'summary': result.summary,
                    'exact_match': {
                        'score': result.exact_match.score,
                        'explanation': result.exact_match.explanation
                    },
                    'similarity_match': {
                        'score': result.similarity_match.score,
                        'explanation': result.similarity_match.explanation
                    },
                    'achievement_impact': {
                        'score': result.achievement_impact.score,
                        'explanation': result.achievement_impact.explanation
                    },
                    'ownership': {
                        'score': result.ownership.score,
                        'explanation': result.ownership.explanation
                    }
                }
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))

        @app.post("/api/v1/generate-questions")
        async def generate_questions(request: GenerateQuestionsRequest):
            """Generate interview questions endpoint."""
            try:
                questions = provider.generate_interview_questions(
                    request.candidate_profile,
                    request.job_description,
                    request.num_questions
                )
                return {"questions": questions}
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))

        @app.post("/api/v1/rewrite-resume")
        async def rewrite_resume(request: RewriteRequest):
            """Rewrite resume endpoint."""
            try:
                result = provider.rewrite_resume_for_job(
                    request.resume_text,
                    request.job_description,
                    request.job_title
                )
                return result
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))

        return app

    except ImportError:
        logger.warning("FastAPI not installed. Microservice creation disabled.")
        return None
