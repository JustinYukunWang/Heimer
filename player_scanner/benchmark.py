import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from db.client import get_session
from sqlalchemy import text


_VALID_RANKS = frozenset({'CHALLENGER', 'GRANDMASTER', 'MASTER'})


async def get_benchmark(
    role: str | None = None,
    champion: str | None = None,
    ranks: list[str] | None = None,
) -> dict[int, dict]:
    """
    Query Neon for per-minute averages filtered by rank tier, role, and/or champion.
    ranks defaults to all three tiers; pass a subset to compare against e.g. Challenger only.
    """
    selected = [r for r in (ranks or _VALID_RANKS) if r in _VALID_RANKS] or list(_VALID_RANKS)
    # Values are validated against a whitelist — safe to interpolate
    rank_sql = ', '.join(f"'{r}'" for r in selected)
    conditions = [f"pl.rank IN ({rank_sql})"]
    params: dict = {}

    if role:
        conditions.append("UPPER(p.role) = UPPER(:role)")
        params["role"] = role
    if champion:
        conditions.append("LOWER(p.champion) = LOWER(:champion)")
        params["champion"] = champion

    where = " AND ".join(conditions)

    query = text(f"""
        SELECT
            ts.timestamp_minute,
            AVG(ts.cs)      AS avg_cs,
            AVG(ts.gold)    AS avg_gold,
            AVG(ts.xp)      AS avg_xp,
            AVG(ts.level)   AS avg_level,
            AVG(ts.kills)   AS avg_kills,
            AVG(ts.deaths)  AS avg_deaths,
            AVG(ts.assists) AS avg_assists
        FROM timeline_snapshots ts
        JOIN participants p ON ts.match_id = p.match_id AND ts.puuid = p.puuid
        JOIN players     pl ON ts.puuid = pl.puuid
        WHERE {where}
        GROUP BY ts.timestamp_minute
        ORDER BY ts.timestamp_minute
    """)

    async with get_session() as db:
        result = await db.execute(query, params)
        rows = result.fetchall()

    return {
        row[0]: {
            "cs":      round(float(row[1]), 1) if row[1] is not None else None,
            "gold":    round(float(row[2]), 0) if row[2] is not None else None,
            "xp":      round(float(row[3]), 0) if row[3] is not None else None,
            "level":   round(float(row[4]), 1) if row[4] is not None else None,
            "kills":   round(float(row[5]), 2) if row[5] is not None else None,
            "deaths":  round(float(row[6]), 2) if row[6] is not None else None,
            "assists": round(float(row[7]), 2) if row[7] is not None else None,
        }
        for row in rows
    }