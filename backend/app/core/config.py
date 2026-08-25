from typing import List
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    ENVIRONMENT: str = Field(default="development")
    DEBUG: bool = Field(default=True)
    PROJECT_NAME: str = Field(default="CodeRunner Cloud")
    API_V1_PREFIX: str = Field(default="/api/v1")

    # CORS
    ALLOWED_ORIGINS: str = Field(
        default="http://localhost:4200,http://127.0.0.1:4200,http://localhost:3000"
    )

    # Database
    DATABASE_URL: str = Field(default="postgresql://coderunner:password@localhost:5432/coderunner")

    # Redis
    REDIS_URL: str = Field(default="redis://localhost:6379/0")

    # JWT
    JWT_SECRET: str = Field(default="coderunner_cloud_dev_secret_key_needs_32_bytes!")
    JWT_ALGORITHM: str = Field(default="HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=1440)  # 24 hours

    # API Key hashing secret
    API_KEY_SECRET: str = Field(default="api_key_secret_salt_for_hmac_hashing_change_me!")

    # Docker Sandbox Execution Constraints
    DOCKER_BASE_URL: str = Field(default="")
    DEFAULT_EXECUTION_TIMEOUT: int = Field(default=10)
    DEFAULT_MEMORY_LIMIT: str = Field(default="128m")
    DEFAULT_CPU_QUOTA: int = Field(default=50000)   # 50% CPU
    DEFAULT_PIDS_LIMIT: int = Field(default=64)
    MAX_SOURCE_CODE_SIZE_BYTES: int = Field(default=65536)   # 64 KB
    MAX_OUTPUT_SIZE_BYTES: int = Field(default=131072)        # 128 KB

    # Plan Limits
    FREE_MONTHLY_EXECUTIONS: int = Field(default=100)
    DEVELOPER_MONTHLY_EXECUTIONS: int = Field(default=5000)
    PRO_MONTHLY_EXECUTIONS: int = Field(default=25000)

    # Rate Limits (requests per minute)
    RATE_LIMIT_FREE: int = Field(default=20)
    RATE_LIMIT_DEVELOPER: int = Field(default=120)
    RATE_LIMIT_PRO: int = Field(default=600)

    @property
    def cors_origins(self) -> List[str]:
        return [o.strip() for o in self.ALLOWED_ORIGINS.split(",") if o.strip()]

    model_config = {"case_sensitive": True, "env_file": ".env", "extra": "ignore"}


settings = Settings()
