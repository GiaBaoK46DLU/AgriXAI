"""Kết nối cơ sở dữ liệu."""

from __future__ import annotations

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import settings

engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,   # tự kiểm tra kết nối chết trước khi dùng lại
    echo=False,
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


class Base(DeclarativeBase):
    """Lớp cơ sở cho mọi bảng."""


def get_db() -> Generator[Session, None, None]:
    """Dependency của FastAPI — mở session cho mỗi request rồi đóng lại."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
