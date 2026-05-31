import dataclasses
import sys
import os
from datetime import datetime, timedelta, timezone

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.encoders import jsonable_encoder

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from player_scanner import (
    scan_player,
    compute_filtered_analysis,
    get_per_minute_comparison,
)

app = FastAPI(title="Heimer API", version="0.1.0")

_origins = os.getenv("ALLOWED_ORIGINS", "*").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Simple in-memory cache  {cache_key: (data, expires_at)}
# Avoids redundant Riot API calls when analysis + timeline hit back-to-back.
# ---------------------------------------------------------------------------
_cache: dict = {}
_CACHE_TTL = timedelta(minutes=5)


def _cache_key(game_name: str, tag_line: str, platform: str) -> str:
    return f"{game_name}#{tag_line}@{platform}".lower()


async def _get_scan(game_name: str, tag_line: str, platform: str) -> dict:
    key = _cache_key(game_name, tag_line, platform)
    now = datetime.now(tz=timezone.utc)
    if key in _cache:
        data, expires = _cache[key]
        if now < expires:
            return data
    data = await scan_player(game_name, tag_line, platform)
    if "error" not in data:
        _cache[key] = (data, now + _CACHE_TTL)
    return data


def _serialize(obj) -> dict:
    """Convert a dataclass (possibly nested) to a JSON-safe dict."""
    return jsonable_encoder(dataclasses.asdict(obj))


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.get("/player/{game_name}/{tag_line}")
async def get_player(
    game_name: str,
    tag_line: str,
    platform: str = Query(default="na1"),
):
    """
    Full player scan: profile, last 20 ranked matches, champion pool.
    Results are cached for 5 minutes.
    """
    data = await _get_scan(game_name, tag_line, platform)
    if "error" in data:
        raise HTTPException(status_code=404, detail=data["error"])

    return {
        "profile":        _serialize(data["profile"]),
        "recent_matches": [_serialize(m) for m in data["recent_matches"]],
        "champion_pool":  [_serialize(c) for c in data["champion_pool"]],
    }


@app.get("/player/{game_name}/{tag_line}/analysis")
async def get_analysis(
    game_name: str,
    tag_line: str,
    platform: str = Query(default="na1"),
    role:     str | None = Query(default=None),
    champion: str | None = Query(default=None),
):
    """
    Aggregate stats for a player filtered by role and/or champion.
    Returns None (204) if no matching games found.
    """
    data = await _get_scan(game_name, tag_line, platform)
    if "error" in data:
        raise HTTPException(status_code=404, detail=data["error"])

    analysis = compute_filtered_analysis(data["recent_matches"], role=role, champion=champion)
    if analysis is None:
        raise HTTPException(
            status_code=404,
            detail=f"No games found for {game_name} playing {champion or 'any champion'} as {role or 'any role'}.",
        )

    return _serialize(analysis)


@app.get("/player/{game_name}/{tag_line}/timeline")
async def get_timeline(
    game_name: str,
    tag_line:  str,
    platform:  str = Query(default="na1"),
    role:      str | None = Query(default=None),
    champion:  str | None = Query(default=None),
    ranks:     list[str] = Query(default=["CHALLENGER", "GRANDMASTER", "MASTER"]),
):
    """
    Per-minute stats vs benchmark for filtered matches.
    ranks controls which tier(s) to benchmark against — default all three.
    """
    data = await _get_scan(game_name, tag_line, platform)
    if "error" in data:
        raise HTTPException(status_code=404, detail=data["error"])

    puuid = data["profile"].puuid
    snapshots = await get_per_minute_comparison(
        data["recent_matches"], puuid, platform=platform,
        role=role, champion=champion, ranks=ranks,
    )

    return [_serialize(s) for s in snapshots]


@app.get("/health")
async def health():
    return {"status": "ok"}