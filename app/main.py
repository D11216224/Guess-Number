"""FastAPI application for the Guess Number web game."""

import uuid
from pathlib import Path
from typing import Optional

from fastapi import Cookie, FastAPI, HTTPException, Request, Response
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from app.database import create_tables
from app.game import create_game, get_user_stats, submit_guess

app = FastAPI(title="猜數字遊戲")

# Ensure tables exist on startup
create_tables()

# Mount static files
_static_dir = Path(__file__).parent.parent / "static"
if _static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(_static_dir)), name="static")

_template_path = Path(__file__).parent.parent / "templates" / "index.html"


# ---------------------------------------------------------------------------
# Cookie helper
# ---------------------------------------------------------------------------

COOKIE_NAME = "guess_user_id"


def _get_or_create_user_id(
    response: Response, user_id: Optional[str]
) -> str:
    if user_id:
        return user_id
    new_id = str(uuid.uuid4())
    response.set_cookie(COOKIE_NAME, new_id, max_age=60 * 60 * 24 * 365, httponly=True)
    return new_id


# ---------------------------------------------------------------------------
# Page route
# ---------------------------------------------------------------------------


@app.get("/", response_class=HTMLResponse)
async def index(request: Request, response: Response, guess_user_id: Optional[str] = Cookie(default=None)):
    _get_or_create_user_id(response, guess_user_id)
    html = _template_path.read_text(encoding="utf-8")
    return HTMLResponse(content=html)


# ---------------------------------------------------------------------------
# Pydantic schemas
# ---------------------------------------------------------------------------


class GameCreateResponse(BaseModel):
    game_id: str
    status: str
    guess_count: int


class GuessRequest(BaseModel):
    value: int = Field(..., ge=1, le=100, description="猜測值 (1~100)")


class GuessResponse(BaseModel):
    result: str
    message: str
    guess_count: int
    status: str


# ---------------------------------------------------------------------------
# API routes
# ---------------------------------------------------------------------------


@app.post("/api/games", response_model=GameCreateResponse)
async def api_create_game(
    response: Response,
    guess_user_id: Optional[str] = Cookie(default=None),
):
    user_id = _get_or_create_user_id(response, guess_user_id)
    game = create_game(user_id)
    return GameCreateResponse(game_id=game.id, status=game.status, guess_count=game.guess_count)


@app.post("/api/games/{game_id}/guess", response_model=GuessResponse)
async def api_guess(
    game_id: str,
    body: GuessRequest,
    response: Response,
    guess_user_id: Optional[str] = Cookie(default=None),
):
    user_id = _get_or_create_user_id(response, guess_user_id)
    try:
        result = submit_guess(game_id, user_id, body.value)
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return GuessResponse(**result)


@app.get("/api/users/me/stats")
async def api_user_stats(
    response: Response,
    guess_user_id: Optional[str] = Cookie(default=None),
):
    user_id = _get_or_create_user_id(response, guess_user_id)
    return get_user_stats(user_id)
