import cassiopeia as cass
import os

from dotenv import load_dotenv
load_dotenv()
KEY = os.getenv('API_KEY')

cass.set_riot_api_key(KEY)

cass.apply_settings({
    "caching": {
        "enabled": True,
        "cache_expiry": 3600  # Cache data for 1 hour
    }
})

cass.get_league_entries