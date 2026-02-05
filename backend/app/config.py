import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    PROJECT_NAME: str = "Parlamentsmonitor"
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql://polit:polit@localhost:5432/polit_monitor",
    )
    SECRET_KEY: str = os.getenv("SECRET_KEY", "change-me-in-production")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours
    PARLIAMENT_API_BASE: str = "https://ws.parlament.ch/odata.svc"
    SYNC_INTERVAL_HOURS: int = 6
    MONITORING_CRON_HOUR: int = 7


settings = Settings()
