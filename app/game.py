"""Game logic for the Guess Number game."""

import random
import uuid
from datetime import datetime, timezone

from app.database import Game, GuessLog, get_session


def create_game(user_id: str) -> Game:
    """Create a new game session for the given user."""
    session = get_session()
    game = Game(
        id=str(uuid.uuid4()),
        user_id=user_id,
        answer=random.randint(1, 100),
        guess_count=0,
        status="playing",
        started_at=datetime.now(timezone.utc),
    )
    session.add(game)
    session.commit()
    session.refresh(game)
    session.close()
    return game


def submit_guess(game_id: str, user_id: str, value: int) -> dict:
    """
    Submit a guess for the given game.

    Returns a dict with keys: result, message, guess_count, status.
    Raises ValueError for invalid input or game state.
    """
    if not (1 <= value <= 100):
        raise ValueError("猜測值需在 1～100 之間")

    session = get_session()
    game = session.get(Game, game_id)

    if game is None:
        session.close()
        raise ValueError("找不到遊戲")

    if game.user_id != user_id:
        session.close()
        raise PermissionError("無法存取此遊戲")

    if game.status == "finished":
        session.close()
        raise ValueError("本局已結束，請開始新局")

    game.guess_count += 1

    if value > game.answer:
        result = "too_high"
        message = "大了"
    elif value < game.answer:
        result = "too_low"
        message = "小了"
    else:
        result = "correct"
        message = "恭喜通過！"
        game.status = "finished"
        game.finished_at = datetime.now(timezone.utc)

    log = GuessLog(
        game_id=game_id,
        guess_value=value,
        result=result,
        created_at=datetime.now(timezone.utc),
    )
    session.add(log)
    session.commit()

    response = {
        "result": result,
        "message": message,
        "guess_count": game.guess_count,
        "status": game.status,
    }
    session.close()
    return response


def get_user_stats(user_id: str, recent_n: int = 10) -> dict:
    """Return statistics for the given user."""
    from sqlalchemy import select

    session = get_session()
    stmt = (
        select(Game)
        .where(Game.user_id == user_id, Game.status == "finished")
        .order_by(Game.finished_at.desc())
    )
    finished_games = session.execute(stmt).scalars().all()

    if not finished_games:
        session.close()
        return {
            "total_games": 0,
            "best_guess_count": None,
            "avg_last_5": None,
            "avg_last_10": None,
            "recent_games": [],
        }

    counts = [g.guess_count for g in finished_games]
    best = min(counts)
    avg5 = round(sum(counts[:5]) / min(len(counts), 5), 2)
    avg10 = round(sum(counts[:10]) / min(len(counts), 10), 2)

    recent = [
        {
            "game_id": g.id,
            "finished_at": g.finished_at.isoformat() if g.finished_at else None,
            "guess_count": g.guess_count,
        }
        for g in finished_games[:recent_n]
    ]

    session.close()
    return {
        "total_games": len(finished_games),
        "best_guess_count": best,
        "avg_last_5": avg5,
        "avg_last_10": avg10,
        "recent_games": recent,
    }
