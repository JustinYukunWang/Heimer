import datetime
import cassiopeia as cass
from cassiopeia import Account
from cassiopeia.data import Queue
import pandas as pd
from collections import defaultdict
import os

cass.set_riot_api_key("RGAPI-17a738d9-a905-4101-a9b0-4e69e76bd377")

cass.apply_settings({
    "caching": {
        "enabled": True,
        "cache_expiry": 3600  # Cache data for 1 hour
    }
})

def player_data_with_name(name: str, tagline: str, region: str, target_count: int):
    account = Account(name=name, tagline=tagline, region=region)
    summoner = account.summoner
    match_history = cass.get_match_history(
        continent=summoner.region.continent,
        puuid=summoner.puuid,
        queue=Queue.ranked_solo_fives,
    )

    # Desired timestamps to track
    desired_timestamps = {5, 10, 15, 20, 25, 30}
    timestamp_counts = defaultdict(int)  # Track counts for each timestamp
    data = []
    matches_fetched = 0

    for match in match_history:
        matches_fetched += 1
        p = match.participants[account.summoner]
        duration = p.stats.time_played / 60
        for i in range(5, int(duration), 5):
            if i not in desired_timestamps:
                continue  # Skip timestamps not in the desired list
            
            if timestamp_counts[i] >= target_count:
                continue  # Skip this timestamp if we already have enough data

            if p.lane == cass.data.Lane.top_lane:
                try:
                    # Attempt to fetch cumulative timeline state
                    p_state = p.cumulative_timeline[datetime.timedelta(minutes=i, seconds=5)]
                    skills = p_state.skills
                    entry = {
                        "Match ID": match.id,
                        "Time Stamp(mins)": i,
                        "Champion": p.champion.name,
                        "Skills": skills,
                        "Kills": p_state.kills,
                        "Deaths": p_state.deaths,
                        "Assists": p_state.assists,
                        "KDA": p_state.kda,
                        "Level": p_state.level,
                        "Experience": p_state.experience,
                        "Objectives Assisted": p_state.objectives,
                        "Gold Earned": p_state.gold_earned,
                        "Current Gold": p_state.current_gold,
                        "CS": p_state.creep_score,
                        "Jungle CS": p_state.neutral_minions_killed,
                        "Vision Score": p.stats.vision_score
                    }
                    data.append(entry)
                    timestamp_counts[i] += 1  # Increment count for this timestamp

                    # Break if we have collected enough data for all desired timestamps
                    if all(timestamp_counts[t] >= target_count for t in desired_timestamps):
                        print(f"Collected enough data for all desired timestamps after {matches_fetched} matches.")
                        return data

                except ValueError as e:
                    # Log and continue processing remaining timestamps
                    print(f"ValueError at timestamp {i} for match {match.id}: {e}")
                    continue
                except Exception as e:
                    # Catch all other exceptions for debugging
                    print(f"Unexpected error at timestamp {i} for match {match.id}: {e}")
                    continue

    print(f"Finished processing {matches_fetched} matches. Some timestamps may have fewer than {target_count} entries.")
    return data

def player_data_with_account(account, target_count: int):
    summoner = account.summoner
    match_history = cass.get_match_history(
        continent=summoner.region.continent,
        puuid=summoner.puuid,
        queue=Queue.ranked_solo_fives,
    )

    # Desired timestamps to track
    desired_timestamps = {5, 10, 15, 20, 25, 30}
    timestamp_counts = defaultdict(int)  # Track counts for each timestamp
    data = []
    matches_fetched = 0

    for match in match_history:
        matches_fetched += 1
        p = match.participants[account.summoner]
        duration = p.stats.time_played / 60

        for i in range(5, int(duration), 5):
            if i not in desired_timestamps:
                continue  # Skip timestamps not in the desired list
            
            if timestamp_counts[i] >= target_count:
                continue  # Skip this timestamp if we already have enough data

            if p.lane == cass.data.Lane.top_lane:
                try:
                    # Attempt to fetch cumulative timeline state
                    p_state = p.cumulative_timeline[datetime.timedelta(minutes=i, seconds=5)]
                    skills = p_state.skills
                    entry = {
                        "Match ID": match.id,
                        "Time Stamp(mins)": i,
                        "Champion": p.champion.name,
                        "Skills": skills,
                        "Kills": p_state.kills,
                        "Deaths": p_state.deaths,
                        "Assists": p_state.assists,
                        "KDA": p_state.kda,
                        "Level": p_state.level,
                        "Experience": p_state.experience,
                        "Objectives Assisted": p_state.objectives,
                        "Gold Earned": p_state.gold_earned,
                        "Current Gold": p_state.current_gold,
                        "CS": p_state.creep_score,
                        "Jungle CS": p_state.neutral_minions_killed,
                        "Vision Score": p.stats.vision_score
                    }
                    data.append(entry)
                    timestamp_counts[i] += 1  # Increment count for this timestamp

                    # Break if we have collected enough data for all desired timestamps
                    if all(timestamp_counts[t] >= target_count for t in desired_timestamps):
                        print(f"Collected enough data for all desired timestamps after {matches_fetched} matches.")
                        return data

                except ValueError as e:
                    # Log and continue processing remaining timestamps
                    print(f"ValueError at timestamp {i} for match {match.id}: {e}")
                    continue
                except Exception as e:
                    # Catch all other exceptions for debugging
                    print(f"Unexpected error at timestamp {i} for match {match.id}: {e}")
                    continue

    print(f"Finished processing {matches_fetched} matches. Some timestamps may have fewer than {target_count} entries.")
    return data

