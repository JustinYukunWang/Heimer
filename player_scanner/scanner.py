import asyncio
import aiohttp
import os
import sys
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone

from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from backend.fetch_functions.timeline_fetch import extract_snapshots
from player_scanner.benchmark import get_benchmark

load_dotenv()
KEY = os.getenv("API_KEY")

PLATFORM_TO_CONTINENT = {
    "na1": "americas", "br1": "americas", "la1": "americas", "la2": "americas",
    "kr": "asia",      "jp1": "asia",
    "euw1": "europe",  "eun1": "europe", "tr1": "europe", "ru": "europe",
    "oc1": "sea",
}

_sem = asyncio.Semaphore(5)


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class PlayerProfile:
    puuid: str
    game_name: str
    tag_line: str
    summoner_level: int
    profile_icon_url: str
    rank: str           # e.g. "PLATINUM II" or "Unranked"
    lp: int
    wins: int
    losses: int
    winrate: float      # 0.0 – 1.0


@dataclass
class MatchSummary:
    match_id: str
    champion: str
    role: str
    kills: int
    deaths: int
    assists: int
    cs: int
    gold: int
    damage: int
    vision_score: int
    win: bool
    duration: int       # seconds
    game_timestamp: datetime
    items: list
    patch: str


@dataclass
class ChampionStats:
    champion: str
    games: int
    wins: int
    winrate: float
    avg_kills: float
    avg_deaths: float
    avg_assists: float


@dataclass
class FilteredAnalysis:
    games_analyzed: int
    winrate: float
    avg_kills: float
    avg_deaths: float
    avg_assists: float
    avg_cs_per_min: float
    avg_gold_per_min: float
    avg_vision_score: float
    avg_damage: float


@dataclass
class PerMinuteSnapshot:
    timestamp_minute: int
    player_cs: float
    player_gold: float
    player_xp: float
    player_level: float
    player_kills: float
    player_deaths: float
    player_assists: float
    benchmark_cs: float | None
    benchmark_gold: float | None
    benchmark_xp: float | None
    benchmark_level: float | None
    benchmark_kills: float | None
    benchmark_deaths: float | None
    benchmark_assists: float | None


# ---------------------------------------------------------------------------
# Riot API helpers
# ---------------------------------------------------------------------------

async def _get(http: aiohttp.ClientSession, url: str) -> dict | list | None:
    async with _sem:
        while True:
            async with http.get(url, headers={"X-Riot-Token": KEY}) as r:
                if r.status == 200:
                    return await r.json()
                if r.status == 429:
                    wait = int(r.headers.get("Retry-After", 1))
                    await asyncio.sleep(wait)
                    continue
                return None


async def _latest_ddragon_version(http: aiohttp.ClientSession) -> str:
    async with http.get("https://ddragon.leagueoflegends.com/api/versions.json") as r:
        versions = await r.json() if r.status == 200 else []
        return versions[0] if versions else "15.1.1"


async def _fetch_account(http, game_name: str, tag_line: str, platform: str) -> dict | None:
    continent = PLATFORM_TO_CONTINENT.get(platform.lower(), "americas")
    return await _get(http, f"https://{continent}.api.riotgames.com/riot/account/v1/accounts/by-riot-id/{game_name}/{tag_line}")


async def _fetch_summoner(http, puuid: str, platform: str) -> dict | None:
    return await _get(http, f"https://{platform}.api.riotgames.com/lol/summoner/v4/summoners/by-puuid/{puuid}")


async def _fetch_rank(http, summoner_id: str, platform: str) -> dict | None:
    data = await _get(http, f"https://{platform}.api.riotgames.com/lol/league/v4/entries/by-summoner/{summoner_id}")
    if not data:
        return None
    return next((e for e in data if e.get("queueType") == "RANKED_SOLO_5x5"), None)


async def _fetch_match_ids(http, puuid: str, platform: str, count: int = 20) -> list[str]:
    continent = PLATFORM_TO_CONTINENT.get(platform.lower(), "americas")
    data = await _get(http, f"https://{continent}.api.riotgames.com/lol/match/v5/matches/by-puuid/{puuid}/ids?queue=420&count={count}")
    return data if isinstance(data, list) else []


