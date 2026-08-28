from typing import List
from pydantic_settings import BaseSettings
from pydantic import Field, field_validator
import sys


class Settings(BaseSettings):
    ENVIRONMENT: str = Field(default="development")
    DEBUG: bool = Field(default=True)
    PROJECT_NAME: str = Field(default="CodeRunner Cloud")
    API_V1_PREFIX: str = Field(default="/api/v1")

    # CORS
    ALLOWED_ORIGINS: str = Field(
        default="http://localhost:4200,http://127.0.0.1:4200,http://localhost:3000,https://coderunner-cloud.vercel.app"
    )

    # Database — required in production
    DATABASE_URL: str = Field(default="postgresql://coderunner:password@localhost:5432/coderunner")

    # Redis
    REDIS_URL: str = Field(default="redis://localhost:6379/0")

    # JWT
    JWT_SECRET: str = Field(default="coderunner_cloud_dev_secret_key_needs_32_bytes!")
    JWT_ALGORITHM: str = Field(default="HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=1440)

    # API Key hashing secret
    API_KEY_SECRET: str = Field(default="api_key_secret_salt_for_hmac_hashing_change_me!")

    # SafePay Configuration
    SAFEPAY_API_KEY: str = Field(default="")
    SAFEPAY_WEBHOOK_SECRET: str = Field(default="")
    SAFEPAY_ENVIRONMENT: str = Field(default="sandbox")

    # Docker Sandbox Execution Constraints
    DOCKER_BASE_URL: str = Field(default="")
    DEFAULT_EXECUTION_TIMEOUT: int = Field(default=10)
    DEFAULT_MEMORY_LIMIT: str = Field(default="128m")
    DEFAULT_CPU_QUOTA: int = Field(default=50000)
    DEFAULT_PIDS_LIMIT: int = Field(default=64)
    MAX_SOURCE_CODE_SIZE_BYTES: int = Field(default=65536)
    MAX_OUTPUT_SIZE_BYTES: int = Field(default=131072)

    # Plan Limits (legacy)
    FREE_MONTHLY_EXECUTIONS: int = Field(default=100)
    DEVELOPER_MONTHLY_EXECUTIONS: int = Field(default=5000)
    PRO_MONTHLY_EXECUTIONS: int = Field(default=25000)

    # Rate Limits
    RATE_LIMIT_FREE: int = Field(default=20)
    RATE_LIMIT_DEVELOPER: int = Field(default=120)
    RATE_LIMIT_PRO: int = Field(default=600)

    # Render dynamic port (optional — Render sets $PORT)
    PORT: int = Field(default=8000)

    @field_validator("JWT_SECRET", mode="before")
    @classmethod
    def validate_jwt_secret(cls, v: str) -> str:
        weak_defaults = {
            "coderunner_cloud_dev_secret_key_needs_32_bytes!",
            "super_secret_key_change_in_production",
        }
        import os
        env = os.environ.get("ENVIRONMENT", "development")
        if env == "production" and v.strip() in weak_defaults:
            raise ValueError(
                "JWT_SECRET is using a weak default value in production. "
                "Set a strong random secret in Render Environment Variables."
            )
        return v

    @field_validator("API_KEY_SECRET", mode="before")
    @classmethod
    def validate_api_key_secret(cls, v: str) -> str:
        weak_defaults = {
            "api_key_secret_salt_for_hmac_hashing_change_me!",
            "another_super_secret_key_for_hashing",
        }
        import os
        env = os.environ.get("ENVIRONMENT", "development")
        if env == "production" and v.strip() in weak_defaults:
            raise ValueError(
                "API_KEY_SECRET is using a weak default value in production. "
                "Set a strong random secret in Render Environment Variables."
            )
        return v

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def validate_and_fix_database_url(cls, v: str) -> str:
        """
        1. Fail fast with a clear message if DATABASE_URL is missing/empty.
        2. Normalise Render's 'postgres://' prefix → 'postgresql+psycopg2://'
           so SQLAlchemy can parse it without error.
        """
        if not v or not v.strip():
            print(
                "\n[FATAL] DATABASE_URL is not set. "
                "Add it as an environment variable in Render → Service → Environment.\n"
                "Expected format: postgresql+psycopg2://<user>:<password>@<host>:5432/<dbname>\n",
                file=sys.stderr,
            )
            raise ValueError(
                "DATABASE_URL is required but was not provided. "
                "Set it in Render Environment Variables."
            )

        url = v.strip()

        # Render PostgreSQL gives 'postgres://...' — SQLAlchemy 2.x needs 'postgresql://'
        if url.startswith("postgres://"):
            url = "postgresql+psycopg2://" + url[len("postgres://"):]

        # Plain 'postgresql://' → add psycopg2 driver explicitly
        elif url.startswith("postgresql://"):
            url = "postgresql+psycopg2://" + url[len("postgresql://"):]

        # Already has driver specified — leave as-is
        # e.g. postgresql+psycopg2://... or postgresql+asyncpg://...

        valid_prefixes = (
            "postgresql+psycopg2://",
            "postgresql+psycopg://",
            "postgresql+asyncpg://",
            "sqlite:///",     # allow SQLite for local dev/testing
        )
        if not any(url.startswith(p) for p in valid_prefixes):
            print(
                f"\n[FATAL] DATABASE_URL has an unrecognised format.\n"
                f"Expected: postgresql+psycopg2://<user>:<password>@<host>:5432/<dbname>\n"
                f"Got prefix: {url[:30]}...\n",
                file=sys.stderr,
            )
            raise ValueError(
                "DATABASE_URL format is invalid. "
                "Expected a PostgreSQL SQLAlchemy URL."
            )

        return url

    @property
    def cors_origins(self) -> List[str]:
        return [o.strip() for o in self.ALLOWED_ORIGINS.split(",") if o.strip()]

    model_config = {"case_sensitive": True, "env_file": ".env", "extra": "ignore"}


settings = Settings()