def player_data_with_name_filter_champ(name: str, tagline: str, region: str, target_count: int, champName: str):
    account = Account(name=name, tagline=tagline, region=region)
    summoner = account.summoner
    match_history = cass.get_match_history(
        continent=summoner.region.continent,
        puuid=summoner.puuid,
        queue=Queue.ranked_solo_fives,
    )

    # Desired timestamps to track
    desired_timestamps = {5, 10, 15, 20, 25, 30}
    timestamp_counts = defaultdict(int)  # Track counts for each timestamp
    data = []
    matches_fetched = 0

    for match in match_history:
        matches_fetched += 1
        p = match.participants[account.summoner]
        duration = p.stats.time_played / 60
        for i in range(5, int(duration), 5):
            if i not in desired_timestamps:
                continue  # Skip timestamps not in the desired list
            
            if timestamp_counts[i] >= target_count:
                continue  # Skip this timestamp if we already have enough data

            if (p.lane == cass.data.Lane.top_lane) and (p.champion.name == champName):
                try:
                    # Attempt to fetch cumulative timeline state
                    p_state = p.cumulative_timeline[datetime.timedelta(minutes=i, seconds=5)]
                    skills = p_state.skills
                    entry = {
                        "Match ID": match.id,
                        "Time Stamp(mins)": i,
                        "Champion": p.champion.name,
                        "Skills": skills,
                        "Kills": p_state.kills,
                        "Deaths": p_state.deaths,
                        "Assists": p_state.assists,
                        "KDA": p_state.kda,
                        "Level": p_state.level,
                        "Experience": p_state.experience,
                        "Objectives Assisted": p_state.objectives,
                        "Gold Earned": p_state.gold_earned,
                        "Current Gold": p_state.current_gold,
                        "CS": p_state.creep_score,
                        "Jungle CS": p_state.neutral_minions_killed,
                        "Vision Score": p.stats.vision_score
                    }
                    data.append(entry)
                    timestamp_counts[i] += 1  # Increment count for this timestamp

                    # Break if we have collected enough data for all desired timestamps
                    if all(timestamp_counts[t] >= target_count for t in desired_timestamps):
                        print(f"Collected enough data for all desired timestamps after {matches_fetched} matches.")
                        return data

                except ValueError as e:
                    # Log and continue processing remaining timestamps
                    print(f"ValueError at timestamp {i} for match {match.id}: {e}")
                    continue
                except Exception as e:
                    # Catch all other exceptions for debugging
                    print(f"Unexpected error at timestamp {i} for match {match.id}: {e}")
                    continue

    print(f"Finished processing {matches_fetched} matches. Some timestamps may have fewer than {target_count} entries.")
    return data

def player_endGame_data_with_name_filter_champ(name: str, tagline: str, region: str, target_count: int, champName: str):
    account = Account(name=name, tagline=tagline, region=region)
    summoner = account.summoner
    match_history = cass.get_match_history(
        continent=summoner.region.continent,
        puuid=summoner.puuid,
        queue=Queue.ranked_solo_fives,
    )

    def categorize_duration(duration_minutes):
        if 15 <= duration_minutes < 20:
            return "15-20 mins"
        elif 20 <= duration_minutes < 25:
            return "20-25 mins"
        elif 25 <= duration_minutes < 30:
            return "25-30 mins"
        elif 30 <= duration_minutes < 35:
            return "30-35 mins"
        return "Other"

    data = []
    matches_fetched = 0
    match_index = 0
    while matches_fetched < target_count and match_index < len(match_history):
        match = match_history[match_index]
        match_index += 1  # Increment the match index
        p = match.participants[account.summoner]
        try:
            if p.champion.name == champName:
                game_duration_minutes = p.stats.time_played / 60
                duration_category = categorize_duration(game_duration_minutes)

                entry = {
                    "Match ID": match.id,
                    "Kills": p.stats.kills,
                    "Deaths": p.stats.deaths,
                    "Assists": p.stats.assists,
                    "Consumables Purchased": p.stats.consumables_purchased,
                    "Turret damages": p.stats.damage_dealt_to_turrets,
                    "Self-mitigated damage": p.stats.damage_self_mitigated,
                    "Longest time spent living": p.stats.longest_time_spent_living,
                    "Total damage to champions": p.stats.total_damage_dealt_to_champions,
                    "Total damage shielded to teammates": p.stats.total_damage_shielded_on_teammates,
                    "Total damage taken": p.stats.true_damage_taken,
                    "Total wards bought": p.stats.vision_wards_bought,
                    "Game Duration (mins)": round(game_duration_minutes, 2),
                    "Duration Category": duration_category,
                }
                matches_fetched += 1
                data.append(entry)
        except Exception as e:
            # Catch all other exceptions for debugging
            print(f"Unexpected error for match {match.id}: {e}")
            continue
    return data

def save_to_spreadsheet(data, path, filename):
    # Convert the list of dictionaries to a pandas DataFrame
    df = pd.DataFrame(data)
    filepath = os.path.join(path, filename)
    # Save the DataFrame to a CSV file
    df.to_csv(filepath, index=False)
    print(f"Data saved to {filename} successfully!")



if __name__ == "__main__":
    data = player_data_with_name("The Serendipity", "NA1", "NA", 40)
    save_to_spreadsheet(data, r"C:\Users\IKUN\Desktop\League Project\data", "player_data.csv")