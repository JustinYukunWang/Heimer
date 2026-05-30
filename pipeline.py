"""
pipeline.py — MVP 1: Benchmark Dataset Collection

Pulls Challenger / Grandmaster / Master players from NA,
walks their recent ranked match history, and writes
players, matches, participants, and timeline snapshots
to the Supabase database.

Usage:
    python pipeline.py
"""

import asyncio
import aiohttp
import os
import sys
from datetime import datetime, timezone

from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(__file__))
from db.client import (
    get_session,
    ensure_players_exist,
    upsert_players,
    upsert_match,
    upsert_participants,
    upsert_snapshots,
)
from fetch_functions.timeline_fetch import extract_snapshots

load_dotenv()
KEY = os.getenv("API_KEY")

PLATFORM  = "na1"
CONTINENT = "americas"

MATCHES_PER_PLAYER = 10   # per player; keeps storage proportional

# Hard cap on total unique matches stored.
# At ~13 KB/match, 25k matches ≈ 325 MB — safe under Neon's 0.5 GB free tier.
MAX_MATCHES = 25_000

# Keep concurrent Riot API requests low on a dev key (20 req/s, 100 req/2 min).
_sem = asyncio.Semaphore(5)


# ---------------------------------------------------------------------------
# Riot API helpers
# ---------------------------------------------------------------------------

async def _get(http: aiohttp.ClientSession, url: str) -> dict | list | None:
    """Async GET with automatic 429 retry."""
    async with _sem:
        while True:
            async with http.get(url, headers={"X-Riot-Token": KEY}) as r:
                if r.status == 200:
                    return await r.json()
                if r.status == 429:
                    wait = int(r.headers.get("Retry-After", 1))
                    print(f"    Rate limited — waiting {wait}s...")
                    await asyncio.sleep(wait)
                    continue
                print(f"    HTTP {r.status}: {url}")
                return None


async def fetch_league_entries(http: aiohttp.ClientSession, tier: str) -> list[dict]:
    tier_key = {"CHALLENGER": "challenger", "GRANDMASTER": "grandmaster", "MASTER": "master"}[tier]
    url = (
        f"https://{PLATFORM}.api.riotgames.com"
        f"/lol/league/v4/{tier_key}leagues/by-queue/RANKED_SOLO_5x5"
    )
    data = await _get(http, url)
    return data.get("entries", []) if data else []


async def summoner_to_puuid(http: aiohttp.ClientSession, summoner_id: str) -> str | None:
    url = f"https://{PLATFORM}.api.riotgames.com/lol/summoner/v4/summoners/{summoner_id}"
    data = await _get(http, url)
    return data.get("puuid") if data else None


async def fetch_match_ids(http: aiohttp.ClientSession, puuid: str) -> list[str]:
    url = (
        f"https://{CONTINENT}.api.riotgames.com"
        f"/lol/match/v5/matches/by-puuid/{puuid}/ids"
        f"?queue=420&count={MATCHES_PER_PLAYER}"
    )
    data = await _get(http, url)
    return data if isinstance(data, list) else []


async def fetch_match_data(http: aiohttp.ClientSession, match_id: str) -> dict | None:
    url = f"https://{CONTINENT}.api.riotgames.com/lol/match/v5/matches/{match_id}"
    return await _get(http, url)


async def fetch_timeline_data(http: aiohttp.ClientSession, match_id: str) -> dict | None:
    url = f"https://{CONTINENT}.api.riotgames.com/lol/match/v5/matches/{match_id}/timeline"
    return await _get(http, url)


# ---------------------------------------------------------------------------
# Parsing
# ---------------------------------------------------------------------------

def parse_match(raw: dict) -> tuple[dict, list[dict]]:
    """Return (match_row, participant_rows) from a raw match API response."""
    info = raw.get("info", {})

    # Keep only major.minor from the full version string
    patch = ".".join(info.get("gameVersion", "").split(".")[:2])

    match_row = {
        "match_id":       raw["metadata"]["matchId"],
        "patch":          patch,
        "duration":       info.get("gameDuration"),
        "queue":          str(info.get("queueId", "")),
        "game_timestamp": datetime.fromtimestamp(
            info.get("gameCreation", 0) / 1000, tz=timezone.utc
        ),
    }

    participant_rows = [
        {
            "match_id": match_row["match_id"],
            "puuid":    p["puuid"],
            "champion": p.get("championName"),
            "role":     p.get("teamPosition") or p.get("individualPosition"),
            "win":      p.get("win"),
        }
        for p in info.get("participants", [])
    ]

    return match_row, participant_rows


