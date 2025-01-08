import cassiopeia as cass
import requests
import os
import sys
import time
from dotenv import load_dotenv

sys.path.append(os.path.abspath("../fetch_functions"))
import primary_user_fetch as p_fetch

load_dotenv()
KEY = os.getenv('API_KEY')

cass.set_riot_api_key(KEY)

cass.apply_settings({
    "caching": {
        "enabled": True,
        "cache_expiry": 3600  # Cache data for 1 hour
    }
})

cache = {}

def summonerId_to_PUUID(summonerId: str):
    if summonerId in cache:
        cached_data = cache[summonerId]
        if time.time() - cached_data['timestamp'] < 3600:  # Cache valid for 1 hour
            return cached_data['puuid']

    url = f"https://na1.api.riotgames.com/lol/summoner/v4/summoners/{summonerId}?api_key={KEY}"
    response = requests.get(url)
    if response.status_code == 200:
        puuid = response.json()['puuid']
        cache[summonerId] = {'puuid': puuid, 'timestamp': time.time()}  # Store in cache
        return puuid
    elif response.status_code == 429:
        retry_after = int(response.headers.get('Retry-After', 1))
        print(f"Rate limit exceeded. Retrying after {retry_after} seconds...")
        time.sleep(retry_after)
        return summonerId_to_PUUID(summonerId)
    else:
        print(f"Error fetching PUUID: {response.status_code}")
        return None

def filter_player_id(data: list):
    df = []
    for player in data:
        entry = {
            'Tier': player['tier'],
            'Division': player['rank'],
            'Player ID': summonerId_to_PUUID(player['summonerId'])
        }
        df.append(entry)
    return df

def Higher_Rank_Id_filter(data: dict):
    df = []
    Tier = data['tier']
    for player in data['entries']:
        entry = {
            'Tier': Tier,
            'Points': player['leaguePoints'],
            'Player ID': summonerId_to_PUUID(player['summonerId'])
        }
        df.append(entry)
    return df

def get_ranked_entries(region: str, tier: str, division: str):
    url = f'https://{region}.api.riotgdames.com/lol/league/v4/entries/RANKED_SOLO_5x5/{tier}/{division}?page=1&api_key={KEY}'
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error when fetching, error code: {response.status_code}")
        return None
    
def get_challenger_league():
    url = f"https://na1.api.riotgames.com/lol/league/v4/challengerleagues/by-queue/RANKED_SOLO_5x5?api_key={KEY}"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error when fetching, error code: {response.status_code}")
        return None

def get_grandmaster_league():
    url = f"https://na1.api.riotgames.com/lol/league/v4/grandmasterleagues/by-queue/RANKED_SOLO_5x5?api_key={KEY}"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error when fetching, error code: {response.status_code}")
        return None

def get_master_league():
    url = f"https://na1.api.riotgames.com/lol/league/v4/masterleagues/by-queue/RANKED_SOLO_5x5?api_key={KEY}"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error when fetching, error code: {response.status_code}")
        return None


if __name__ == "__main__":
    df = []
    data_response = get_ranked_entries('na1', 'DIAMOND', 'I')
    if data_response:
        data = data_response.json()
        df = filter_player_id(data)
        print(df)