from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # --- 新增环境变量 ---
    # 定义当前环境：development (开发) 或 production (生产)
    APP_ENV: str = "development"  
    
    DATABASE_URL: str = "postgresql+asyncpg:///orbit_db"
    SECRET_KEY: SecretStr
    DEBUG: bool = False
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 天
    ALGORITHM: str = "HS256"
    # 如果未来需要 refresh token
    REFRESH_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 30  # 30 天
    
    model_config = SettingsConfigDict(
        env_file=".env", 
        env_file_encoding="utf-8")

settings = Settings()