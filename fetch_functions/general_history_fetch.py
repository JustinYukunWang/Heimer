import cassiopeia as cass

cass.apply_settings({
    "caching": {
        "enabled": True,
        "cache_expiry": 3600  # Cache data for 1 hour
    }
})

cass.get_league_entries