"""Unit tests for the Guess Number game."""

import pytest
from fastapi.testclient import TestClient

# Use an in-memory SQLite DB for tests
import os
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

from app.database import Base, engine, create_tables
from app.main import app


@pytest.fixture(autouse=True)
def setup_db():
    """Create all tables before each test and drop them after."""
    create_tables()
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client():
    return TestClient(app, raise_server_exceptions=True)


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def new_game(client: TestClient) -> dict:
    resp = client.post("/api/games")
    assert resp.status_code == 200
    return resp.json()


# ---------------------------------------------------------------------------
# POST /api/games
# ---------------------------------------------------------------------------

def test_create_game_returns_playing_status(client):
    data = new_game(client)
    assert data["status"] == "playing"
    assert data["guess_count"] == 0
    assert "game_id" in data


# ---------------------------------------------------------------------------
# POST /api/games/{id}/guess
# ---------------------------------------------------------------------------

def test_guess_too_high(client, monkeypatch):
    """When guess > answer, result should be too_high."""
    import app.game as game_module
    monkeypatch.setattr(game_module.random, "randint", lambda a, b: 50)
    game = new_game(client)
    resp = client.post(f"/api/games/{game['game_id']}/guess", json={"value": 75})
    assert resp.status_code == 200
    data = resp.json()
    assert data["result"] == "too_high"
    assert data["message"] == "大了"
    assert data["guess_count"] == 1
    assert data["status"] == "playing"


def test_guess_too_low(client, monkeypatch):
    """When guess < answer, result should be too_low."""
    import app.game as game_module
    monkeypatch.setattr(game_module.random, "randint", lambda a, b: 50)
    game = new_game(client)
    resp = client.post(f"/api/games/{game['game_id']}/guess", json={"value": 25})
    assert resp.status_code == 200
    data = resp.json()
    assert data["result"] == "too_low"
    assert data["message"] == "小了"
    assert data["status"] == "playing"


def test_guess_correct(client, monkeypatch):
    """When guess == answer, result should be correct and game finishes."""
    import app.game as game_module
    monkeypatch.setattr(game_module.random, "randint", lambda a, b: 42)
    game = new_game(client)
    resp = client.post(f"/api/games/{game['game_id']}/guess", json={"value": 42})
    assert resp.status_code == 200
    data = resp.json()
    assert data["result"] == "correct"
    assert data["message"] == "恭喜通過！"
    assert data["status"] == "finished"


def test_guess_count_increments(client, monkeypatch):
    """Each valid guess increments guess_count by 1."""
    import app.game as game_module
    monkeypatch.setattr(game_module.random, "randint", lambda a, b: 80)
    game = new_game(client)
    gid = game["game_id"]
    for i in range(1, 4):
        resp = client.post(f"/api/games/{gid}/guess", json={"value": i})
        assert resp.json()["guess_count"] == i


def test_guess_out_of_range_rejected(client):
    """Guesses outside 1-100 should be rejected with 422."""
    game = new_game(client)
    gid = game["game_id"]
    assert client.post(f"/api/games/{gid}/guess", json={"value": 0}).status_code == 422
    assert client.post(f"/api/games/{gid}/guess", json={"value": 101}).status_code == 422


def test_guess_after_finished_rejected(client, monkeypatch):
    """Guessing on a finished game should return 400."""
    import app.game as game_module
    monkeypatch.setattr(game_module.random, "randint", lambda a, b: 7)
    game = new_game(client)
    gid = game["game_id"]
    client.post(f"/api/games/{gid}/guess", json={"value": 7})
    resp = client.post(f"/api/games/{gid}/guess", json={"value": 7})
    assert resp.status_code == 400


def test_guess_wrong_game_id(client):
    """Guessing on a non-existent game should return 400."""
    resp = client.post("/api/games/nonexistent-id/guess", json={"value": 50})
    assert resp.status_code == 400


# ---------------------------------------------------------------------------
# GET /api/users/me/stats
# ---------------------------------------------------------------------------

def test_stats_empty(client):
    resp = client.get("/api/users/me/stats")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_games"] == 0
    assert data["best_guess_count"] is None
    assert data["recent_games"] == []


def test_stats_after_games(client, monkeypatch):
    """After finishing games, stats should reflect results."""
    import app.game as game_module

    answers = [10, 20, 30]
    for answer in answers:
        monkeypatch.setattr(game_module.random, "randint", lambda a, b, _ans=answer: _ans)
        game = new_game(client)
        gid = game["game_id"]
        # make a wrong guess first to inflate count
        if answer != 10:
            client.post(f"/api/games/{gid}/guess", json={"value": 1})
        client.post(f"/api/games/{gid}/guess", json={"value": answer})

    resp = client.get("/api/users/me/stats")
    data = resp.json()
    assert data["total_games"] == 3
    assert data["best_guess_count"] == 1  # first game was solved in 1 guess
    assert len(data["recent_games"]) == 3


# ---------------------------------------------------------------------------
# Page route
# ---------------------------------------------------------------------------

def test_index_page_returns_html(client):
    resp = client.get("/")
    assert resp.status_code == 200
    assert "text/html" in resp.headers["content-type"]
    assert "猜數字遊戲" in resp.text
