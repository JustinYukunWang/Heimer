import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from db.client import get_session
from sqlalchemy import text


async def get_benchmark(role: str | None = None, champion: str | None = None) -> dict[int, dict]:
    """
    Query Neon for Master+/GM/Challenger average per-minute stats.
    Returns dict keyed by timestamp_minute → {cs, gold, xp, level, kills, deaths, assists}.
    Optionally filtered by role and/or champion.
    """
    conditions = ["pl.rank IN ('CHALLENGER', 'GRANDMASTER', 'MASTER')"]
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