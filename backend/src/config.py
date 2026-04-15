from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database
    database_url: str = "postgresql+psycopg://dev:devpassword@localhost:5432/public_sector"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # Alibaba Cloud OSS
    storage_backend: str = "local"  # "oss" or "local"
    local_storage_path: str = "/data/uploads"
    oss_access_key_id: str = ""
    oss_access_key_secret: str = ""
    oss_bucket_name: str = "public-sector-docs"
    oss_endpoint: str = "https://oss-ap-southeast-1.aliyuncs.com"

    # Alibaba Cloud Model Studio (dashscope)
    dashscope_api_key: str = ""

    # Celery
    celery_broker_url: str = "redis://localhost:6379/0"
    celery_result_backend: str = "redis://localhost:6379/1"

    # VNeID OAuth
    vneid_base_url: str = "http://localhost:9000"
    vneid_client_id: str = "citizen-app"
    vneid_client_secret: str = "mock-secret"  # noqa: S105

    # JWT
    jwt_secret_key: str = "change-me-in-production"  # noqa: S105
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 60

    # Image quality
    image_quality_threshold: float = 0.5

    # Classification
    classification_confidence_threshold: float = 0.7

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
