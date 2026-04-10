"""Database setup and models for the Guess Number game."""

import os
import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, create_engine
from sqlalchemy.orm import DeclarativeBase, Session, relationship
from sqlalchemy.pool import StaticPool

DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///./guess_number.db")

_is_memory = DATABASE_URL == "sqlite:///:memory:"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    **({"poolclass": StaticPool} if _is_memory else {}),
)


class Base(DeclarativeBase):
    pass


class Game(Base):
    __tablename__ = "games"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, nullable=False, index=True)
    answer = Column(Integer, nullable=False)
    guess_count = Column(Integer, default=0, nullable=False)
    status = Column(String, default="playing", nullable=False)  # playing / finished
    started_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    finished_at = Column(DateTime, nullable=True)

    guess_logs = relationship("GuessLog", back_populates="game", cascade="all, delete-orphan")


class GuessLog(Base):
    __tablename__ = "guess_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    game_id = Column(String, ForeignKey("games.id"), nullable=False)
    guess_value = Column(Integer, nullable=False)
    result = Column(String, nullable=False)  # too_high / too_low / correct
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    game = relationship("Game", back_populates="guess_logs")


def create_tables() -> None:
    Base.metadata.create_all(bind=engine)


def get_session() -> Session:
    return Session(engine)
