# Match ID Fetcher

This tool fetches match IDs for players in a CSV file and stores them in a new CSV file with duplicates removed.

## Features

- Fetches match IDs for players using their PUUID
- Removes duplicate match IDs
- Supports filtering by queue type
- Configurable number of matches per player
- Handles rate limiting and retries

## Setup

### Prerequisites

- Python 3.8+
- Required packages: pandas, requests, dotenv

### API Key

You need a valid Riot API key to use this tool. To set up your API key:

1. Get an API key from the [Riot Developer Portal](https://developer.riotgames.com/)
2. Create a `.env` file in the project root with the following content:
   ```
   API_KEY=your-riot-api-key
   ```

## Usage

### Command Line

```bash
python -m backend.fetch_player_matches --input data/player_list/challenger_players.csv --count 50
```

### Arguments

- `--input`: Path to the input CSV file containing player information (required)
- `--output`: Path to the output CSV file to store match IDs (default: `{input_name}_match_ids.csv` in the same directory as input)
- `--count`: Number of matches to fetch per player (default: 20, max: 100)
- `--queue`: Queue type (e.g., 420 for ranked solo/duo)

### Input CSV Format

The input CSV file should have one of the following columns:
- `puuid`: Player Universally Unique ID
- `Player ID`: Player Universally Unique ID (alternative column name)

Example input CSV:
```
puuid,summoner_name,tier,rank
RDnK7jN81zbheBbytSezRf0RlsITaG1qFYC39XzpUEa5s5-l5eaRv-SqCqzAPNV7ScMUZQEPplW34Q,SτΨαi#STR,CHALLENGER,I
nuFrArR40u2gGzw5IC0o7ib3huPgLkVEXMw1Pj1iQQP8AkUIdFfZdzSXoens-AKgr0DQQPw3C2nkJQ,Mahiru Shiina#LCS,CHALLENGER,I
```

### Output CSV Format

The output CSV file will have a single column:
- `match_id`: Match ID

Example output CSV:
```
match_id
NA1_5268077440
NA1_5268077441
NA1_5268077442
```

## Queue Types

Common queue types:
- 400: Normal Draft
- 420: Ranked Solo/Duo
- 430: Normal Blind
- 440: Ranked Flex
- 700: Clash

## Example Workflow

1. Fetch player list:
   ```bash
   python -m backend.run_local_pipeline --ranks CHALLENGER
   ```

2. Fetch match IDs for those players:
   ```bash
   python -m backend.fetch_player_matches --input data/player_list/challenger_players.csv --count 50 --queue 420
   ```

3. Fetch timeline data for those matches:
   ```bash
   python -m backend.fetch_match_timelines --file data/player_list/challenger_players_match_ids.csv
   ```

## Troubleshooting

### API Key Issues

If you see a 401 error, your API key might be invalid or expired. Get a new key from the Riot Developer Portal and update your `.env` file.

### Rate Limiting

If you see a 429 error, you've hit the API rate limit. The script will automatically retry after the specified delay, but you might want to reduce the number of matches you're fetching per player or add more delays between requests.

### No Matches Found

If no matches are found for a player, it could be because:
- The player hasn't played any matches in the specified queue
- The player's PUUID is incorrect
- The API key doesn't have the necessary permissions
