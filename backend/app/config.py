"""应用配置 - 从环境变量读取"""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # 数据库
    database_url: str = "sqlite+aiosqlite:///./toto.db"

    # 爬虫配置
    scrape_delay_seconds: float = 5.0          # 单次请求间隔
    scrape_user_agent: str = "TotoAnalyzer/0.1 (personal-project; +https://github.com/yourname/toto-analyzer)"
    scrape_max_retries: int = 3

    # API
    api_cors_origins: list[str] = ["http://localhost:3000", "http://localhost:8080"]

    # 鉴权 (P3)
    jwt_secret: str = "change-me-in-prod"
    jwt_algorithm: str = "HS256"
    jwt_expire_hours: int = 24 * 30


settings = Settings()
