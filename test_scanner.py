import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from player_scanner import scan_player, compute_filtered_analysis, get_per_minute_comparison


async def main():
    print("Scanning Thekun#Wang on NA1...\n")

    result = await scan_player("Thekun", "Wang", platform="na1")

    if "error" in result:
        print(f"ERROR: {result['error']}")
        return

    profile = result["profile"]
    matches = result["recent_matches"]
    pool    = result["champion_pool"]

    print("=" * 50)
    print("PROFILE")
    print("=" * 50)
    print(f"  Name:    {profile.game_name}#{profile.tag_line}")
    print(f"  Level:   {profile.summoner_level}")
    print(f"  Rank:    {profile.rank} — {profile.lp} LP")
    print(f"  W/L:     {profile.wins}W / {profile.losses}L  ({profile.winrate:.1%})")
    print(f"  Icon:    {profile.profile_icon_url}")

    print(f"\n{'=' * 50}")
    print(f"RECENT MATCHES ({len(matches)} fetched)")
    print("=" * 50)
    for m in matches[:5]:
        result_str = "WIN" if m.win else "LOSS"
        print(f"  [{result_str}] {m.champion:<15} {m.role:<10} {m.kills}/{m.deaths}/{m.assists}  CS:{m.cs}  Patch:{m.patch}")

    print(f"\n{'=' * 50}")
    print("CHAMPION POOL")
    print("=" * 50)
    for c in pool[:5]:
        print(f"  {c.champion:<15} {c.games}g  {c.winrate:.1%} WR  {c.avg_kills:.1f}/{c.avg_deaths:.1f}/{c.avg_assists:.1f}")

    # Pick most-played champion for filtered analysis
    if pool:
        top_champ = pool[0].champion
        print(f"\n{'=' * 50}")
        print(f"FILTERED ANALYSIS — {top_champ}")
        print("=" * 50)
        analysis = compute_filtered_analysis(matches, champion=top_champ)
        if analysis:
            print(f"  Games:     {analysis.games_analyzed}")
            print(f"  Winrate:   {analysis.winrate:.1%}")
            print(f"  KDA:       {analysis.avg_kills:.1f}/{analysis.avg_deaths:.1f}/{analysis.avg_assists:.1f}")
            print(f"  CS/min:    {analysis.avg_cs_per_min:.1f}")
            print(f"  Gold/min:  {analysis.avg_gold_per_min:.0f}")
            print(f"  Avg vision:{analysis.avg_vision_score:.1f}")
            print(f"  Avg dmg:   {analysis.avg_damage:.0f}")

        print(f"\n{'=' * 50}")
        print(f"PER-MINUTE COMPARISON — {top_champ} vs Master+")
        print("=" * 50)
        snapshots = await get_per_minute_comparison(matches, profile.puuid, champion=top_champ)
        if snapshots:
            print(f"  {'Min':>4}  {'CS(you)':>8} {'CS(M+)':>8}  {'Gold(you)':>10} {'Gold(M+)':>10}  {'KDA(you)':>10}")
            for s in snapshots:
                b_cs   = f"{s.benchmark_cs:.1f}" if s.benchmark_cs is not None else "  N/A"
                b_gold = f"{s.benchmark_gold:.0f}" if s.benchmark_gold is not None else "   N/A"
                print(f"  {s.timestamp_minute:>4}  {s.player_cs:>8.1f} {b_cs:>8}  {s.player_gold:>10.0f} {b_gold:>10}  {s.player_kills:.1f}/{s.player_deaths:.1f}/{s.player_assists:.1f}")
        else:
            print("  No timeline data yet (DB may not have Master+ data for this champion)")


if __name__ == "__main__":
    asyncio.run(main())