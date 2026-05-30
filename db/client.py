import os
import json
from contextlib import asynccontextmanager
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_async_engine(
    DATABASE_URL,
    pool_size=5,
    max_overflow=10,
    pool_pre_ping=True,       # re-validate connections after Neon auto-suspends
    connect_args={"ssl": True},
)
_Session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


@asynccontextmanager
async def get_session():
    async with _Session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def clear_all_tables(session: AsyncSession):
    """Truncate match data at the start of each run so data stays current.
    item_catalog is intentionally excluded — patch item data never changes.
    """
    await session.execute(text(
        "TRUNCATE timeline_snapshots, participants, matches, players RESTART IDENTITY CASCADE"
    ))


async def get_known_patches(session: AsyncSession) -> set[str]:
    """Return all patch versions already present in item_catalog."""
    result = await session.execute(text("SELECT DISTINCT patch FROM item_catalog"))
    return {row[0] for row in result.fetchall()}


async def upsert_item_catalog(session: AsyncSession, items: list[dict]):
    """Bulk-insert item definitions for a patch, skipping duplicates."""
    if not items:
        return
    for item in items:
        if isinstance(item.get("tags"), list):
            item["tags"] = json.dumps(item["tags"])
        if isinstance(item.get("stats"), dict):
            item["stats"] = json.dumps(item["stats"])
    await session.execute(
        text("""
            INSERT INTO item_catalog (item_id, patch, name, description, tags, stats)
            VALUES (:item_id, :patch, :name, :description, :tags, :stats)
            ON CONFLICT (item_id, patch) DO NOTHING
        """),
        items,
    )


async def ensure_players_exist(session: AsyncSession, puuids: list[str]):
    """Register PUUIDs that appeared as match participants but aren't tracked players.
    Uses DO NOTHING so it never overwrites rank/lp data for players we already know.
    """
    if not puuids:
        return
    rows = [{"puuid": p, "rank": "UNKNOWN", "lp": None, "region": "UNKNOWN"} for p in puuids]
    await session.execute(
        text("""
            INSERT INTO players (puuid, rank, lp, region)
            VALUES (:puuid, :rank, :lp, :region)
            ON CONFLICT (puuid) DO NOTHING
        """),
        rows,
    )


async def upsert_players(session: AsyncSession, players: list[dict]):
    """Insert players, updating rank/lp if the puuid already exists."""
    if not players:
        return
    await session.execute(
        text("""
            INSERT INTO players (puuid, rank, lp, region)
            VALUES (:puuid, :rank, :lp, :region)
            ON CONFLICT (puuid) DO UPDATE SET
                rank = EXCLUDED.rank,
                lp   = EXCLUDED.lp
        """),
        players,
    )


async def upsert_match(session: AsyncSession, match: dict):
    """Insert a match row, skipping if already stored."""
    await session.execute(
        text("""
            INSERT INTO matches (match_id, patch, duration, queue, game_timestamp)
            VALUES (:match_id, :patch, :duration, :queue, :game_timestamp)
            ON CONFLICT (match_id) DO NOTHING
        """),
        match,
    )


async def upsert_participants(session: AsyncSession, participants: list[dict]):
    """Insert participant rows for a match, skipping duplicates."""
    if not participants:
        return
    await session.execute(
        text("""
            INSERT INTO participants (match_id, puuid, champion, role, win)
            VALUES (:match_id, :puuid, :champion, :role, :win)
            ON CONFLICT (match_id, puuid) DO NOTHING
        """),
        participants,
    )


async def upsert_snapshots(session: AsyncSession, snapshots: list[dict]):
    """Insert timeline snapshots, skipping duplicates.
    Each snapshot dict must have an 'items' key that is a list — it will be
    serialised to JSON automatically.
    """
    if not snapshots:
        return
    for s in snapshots:
        if isinstance(s.get("items"), list):
            s["items"] = json.dumps(s["items"])
    await session.execute(
        text("""
            INSERT INTO timeline_snapshots
                (match_id, puuid, timestamp_minute, cs, gold, xp,
                 kills, deaths, assists, vision_score, items)
            VALUES
                (:match_id, :puuid, :timestamp_minute, :cs, :gold, :xp,
                 :kills, :deaths, :assists, :vision_score, :items)
            ON CONFLICT (match_id, puuid, timestamp_minute) DO NOTHING
        """),
        snapshots,
    )