async def _fetch_match(http, match_id: str, platform: str) -> dict | None:
    continent = PLATFORM_TO_CONTINENT.get(platform.lower(), "americas")
    return await _get(http, f"https://{continent}.api.riotgames.com/lol/match/v5/matches/{match_id}")


async def _fetch_timeline(http, match_id: str, platform: str) -> dict | None:
    continent = PLATFORM_TO_CONTINENT.get(platform.lower(), "americas")
    return await _get(http, f"https://{continent}.api.riotgames.com/lol/match/v5/matches/{match_id}/timeline")


# ---------------------------------------------------------------------------
# Parsing
# ---------------------------------------------------------------------------

def _parse_match_summary(raw: dict, puuid: str) -> MatchSummary | None:
    info = raw.get("info", {})
    for p in info.get("participants", []):
        if p["puuid"] != puuid:
            continue
        return MatchSummary(
            match_id=raw["metadata"]["matchId"],
            champion=p.get("championName", ""),
            role=p.get("teamPosition") or p.get("individualPosition", ""),
            kills=p.get("kills", 0),
            deaths=p.get("deaths", 0),
            assists=p.get("assists", 0),
            cs=p.get("totalMinionsKilled", 0) + p.get("neutralMinionsKilled", 0),
            gold=p.get("goldEarned", 0),
            damage=p.get("totalDamageDealtToChampions", 0),
            vision_score=p.get("visionScore", 0),
            win=p.get("win", False),
            duration=info.get("gameDuration", 0),
            game_timestamp=datetime.fromtimestamp(info.get("gameCreation", 0) / 1000, tz=timezone.utc),
            items=[p[f"item{i}"] for i in range(7) if p.get(f"item{i}")],
            patch=".".join(info.get("gameVersion", "").split(".")[:2]),
        )
    return None


def _build_champion_pool(matches: list[MatchSummary]) -> list[ChampionStats]:
    stats: dict = defaultdict(lambda: {"games": 0, "wins": 0, "kills": 0, "deaths": 0, "assists": 0})
    for m in matches:
        s = stats[m.champion]
        s["games"] += 1
        s["wins"] += int(m.win)
        s["kills"] += m.kills
        s["deaths"] += m.deaths
        s["assists"] += m.assists
    return sorted([
        ChampionStats(
            champion=champ,
            games=(g := s["games"]),
            wins=s["wins"],
            winrate=s["wins"] / g,
            avg_kills=s["kills"] / g,
            avg_deaths=s["deaths"] / g,
            avg_assists=s["assists"] / g,
        )
        for champ, s in stats.items()
    ], key=lambda x: x.games, reverse=True)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

async def scan_player(game_name: str, tag_line: str, platform: str = "na1") -> dict:
    """
    Fetch a player's full profile, last 20 ranked matches, and champion pool.
    All data is fetched on-demand from Riot API — nothing stored in DB.
    """
    async with aiohttp.ClientSession() as http:
        account = await _fetch_account(http, game_name, tag_line, platform)
        if not account:
            return {"error": f"Player '{game_name}#{tag_line}' not found."}

        puuid = account["puuid"]

        # Parallel: summoner data, match IDs, DDragon version
        summoner, match_ids, ddragon_version = await asyncio.gather(
            _fetch_summoner(http, puuid, platform),
            _fetch_match_ids(http, puuid, platform),
            _latest_ddragon_version(http),
        )

        if not summoner:
            return {"error": "Could not fetch summoner data."}

        # Rank needs summoner ID — one sequential step
        rank_data = await _fetch_rank(http, summoner["id"], platform)

        # Build profile
        icon_id = summoner.get("profileIconId", 0)
        total_games = (rank_data["wins"] + rank_data["losses"]) if rank_data else 0
        profile = PlayerProfile(
            puuid=puuid,
            game_name=account["gameName"],
            tag_line=account["tagLine"],
            summoner_level=summoner.get("summonerLevel", 0),
            profile_icon_url=f"https://ddragon.leagueoflegends.com/cdn/{ddragon_version}/img/profileicon/{icon_id}.png",
            rank=f"{rank_data['tier']} {rank_data['rank']}" if rank_data else "Unranked",
            lp=rank_data.get("leaguePoints", 0) if rank_data else 0,
            wins=rank_data.get("wins", 0) if rank_data else 0,
            losses=rank_data.get("losses", 0) if rank_data else 0,
            winrate=rank_data["wins"] / total_games if total_games > 0 else 0.0,
        )

        # Fetch all 20 matches in parallel
        match_raws = await asyncio.gather(*[_fetch_match(http, mid, platform) for mid in match_ids])
        matches = [m for raw in match_raws if raw for m in [_parse_match_summary(raw, puuid)] if m]

        return {
            "profile": profile,
            "recent_matches": matches,
            "champion_pool": _build_champion_pool(matches),
        }


