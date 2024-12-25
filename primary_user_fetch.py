import datetime
import cassiopeia as cass
from cassiopeia import Account
from cassiopeia.data import Queue
import pandas as pd
from collections import defaultdict

cass.set_riot_api_key("RGAPI-41ee105b-d0e5-41bd-9ed6-366c5583110b")

def fetch_player_data(name: str, tagline: str, region: str, target_count=40):
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

def save_to_spreadsheet(data, filename="player_data.csv"):
    # Convert the list of dictionaries to a pandas DataFrame
    df = pd.DataFrame(data)
    
    # Save the DataFrame to a CSV file
    df.to_csv(filename, index=False)
    print(f"Data saved to {filename} successfully!")

if __name__ == "__main__":
    data = fetch_player_data(name="The Serendipity", tagline="NA1", region="NA")
    save_to_spreadsheet(data)