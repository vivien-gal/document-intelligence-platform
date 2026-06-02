from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "sqlite:///./data/app.db"
    data_dir: str = "./data"
    embedding_model: str = "all-MiniLM-L6-v2"
    chunk_size: int = 1000
    chunk_overlap: int = 200

    @property
    def data_path(self) -> Path:
        return Path(self.data_dir)


settings = Settings()