def compute_filtered_analysis(
    matches: list[MatchSummary],
    role: str | None = None,
    champion: str | None = None,
) -> FilteredAnalysis | None:
    """
    Compute aggregate stats from a filtered subset of matches.
    Call this after scan_player() to analyze a specific role/champion.
    """
    filtered = [
        m for m in matches
        if (role is None or m.role.upper() == role.upper())
        and (champion is None or m.champion.lower() == champion.lower())
    ]
    if not filtered:
        return None

    n = len(filtered)
    wins = sum(1 for m in filtered if m.win)
    durations = [m.duration / 60 for m in filtered]

    return FilteredAnalysis(
        games_analyzed=n,
        winrate=wins / n,
        avg_kills=sum(m.kills for m in filtered) / n,
        avg_deaths=sum(m.deaths for m in filtered) / n,
        avg_assists=sum(m.assists for m in filtered) / n,
        avg_cs_per_min=sum(m.cs / d for m, d in zip(filtered, durations)) / n,
        avg_gold_per_min=sum(m.gold / d for m, d in zip(filtered, durations)) / n,
        avg_vision_score=sum(m.vision_score for m in filtered) / n,
        avg_damage=sum(m.damage for m in filtered) / n,
    )


async def get_per_minute_comparison(
    matches: list[MatchSummary],
    puuid: str,
    platform: str = "na1",
    role: str | None = None,
    champion: str | None = None,
) -> list[PerMinuteSnapshot]:
    """
    Fetch timelines for filtered matches, average the player's per-minute stats,
    then query Neon for the Master+ benchmark and return a side-by-side comparison.
    """
    filtered = [
        m for m in matches
        if (role is None or m.role.upper() == role.upper())
        and (champion is None or m.champion.lower() == champion.lower())
    ]
    if not filtered:
        return []

    async with aiohttp.ClientSession() as http:
        timelines = await asyncio.gather(*[_fetch_timeline(http, m.match_id, platform) for m in filtered])

    # Accumulate player stats across matches at each timestamp
    sums: dict = defaultdict(lambda: {k: 0 for k in ("cs", "gold", "xp", "level", "kills", "deaths", "assists", "count")})
    for timeline in timelines:
        if not timeline:
            continue
        match_id = timeline["metadata"]["matchId"]
        for s in extract_snapshots(timeline, match_id):
            if s["puuid"] != puuid:
                continue
            t = s["timestamp_minute"]
            for key in ("cs", "gold", "xp", "level", "kills", "deaths", "assists"):
                sums[t][key] += s.get(key) or 0
            sums[t]["count"] += 1

    # Fetch Master+ benchmark from Neon
    benchmark = await get_benchmark(role=role, champion=champion)

    results = []
    for minute in sorted(sums):
        d = sums[minute]
        n = d["count"]
        if n == 0:
            continue
        b = benchmark.get(minute, {})
        results.append(PerMinuteSnapshot(
            timestamp_minute=minute,
            player_cs=round(d["cs"] / n, 1),
            player_gold=round(d["gold"] / n, 0),
            player_xp=round(d["xp"] / n, 0),
            player_level=round(d["level"] / n, 1),
            player_kills=round(d["kills"] / n, 2),
            player_deaths=round(d["deaths"] / n, 2),
            player_assists=round(d["assists"] / n, 2),
            benchmark_cs=b.get("cs"),
            benchmark_gold=b.get("gold"),
            benchmark_xp=b.get("xp"),
            benchmark_level=b.get("level"),
            benchmark_kills=b.get("kills"),
            benchmark_deaths=b.get("deaths"),
            benchmark_assists=b.get("assists"),
        ))

    return results