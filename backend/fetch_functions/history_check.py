import os
import pandas as pd
import logging
import requests
import time
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

def extract_timeline_data(match_id, region=None):
    """
    Extract timeline data for a specific match at 1, 5, 10, 15, and 20 minute timestamps.

    Args:
        match_id: The match ID to fetch data for (e.g., "NA1_5268077440")
        region: Not used, kept for backward compatibility

    Returns:
        Dictionary containing timeline data for each player at each timestamp
    """
    try:
        logger.info(f"Fetching match {match_id}")

        # Fetch match data
        match_url = f"{MATCH_API}/{match_id}"
        match_data = make_request(match_url)
        if not match_data:
            logger.error(f"Failed to fetch match data for {match_id}")
            return None

        # Fetch timeline data
        timeline_url = f"{MATCH_API}/{match_id}/timeline"
        timeline_data = make_request(timeline_url)
        if not timeline_data:
            logger.error(f"Failed to fetch timeline data for {match_id}")
            return None

        # Define the timestamps we're interested in (in minutes)
        minute_marks = [1, 5, 10, 15, 20]

        # Prepare a dictionary to hold data
        data = {}

        # Get participant information from match data
        participants = match_data.get('info', {}).get('participants', [])

        # Create a mapping of participant IDs to their information
        participant_info = {}
        for i, participant in enumerate(participants):
            participant_id = i + 1  # Participant IDs are 1-based

            # Get summoner name - try different fields that might contain it
            summoner_name = participant.get('summonerName', '')
            if not summoner_name:
                summoner_name = participant.get('riotIdGameName', '')
            if not summoner_name and participant.get('riotIdTagline'):
                summoner_name = f"{participant.get('riotIdGameName', '')}#{participant.get('riotIdTagline', '')}"

            puuid = participant.get('puuid', '')
            champion_name = participant.get('championName', '')
            team_id = participant.get('teamId')
            team = "Blue" if team_id == 100 else "Red"
            role = participant.get('lane', '')

            # Store participant info
            participant_info[participant_id] = {
                "summoner_name": summoner_name,
                "puuid": puuid,
                "champion": champion_name,
                "team": team,
                "role": role
            }

            # Initialize data structure for this participant
            data[participant_id] = {
                "summoner_name": summoner_name,
                "puuid": puuid,
                "champion": champion_name,
                "team": team,
                "role": role,
                "timeline": {}
            }

            logger.info(f"Participant {participant_id}: {summoner_name} ({champion_name})")

        # Process timeline frames
        frames = timeline_data.get('info', {}).get('frames', [])

        # Find frames closest to our desired minute marks
        for minute in minute_marks:
            # Convert minute to milliseconds
            target_ms = minute * 60 * 1000

            # Find the closest frame
            closest_frame = None
            min_diff = float('inf')

            for frame in frames:
                timestamp_ms = frame.get('timestamp')
                diff = abs(timestamp_ms - target_ms)

                if diff < min_diff:
                    min_diff = diff
                    closest_frame = frame

            if not closest_frame:
                logger.warning(f"No frame found for {minute} minute mark")
                continue

            # Check if the frame is close enough to the desired minute
            frame_minute = closest_frame.get('timestamp') / (60 * 1000)
            if abs(frame_minute - minute) > 0.5:  # More than 30 seconds off
                logger.warning(f"Closest frame to {minute} min is at {frame_minute:.1f} min")

            # Get participant frames
            participant_frames = closest_frame.get('participantFrames', {})

            # Get events up to this frame
            events = []
            for f in frames:
                if f.get('timestamp') <= closest_frame.get('timestamp'):
                    events.extend(f.get('events', []))

            # Process each participant's data
            for p_id_str, p_frame in participant_frames.items():
                p_id = int(p_id_str)
                if p_id not in data:
                    continue

                # Get items from events
                items = []
                for event in events:
                    if (event.get('type') == 'ITEM_PURCHASED' and
                        event.get('participantId') == p_id):
                        items.append(event.get('itemId'))

                # Calculate KDA from events
                kills, deaths, assists = 0, 0, 0
                for event in events:
                    if event.get('type') == 'CHAMPION_KILL':
                        # Check if this participant got a kill
                        if event.get('killerId') == p_id:
                            kills += 1
                        # Check if this participant died
                        elif event.get('victimId') == p_id:
                            deaths += 1
                        # Check if this participant got an assist
                        elif p_id in event.get('assistingParticipantIds', []):
                            assists += 1

                # Extract stats from participant frame
                stats = {
                    "timestamp_min": minute,
                    "gold": p_frame.get('totalGold', 0),
                    "current_gold": p_frame.get('currentGold', 0),
                    "level": p_frame.get('level', 0),
                    "xp": p_frame.get('xp', 0),
                    "minions_killed": p_frame.get('minionsKilled', 0),
                    "jungle_minions_killed": p_frame.get('jungleMinionsKilled', 0),
                    "items": items,
                    "kills": kills,
                    "deaths": deaths,
                    "assists": assists
                }

                # Add to participant's timeline data
                data[p_id]["timeline"][f"{minute}min"] = stats

        return data

    except Exception as e:
        logger.error(f"Error extracting timeline data for match {match_id}: {e}")
        return None

