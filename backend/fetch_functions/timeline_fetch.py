import os
import time
import requests
from dotenv import load_dotenv

load_dotenv()
KEY = os.getenv("API_KEY")

PLATFORM_TO_CONTINENT = {
    "na1": "americas", "br1": "americas", "la1": "americas", "la2": "americas",
    "kr": "asia",      "jp1": "asia",
    "euw1": "europe",  "eun1": "europe", "tr1": "europe", "ru": "europe",
    "oc1": "sea",
}

SNAPSHOT_MINUTES = {5, 10, 15, 20, 25, 30}


def _get(url: str) -> dict | None:
    """GET with automatic rate-limit retry."""
    headers = {"X-Riot-Token": KEY}
    while True:
        r = requests.get(url, headers=headers)
        if r.status_code == 200:
            return r.json()
        if r.status_code == 429:
            wait = int(r.headers.get("Retry-After", 1))
            print(f"Rate limited. Waiting {wait}s...")
            time.sleep(wait)
            continue
        print(f"HTTP {r.status_code} fetching timeline for {url}")
        return None


def fetch_timeline(match_id: str, platform: str) -> dict | None:
    """Fetch the raw match timeline from the Riot Match v5 API."""
    continent = PLATFORM_TO_CONTINENT.get(platform.lower(), "americas")
    url = f"https://{continent}.api.riotgames.com/lol/match/v5/matches/{match_id}/timeline"
    return _get(url)


def extract_snapshots(timeline: dict, match_id: str) -> list[dict]:
    """
    Extract per-minute snapshots at each SNAPSHOT_MINUTES mark for every participant.

    Bypasses cassiopeia entirely — reads participant frames directly from the raw
    Riot timeline response and reconstructs KDA + items from the event log.

    Returns a flat list of snapshot dicts (one per player per timestamp),
    ready to pass straight to db.client.upsert_snapshots().
    """
    metadata = timeline.get("metadata", {})
    info = timeline.get("info", {})

    puuids = metadata.get("participants", [])
    frames = info.get("frames", [])

    if not frames or not puuids:
        return []

    num = len(puuids)

    minute_to_frame: dict[int, dict] = {}
    for frame in frames:
        minute = round(frame["timestamp"] / 60000)
        minute_to_frame[minute] = frame

    all_events = sorted(
        (e for frame in frames for e in frame.get("events", [])),
        key=lambda e: e["timestamp"],
    )

    kills   = [0] * num
    deaths  = [0] * num
    assists = [0] * num
    items: list[list[int]] = [[] for _ in range(num)]

    kda_at: dict[int, list[tuple[int, int, int]]] = {}
    items_at: dict[int, list[list[int]]] = {}

    event_idx = 0
    for minute in sorted(SNAPSHOT_MINUTES):
        cutoff_ms = minute * 60 * 1000

        while event_idx < len(all_events):
            event = all_events[event_idx]
            if event["timestamp"] > cutoff_ms:
                break

            etype = event.get("type")

            if etype == "CHAMPION_KILL":
                killer = event.get("killerId", 0)
                victim = event.get("victimId", 0)
                if 1 <= killer <= num:
                    kills[killer - 1] += 1
                if 1 <= victim <= num:
                    deaths[victim - 1] += 1
                for aid in event.get("assistingParticipantIds", []):
                    if 1 <= aid <= num:
                        assists[aid - 1] += 1

            elif etype == "ITEM_PURCHASED":
                pid = event.get("participantId", 0)
                item_id = event.get("itemId")
                if 1 <= pid <= num and item_id:
                    items[pid - 1].append(item_id)

            elif etype in ("ITEM_SOLD", "ITEM_DESTROYED"):
                pid = event.get("participantId", 0)
                item_id = event.get("itemId")
                if 1 <= pid <= num and item_id and item_id in items[pid - 1]:
                    items[pid - 1].remove(item_id)

            elif etype == "ITEM_UNDO":
                pid = event.get("participantId", 0)
                before = event.get("beforeId", 0)
                after = event.get("afterId", 0)
                if 1 <= pid <= num:
                    if before and before in items[pid - 1]:
                        items[pid - 1].remove(before)
                    if after:
                        items[pid - 1].append(after)

            event_idx += 1

        kda_at[minute]   = [(kills[i], deaths[i], assists[i]) for i in range(num)]
        items_at[minute] = [list(items[i]) for i in range(num)]

    snapshots = []
    for minute in SNAPSHOT_MINUTES:
        frame = minute_to_frame.get(minute)
        if not frame:
            continue

        p_frames = frame.get("participantFrames", {})

        for idx, puuid in enumerate(puuids):
            p_frame = p_frames.get(str(idx + 1))
            if not p_frame:
                continue

            k, d, a = kda_at.get(minute, [])[idx] if kda_at.get(minute) else (0, 0, 0)

            snapshots.append({
                "match_id":         match_id,
                "puuid":            puuid,
                "timestamp_minute": minute,
                "cs":               p_frame.get("minionsKilled", 0),
                "gold":             p_frame.get("totalGold", 0),
                "xp":               p_frame.get("xp", 0),
                "kills":            k,
                "deaths":           d,
                "assists":          a,
                "vision_score":     None,
                "items":            items_at.get(minute, [[]] * num)[idx],
            })

    return snapshots