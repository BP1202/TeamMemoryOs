from pydantic import computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "TeamMemoryOS"
    APP_ENV: str = "development"
    API_V1_PREFIX: str = "/api/v1"

    # Database
    POSTGRES_USER: str = "teammemory_admin"
    POSTGRES_PASSWORD: str = "changeme"
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5433
    POSTGRES_DB: str = "teammemory_os"

    @computed_field
    @property
    def DATABASE_URL(self) -> str:
        return (
            f"postgresql+psycopg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    model_config = SettingsConfigDict(
        env_file="backend/.env",
        case_sensitive=True
    )


settings = Settings()