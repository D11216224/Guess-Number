# Guess-Number 猜數字遊戲（Web）

A web-based number guessing game built with **FastAPI** (Python) and plain HTML/JS.

## Features

- Random 1–100 integer generated each game
- Real-time "大了 / 小了 / 恭喜通過！" feedback
- Guess count tracked per game
- Personal stats: best score, recent-5 average, full history
- Cookie-based user identification (no login required)

## Project Structure

```
├── app/
│   ├── __init__.py
│   ├── main.py        # FastAPI app & routes
│   ├── database.py    # SQLAlchemy models (Game, GuessLog)
│   └── game.py        # Core game logic
├── templates/
│   └── index.html     # Single-page frontend
├── tests/
│   └── test_game.py   # pytest unit & integration tests
├── requirements.txt
└── README.md
```

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run the server
uvicorn app.main:app --reload

# Open in browser
open http://localhost:8000
```

## API

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/games` | Start a new game |
| `POST` | `/api/games/{id}/guess` | Submit a guess `{"value": 42}` |
| `GET`  | `/api/users/me/stats` | Personal stats & history |

## Tests

```bash
pytest tests/
```