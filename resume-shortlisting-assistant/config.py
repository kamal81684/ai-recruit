"""
Centralized configuration management for AI Resume Shortlisting Assistant.

This module provides:
1. Environment-based configuration loading
2. Pydantic validation at startup
3. Type-safe configuration access
4. Clear error messages for missing configuration

Contributor: shubham21155102
"""

import os
from typing import Literal, Optional
from pydantic import BaseModel, Field, field_validator
from dotenv import load_dotenv

load_dotenv()


class LLMProviderConfig(BaseModel):
    """Configuration for a specific LLM provider."""
    api_key: str = Field(..., description="API key for the LLM provider")
    model: str = Field(..., description="Model identifier to use")
    temperature: float = Field(default=0.0, ge=0.0, le=2.0, description="Temperature for generation")
    max_tokens: int = Field(default=2048, gt=0, description="Maximum tokens to generate")


class DatabaseConfig(BaseModel):
    """Database configuration."""
    url: str = Field(..., description="Database connection URL")
    pool_size: int = Field(default=5, ge=1, description="Connection pool size")
    max_overflow: int = Field(default=10, ge=0, description="Max overflow connections")


class AppConfig(BaseModel):
    """Main application configuration."""
    # Application settings
    app_name: str = Field(default="AI Resume Shortlisting Assistant")
    environment: Literal["development", "production", "testing"] = Field(default="development")
    debug: bool = Field(default=False)

    # Database configuration
    database: DatabaseConfig

    # LLM Provider settings
    llm_provider: Literal["groq", "openai", "anthropic", "custom"] = Field(default="groq")
    llm: LLMProviderConfig

    # CORS settings
    cors_origins: list[str] = Field(
        default=["http://localhost:3000", "https://ai-recruit-two.vercel.app"],
        description="Allowed CORS origins"
    )

    # Server settings
    host: str = Field(default="0.0.0.0")
    port: int = Field(default=5001, ge=1, le=65535)

    @field_validator('database', mode='before')
    @classmethod
    def validate_database(cls, v):
        """Validate database configuration from environment."""
        if isinstance(v, dict):
            return v
        return {
            'url': os.getenv('DATABASE_URL', ''),
            'pool_size': int(os.getenv('DB_POOL_SIZE', '5')),
            'max_overflow': int(os.getenv('DB_MAX_OVERFLOW', '10'))
        }

    @field_validator('llm', mode='before')
    @classmethod
    def validate_llm(cls, v):
        """Validate LLM configuration from environment."""
        if isinstance(v, dict):
            return v

        provider = os.getenv('LLM_PROVIDER', 'groq').lower()

        # Provider-specific defaults
        model_defaults = {
            'groq': os.getenv('GROQ_MODEL', 'llama-3.3-70b-versatile'),
            'openai': os.getenv('OPENAI_MODEL', 'gpt-4'),
            'anthropic': os.getenv('ANTHROPIC_MODEL', 'claude-3-opus-20240229'),
            'custom': os.getenv('CUSTOM_MODEL', 'gpt-oss-120b')
        }

        return {
            'api_key': os.getenv('GROQ_API_KEY') or os.getenv('OPENAI_API_KEY') or os.getenv('ANTHROPIC_API_KEY') or '',
            'model': model_defaults.get(provider, 'llama-3.3-70b-versatile'),
            'temperature': float(os.getenv('LLM_TEMPERATURE', '0.0')),
            'max_tokens': int(os.getenv('LLM_MAX_TOKENS', '2048'))
        }

    @field_validator('llm_provider')
    @classmethod
    def validate_provider(cls, v):
        """Validate that the selected provider has an API key."""
        provider = v.lower()
        api_keys = {
            'groq': os.getenv('GROQ_API_KEY'),
            'openai': os.getenv('OPENAI_API_KEY'),
            'anthropic': os.getenv('ANTHROPIC_API_KEY')
        }

        if provider in api_keys and not api_keys[provider]:
            raise ValueError(
                f"LLM provider '{provider}' selected but API key not found. "
                f"Please set {provider.upper()}_API_KEY environment variable."
            )

        # Also check for custom provider
        custom_key = os.getenv('CUSTOM_LLM_API_KEY')
        if provider == 'custom' and not custom_key:
            raise ValueError(
                "Custom LLM provider selected but CUSTOM_LLM_API_KEY not found."
            )

        return provider

    @classmethod
    def load_from_env(cls) -> 'AppConfig':
        """
        Load and validate configuration from environment variables.

        Raises:
            ValueError: If required environment variables are missing or invalid

        Returns:
            AppConfig: Validated configuration instance
        """
        return cls(
            app_name=os.getenv('APP_NAME', 'AI Resume Shortlisting Assistant'),
            environment=os.getenv('ENVIRONMENT', 'development'),
            debug=os.getenv('DEBUG', 'false').lower() == 'true',
            llm_provider=os.getenv('LLM_PROVIDER', 'groq'),
            host=os.getenv('HOST', '0.0.0.0'),
            port=int(os.getenv('PORT', '5001'))
        )


# Global configuration instance
_config: Optional[AppConfig] = None


def get_config() -> AppConfig:
    """
    Get the global configuration instance.

    Loads configuration on first call and caches it.

    Returns:
        AppConfig: The application configuration

    Raises:
        ValueError: If configuration validation fails
    """
    global _config

    if _config is None:
        _config = AppConfig.load_from_env()

    return _config


def reload_config() -> AppConfig:
    """
    Force reload configuration from environment.

    Useful for testing or when environment variables change.

    Returns:
        AppConfig: The newly loaded configuration
    """
    global _config
    _config = AppConfig.load_from_env()
    return _config
