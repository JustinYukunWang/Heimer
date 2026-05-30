"""
Script to fetch match IDs for players in a CSV file and store them in a new CSV file.
This script removes duplicate match IDs.
"""
import os
import pandas as pd
import logging
import requests
import time
import argparse
from dotenv import load_dotenv

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Ensure your Riot API key is set
load_dotenv()
KEY = os.getenv('API_KEY')

# Define API endpoints
MATCH_API = 'https://americas.api.riotgames.com/lol/match/v5/matches'
MATCH_HISTORY_API = 'https://americas.api.riotgames.com/lol/match/v5/matches/by-puuid'

# Helper function to make API requests with rate limiting
def make_request(url, params=None, retries=3, retry_delay=1):
    """Make a request to the Riot API with rate limiting and retries."""
    headers = {
        "X-Riot-Token": KEY
    }
    
    for attempt in range(retries):
        response = requests.get(url, headers=headers, params=params)
        
        if response.status_code == 200:
            return response.json()
            
        elif response.status_code == 429:  # Rate limit exceeded
            retry_after = int(response.headers.get('Retry-After', retry_delay))
            logger.warning(f"Rate limit exceeded. Retrying after {retry_after} seconds...")
            time.sleep(retry_after)
            
        elif response.status_code == 404:  # Not found
            logger.error(f"Resource not found: {url}")
            return None
            
        elif response.status_code == 401:  # Unauthorized
            logger.error(f"API key invalid or expired")
            return None
            
        else:
            logger.error(f"API request failed with status code {response.status_code}: {response.text}")
            
        if attempt < retries - 1:
            time.sleep(retry_delay)
    
    return None

def get_match_ids_for_puuid(puuid, count=20, queue=None, start_time=None, end_time=None):
    """
    Get match IDs for a player by PUUID.
    
    Args:
        puuid: Player PUUID
        count: Number of matches to fetch (max 100)
        queue: Queue type (e.g., 420 for ranked solo/duo)
        start_time: Start time in epoch seconds
        end_time: End time in epoch seconds
        
    Returns:
        List of match IDs
    """
    url = f"{MATCH_HISTORY_API}/{puuid}/ids"
    
    params = {
        "count": min(count, 100)  # API limit is 100
    }
    
    if queue is not None:
        params["queue"] = queue
        
    if start_time is not None:
        params["startTime"] = start_time
        
    if end_time is not None:
        params["endTime"] = end_time
    
    logger.info(f"Fetching match IDs for PUUID: {puuid}")
    match_ids = make_request(url, params)
    
    if match_ids:
        logger.info(f"Found {len(match_ids)} matches for PUUID: {puuid}")
        return match_ids
    else:
        logger.warning(f"No matches found for PUUID: {puuid}")
        return []

def process_player_csv(input_file, output_file, count_per_player=20, queue=None):
    """
    Process a CSV file containing player information and fetch match IDs.
    
    Args:
        input_file: Path to the input CSV file
        output_file: Path to the output CSV file
        count_per_player: Number of matches to fetch per player
        queue: Queue type (e.g., 420 for ranked solo/duo)
        
    Returns:
        Number of unique match IDs found
    """
    try:
        # Read the input CSV file
        df = pd.read_csv(input_file)
        
        # Check if the CSV has the required columns
        if 'puuid' in df.columns:
            puuid_column = 'puuid'
        elif 'Player ID' in df.columns:
            puuid_column = 'Player ID'
        else:
            logger.error(f"Input CSV file does not have a 'puuid' or 'Player ID' column")
            return 0
        
        # Get unique PUUIDs
        puuids = df[puuid_column].unique()
        logger.info(f"Found {len(puuids)} unique players in {input_file}")
        
        # Fetch match IDs for each player
        all_match_ids = []
        for i, puuid in enumerate(puuids):
            if not puuid or pd.isna(puuid):
                continue
                
            logger.info(f"Processing player {i+1}/{len(puuids)}")
            match_ids = get_match_ids_for_puuid(puuid, count=count_per_player, queue=queue)
            all_match_ids.extend(match_ids)
            
            # Add a small delay to avoid rate limiting
            time.sleep(1)
        
        # Remove duplicates
        unique_match_ids = list(set(all_match_ids))
        logger.info(f"Found {len(unique_match_ids)} unique match IDs from {len(all_match_ids)} total matches")
        
        # Create output directory if it doesn't exist
        output_dir = os.path.dirname(output_file)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)
        
        # Save to CSV
        match_df = pd.DataFrame({"match_id": unique_match_ids})
        match_df.to_csv(output_file, index=False)
        logger.info(f"Saved {len(unique_match_ids)} match IDs to {output_file}")
        
        return len(unique_match_ids)
        
    except Exception as e:
        logger.error(f"Error processing player CSV: {e}")
        return 0

def main():
    parser = argparse.ArgumentParser(description="Fetch match IDs for players in a CSV file")
    
    parser.add_argument(
        "--input", 
        required=True,
        help="Path to the input CSV file containing player information"
    )
    parser.add_argument(
        "--output", 
        required=True,
        help="Path to the output CSV file to store match IDs"
    )
    parser.add_argument(
        "--count", 
        type=int,
        default=20,
        help="Number of matches to fetch per player (default: 20, max: 100)"
    )
    parser.add_argument(
        "--queue", 
        type=int,
        help="Queue type (e.g., 420 for ranked solo/duo)"
    )
    
    args = parser.parse_args()
    
    # Process the CSV file
    process_player_csv(args.input, args.output, args.count, args.queue)

if __name__ == "__main__":
    main()
