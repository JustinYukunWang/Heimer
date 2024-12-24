import cassiopeia as cass
from cassiopeia import Account, Summoner
import datetime

cass.set_riot_api_key("RGAPI-7a02381c-0e4f-4e5a-8c64-24dbc5914f80")
REGION = "NA"

def print_newest_match(matchID: str):
    
    match = match = cass.get_match(int(matchID.split('_')[1]), REGION)
    print("Frame interval:", match.timeline.frame_interval)

    players = match.participants
    for p in players:
        # You can also use a string instead of datetime.timedelta
        p_state = p.cumulative_timeline["5:00"]
        items = p_state.items
        items = [item.name for item in items]
        rune_list = p.runes
        rune = [rune.name for rune in rune_list]
        skills = p_state.skills
        print("Champion:", p.champion.name)
        print("Items:", items)
        print("Runes: ", rune)
        print("Skills:", skills)
        print("Kills:", p_state.kills)
        print("Deaths:", p_state.deaths)
        print("Assists:", p_state.assists)
        print("KDA:", p_state.kda)
        print("Level:", p_state.level)
        print("Exp:", p_state.experience)
        print("Number of objectives assisted in:", p_state.objectives)
        print("Gold earned:", p_state.gold_earned)
        print("Current gold:", p_state.current_gold)
        print("CS:", p_state.creep_score)
        print("CS in jungle:", p_state.neutral_minions_killed)


if __name__ == "__main__":
    print_newest_match(matchID="NA1_5066114593")