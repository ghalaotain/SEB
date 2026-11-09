import os
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY")

    APP_MODE = os.getenv(
        "APP_MODE",
        "demo",
    ).strip().lower()

    DEMO_MODE = APP_MODE == "demo"

    AI_ENABLED = (
        os.getenv("AI_ENABLED", "false").strip().lower()
        in {"1", "true", "yes", "on"}
    )

    AI_DETECTOR_BACKEND = os.getenv(
        "AI_DETECTOR_BACKEND",
        "opencv",
    ).strip().lower()

    AI_MAX_IMAGE_PIXELS = int(
        os.getenv(
            "AI_MAX_IMAGE_PIXELS",
            "16000000",
        )
    )

    BOOTH_ID = os.getenv("BOOTH_ID", "booth_1")

    PERSONALIZED_AD_DURATION = int(
        os.getenv("PERSONALIZED_AD_DURATION", "15")
    )

    GENERAL_CAROUSEL_INTERVAL = int(
        os.getenv("GENERAL_CAROUSEL_INTERVAL", "7")
    )

    MAX_CONTENT_LENGTH = (
        int(os.getenv("MAX_CONTENT_LENGTH_MB", "8"))
        * 1024
        * 1024
    )

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"

    @classmethod
    def database_uri(cls) -> str:
        if cls.DEMO_MODE:
            database_path = (
                BASE_DIR
                / "instance"
                / "seb_demo.db"
            )

            return (
                f"sqlite:///"
                f"{database_path.as_posix()}"
            )

        database_url = (
            os.getenv("DATABASE_URL")
            or os.getenv("MYSQL_URL")
        )

        if not database_url:
            raise RuntimeError(
                "DATABASE_URL or MYSQL_URL is required outside demo mode."
            )

        if database_url.startswith("mysql://"):
            database_url = database_url.replace(
                "mysql://",
                "mysql+pymysql://",
                1,
            )

        return database_url


class DevelopmentConfig(Config):
    DEBUG = True
    SESSION_COOKIE_SECURE = False


class ProductionConfig(Config):
    DEBUG = False
    SESSION_COOKIE_SECURE = True

    @classmethod
    def validate(cls) -> None:
        if not cls.SECRET_KEY:
            raise RuntimeError(
                "SECRET_KEY is required."
            )

        if len(cls.SECRET_KEY) < 32:
            raise RuntimeError(
                "SECRET_KEY must contain at least 32 characters."
            )

        if cls.DEMO_MODE:
            raise RuntimeError(
                "Production cannot run in demo mode."
            )


CONFIGS = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
}
