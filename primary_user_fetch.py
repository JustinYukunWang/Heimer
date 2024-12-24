import datetime
import cassiopeia as cass
from cassiopeia import Account
from cassiopeia.data import Queue
import pandas as pd

cass.set_riot_api_key("RGAPI-41ee105b-d0e5-41bd-9ed6-366c5583110b")


def fetch_player_data(name: str, tagline: str, region: str):
    account = Account(name=name, tagline=tagline, region=region)
    summoner = account.summoner
    match_history = cass.get_match_history(
        continent=summoner.region.continent,
        puuid=summoner.puuid,
        queue=Queue.ranked_solo_fives,
    )
    matches = match_history[0:29]

    data = []
    for match in matches:
        p = match.participants[account.summoner]
        duration = p.stats.time_played / 60
        for i in range(5, int(duration), 5):
            try:
                p_state = p.cumulative_timeline[datetime.timedelta(minutes=i, seconds=0)]
                items = p_state.items
                items = [item.name for item in items]
                skills = p_state.skills
                entry = {
                    "Match ID": match.id,
                    "Time Stamp(mins)": i,
                    "Champion": p.champion.name,
                    "Items": items,
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
            except ValueError as e:
                print(f"Error processing timestamp {i} for match {match.id}: {e}")
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