def save_timeline_data(data, output_path, match_id):
    """
    Save timeline data to a CSV file.

    Args:
        data: Timeline data dictionary
        output_path: Directory to save the file
        match_id: Match ID for the filename
    """
    if not data:
        logger.error("No data to save")
        return False

    try:
        # Create output directory if it doesn't exist
        os.makedirs(output_path, exist_ok=True)

        # Flatten the data for CSV format
        rows = []
        for participant_id, participant_data in data.items():
            summoner_name = participant_data["summoner_name"]
            puuid = participant_data["puuid"]
            champion = participant_data["champion"]
            team = participant_data["team"]
            role = participant_data["role"]

            for timestamp, stats in participant_data["timeline"].items():
                row = {
                    "match_id": match_id,
                    "participant_id": participant_id,
                    "summoner_name": summoner_name,
                    "puuid": puuid,
                    "champion": champion,
                    "team": team,
                    "role": role,
                    "timestamp": timestamp,
                    "gold": stats["gold"],
                    "current_gold": stats["current_gold"],
                    "level": stats["level"],
                    "xp": stats["xp"],
                    "minions_killed": stats["minions_killed"],
                    "jungle_minions_killed": stats["jungle_minions_killed"],
                    "items": ",".join(map(str, stats["items"])),
                    "kills": stats["kills"],
                    "deaths": stats["deaths"],
                    "assists": stats["assists"]
                }
                rows.append(row)

        # Convert to DataFrame and save
        df = pd.DataFrame(rows)
        output_file = os.path.join(output_path, f"{match_id}_timeline.csv")
        df.to_csv(output_file, index=False)
        logger.info(f"Saved timeline data to {output_file}")
        return True

    except Exception as e:
        logger.error(f"Error saving timeline data: {e}")
        return False

def process_match_list(match_ids, region=None, output_path="data/match_timelines"):
    """
    Process a list of match IDs and extract timeline data for each.

    Args:
        match_ids: List of match IDs to process
        region: Not used, kept for backward compatibility
        output_path: Directory to save the output files

    Returns:
        Number of successfully processed matches
    """
    successful = 0

    for match_id in match_ids:
        try:
            logger.info(f"Processing match {match_id}")
            data = extract_timeline_data(match_id)

            if data:
                if save_timeline_data(data, output_path, match_id):
                    successful += 1
                    logger.info(f"Successfully processed match {match_id}")
                else:
                    logger.error(f"Failed to save data for match {match_id}")
            else:
                logger.error(f"Failed to extract data for match {match_id}")

        except Exception as e:
            logger.error(f"Error processing match {match_id}: {e}")

    return successful

# Example usage
if __name__ == "__main__":
    # Example match ID - use a valid match ID from your region
    match_id = "NA1_4532960760"

    # Extract and save timeline data for a single match
    data = extract_timeline_data(match_id)
    if data:
        save_timeline_data(data, "data/match_timelines", match_id)

        # Print a sample of the data
        print("\nSample of extracted data:")
        participant_id = list(data.keys())[0]
        print(f"Player: {data[participant_id]['summoner_name']} ({data[participant_id]['champion']})")
        for timestamp, stats in list(data[participant_id]['timeline'].items())[:2]:  # Show first 2 timestamps
            print(f"\n{timestamp}:")
            print(f"  Gold: {stats['gold']}")
            print(f"  Items: {stats['items']}")
            print(f"  KDA: {stats['kills']}/{stats['deaths']}/{stats['assists']}")

    # Example of processing multiple matches
    print("\nTo process multiple matches, use:")
    print("python -m backend.fetch_match_timelines --match-ids NA1_4532960760 NA1_4532960761")
