from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg:///orbit_db"
    SECRET_KEY: str = "your-secret-key"
    DEBUG: bool = False
    model_config = SettingsConfigDict(
        env_file=".env", 
        env_file_encoding="utf-8")

settings = Settings()