# ---------------------------------------------------------------------------
# Core processing
# ---------------------------------------------------------------------------

async def process_match(
    http: aiohttp.ClientSession,
    match_id: str,
    processed: set[str],
    stats: dict,
):
    if match_id in processed:
        return
    processed.add(match_id)

    # Fetch match data and timeline in parallel — two requests per match
    match_data, timeline_data = await asyncio.gather(
        fetch_match_data(http, match_id),
        fetch_timeline_data(http, match_id),
    )

    if not match_data or not timeline_data:
        print(f"    Skipping {match_id} — incomplete API response")
        stats["skipped"] += 1
        return

    match_row, participant_rows = parse_match(match_data)
    snapshots = extract_snapshots(timeline_data, match_id)

    # Vision score is end-of-game only in the Riot API; attach it to all
    # timeline snapshots for the same player so it's available for analysis.
    vision_map = {
        p["puuid"]: p.get("visionScore")
        for p in match_data.get("info", {}).get("participants", [])
    }
    for s in snapshots:
        s["vision_score"] = vision_map.get(s["puuid"])

    participant_puuids = [p["puuid"] for p in participant_rows]

    async with get_session() as db:
        # Participants FK → players: ensure every PUUID in this match exists.
        await ensure_players_exist(db, participant_puuids)
        await upsert_match(db, match_row)
        await upsert_participants(db, participant_rows)
        await upsert_snapshots(db, snapshots)

    stats["matches"] += 1
    stats["snapshots"] += len(snapshots)
    print(f"    Stored {match_id}  ({len(snapshots)} snapshots, total: {stats['matches']} matches)")


async def process_player(
    http: aiohttp.ClientSession,
    entry: dict,
    tier: str,
    processed: set[str],
    stats: dict,
):
    lp = entry.get("leaguePoints", 0)

    # Newer Riot API responses include puuid directly on league entries.
    # Fall back to summonerId conversion for older response shapes.
    puuid = entry.get("puuid") or await summoner_to_puuid(http, entry.get("summonerId", ""))
    if not puuid:
        return

    async with get_session() as db:
        await upsert_players(db, [{"puuid": puuid, "rank": tier, "lp": lp, "region": PLATFORM}])

    match_ids = await fetch_match_ids(http, puuid)
    print(f"  [{tier:12s}] {puuid[:16]}…  LP={lp:4d}  matches={len(match_ids)}")

    for match_id in match_ids:
        if stats["matches"] >= MAX_MATCHES:
            return
        await process_match(http, match_id, processed, stats)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

async def main():
    processed: set[str] = set()
    stats = {"matches": 0, "snapshots": 0, "skipped": 0}

    async with aiohttp.ClientSession() as http:

        # Fetch all tier rosters up front
        print("Fetching league rosters...")
        tier_entries: dict[str, list[dict]] = {}
        for tier in ("CHALLENGER", "GRANDMASTER", "MASTER"):
            entries = await fetch_league_entries(http, tier)
            tier_entries[tier] = entries
            print(f"  {tier:12s} — {len(entries)} players")

        # Interleave players across tiers so storage is always balanced.
        # e.g. CHALL[0], GM[0], MASTER[0], CHALL[1], GM[1], MASTER[1], ...
        # This guarantees representation from every tier even if we hit MAX_MATCHES early.
        max_len = max(len(v) for v in tier_entries.values())
        ordered = []
        for i in range(max_len):
            for tier, entries in tier_entries.items():
                if i < len(entries):
                    ordered.append((tier, entries[i]))

        total_players = len(ordered)
        print(f"\n  {total_players} total players — processing in round-robin order\n")

        for i, (tier, entry) in enumerate(ordered, 1):
            if stats["matches"] >= MAX_MATCHES:
                print(f"\n  Match cap ({MAX_MATCHES:,}) reached — stopping early.")
                break
            print(f"  [{i}/{total_players}] {tier}")
            await process_player(http, entry, tier, processed, stats)

    print(f"\n{'='*50}")
    print(f"Pipeline complete.")
    print(f"  Matches stored  : {stats['matches']:,}")
    print(f"  Snapshots stored: {stats['snapshots']:,}")
    print(f"  Matches skipped : {stats['skipped']:,}")


if __name__ == "__main__":
    asyncio.run(main())