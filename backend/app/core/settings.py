from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "TeamMemoryOS"
    APP_ENV: str = "development"
    API_V1_PREFIX: str = "/api/v1"

    model_config = SettingsConfigDict(
        env_file="backend/.env",
        case_sensitive=True
    )


settings = Settings()