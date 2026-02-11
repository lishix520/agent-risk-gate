from __future__ import annotations

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8', extra='ignore')

    app_env: str = Field(default='dev', alias='APP_ENV')
    database_url: str = Field(default='postgresql://admin:admin@127.0.0.1:5432/continuity_system', alias='DATABASE_URL')

    safe_threshold: float = Field(default=0.0, alias='SAFE_THRESHOLD')
    theta_ask: float = Field(default=0.55, alias='THETA_ASK')
    uncertainty_k: float = Field(default=0.4, alias='UNCERTAINTY_K')
    l4_similarity_gate: float = Field(default=0.85, alias='L4_SIMILARITY_GATE')
    confirm_token_ttl_minutes: int = Field(default=30, alias='CONFIRM_TOKEN_TTL_MINUTES')
    reality_first_mode: str = Field(default='low_intervention', alias='REALITY_FIRST_MODE')  # off|low_intervention

    llm_provider: str = Field(default='auto', alias='LLM_PROVIDER')  # auto|anthropic|openai
    llm_timeout_seconds: float = Field(default=20.0, alias='LLM_TIMEOUT_SECONDS')
    llm_max_tokens: int = Field(default=1200, alias='LLM_MAX_TOKENS')

    anthropic_api_key: str = Field(default='', alias='ANTHROPIC_API_KEY')
    anthropic_model: str = Field(default='claude-3-5-sonnet-latest', alias='ANTHROPIC_MODEL')

    openai_api_key: str = Field(default='', alias='OPENAI_API_KEY')
    openai_model: str = Field(default='gpt-4o-mini', alias='OPENAI_MODEL')


settings = Settings()
