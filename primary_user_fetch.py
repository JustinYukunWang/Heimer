import datetime
import cassiopeia as cass
from cassiopeia import Account
from cassiopeia import core

cass.set_riot_api_key("RGAPI-7a02381c-0e4f-4e5a-8c64-24dbc5914f80")
REGION = "NA"
def print_newest_match(name: str, tagline: str, region: str):
    account = Account(name=name, tagline=tagline, region=region)

    match_history = account.summoner.match_history
    match = match_history[0:20]


    p = match.participants[account.summoner]
    

    p_state = p.cumulative_timeline["14:30"]
    items = p_state.items
    items = [item.name for item in items]
    skills = p_state.skills
    print("Champion:", p.champion.name)
    print("Items:", items)
    print("Skills:", skills)
    print("Kills:", p_state.kills)
    print("Deaths:", p_state.deaths)
    print("Assists:", p_state.assists)
    print("KDA:", p_state.kda)
    print("Level:", p_state.level)
    print("Position:", p_state.position)
    print("Exp:", p_state.experience)
    print("Number of objectives assisted in:", p_state.objectives)
    print("Gold earned:", p_state.gold_earned)
    print("Current gold:", p_state.current_gold)
    print("CS:", p_state.creep_score)
    print("CS in jungle:", p_state.neutral_minions_killed)
    print("vision_score: ", p.stats.vision_score)
    print("Time palyed: ", p.stats.time_played / 60, "minutes")


if __name__ == "__main__":
    print_newest_match(name="拳头马斯了123", tagline="44444", region="NA")