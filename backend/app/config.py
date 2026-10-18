import os
from pathlib import Path

from dotenv import load_dotenv

# 优先读取项目根目录的 .env（兼容 docker-compose 与本地直接运行两种方式）
PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv()
load_dotenv(PROJECT_ROOT / ".env")


ENVIRONMENT = os.getenv("ENVIRONMENT", "development").strip().lower()


def _required_in_production(name: str, default: str = "") -> str:
    value = os.getenv(name, default).strip()
    if ENVIRONMENT == "production" and (
        not value or value.startswith("dev-only") or value.startswith("change-me")
    ):
        raise RuntimeError(f"生产环境必须通过环境变量设置安全的 {name}")
    return value


SECRET_KEY = _required_in_production("SECRET_KEY", "dev-only-change-me")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))

DATABASE_URL = os.getenv("DATABASE_URL", "").strip()
if not DATABASE_URL:
    if ENVIRONMENT == "production":
        raise RuntimeError("生产环境必须通过环境变量设置 DATABASE_URL")
    DATABASE_URL = "sqlite:///./blog_dev.db"

CORS_ORIGINS = [
    origin.strip()
    for origin in os.getenv(
        "CORS_ORIGINS",
        "http://localhost:5173,http://127.0.0.1:5173,"
        "http://localhost:4173,http://127.0.0.1:4173,"
        "http://localhost:8080,http://127.0.0.1:8080",
    ).split(",")
    if origin.strip()
]

PUBLIC_BASE_URL = os.getenv("PUBLIC_BASE_URL", "").strip().rstrip("/")

# 演示部署默认关闭动态上传；Render 免费实例的本地磁盘不是持久化存储。
ENABLE_IMAGE_UPLOAD = os.getenv("ENABLE_IMAGE_UPLOAD", "false").strip().lower() in {
    "1",
    "true",
    "yes",
}

ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = _required_in_production("ADMIN_PASSWORD")
