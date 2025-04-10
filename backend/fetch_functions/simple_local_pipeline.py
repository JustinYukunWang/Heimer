"""
Simple, locally ready data pipeline for League of Legends data.
This version doesn't require a Prefect server to be running.
"""
import os
import logging
from pathlib import Path
from dotenv import load_dotenv
from backend.fetch_functions import general_player_fetch as g_fetch
from backend.fetch_functions import primary_player_fetch as p_fetch

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Use a relative path that works locally
BASE_DIR = Path(__file__).parent.parent.parent
SAVE_PATH = os.path.join(BASE_DIR, "data", "player_list")

# Make sure the directory exists
os.makedirs(SAVE_PATH, exist_ok=True)


def fetch_ranked_players(region: str, tier: str, division: str):
    """
    Fetch players from a specific rank and division.

    Args:
        region: Region code (e.g., 'na1')
        tier: Rank tier (e.g., 'DIAMOND')
        division: Division within tier (e.g., 'I')

    Returns:
        List of player data or None if fetch failed
    """
    logger.info(f"Fetching {tier} {division} player list from {region}...")

    try:
        data = g_fetch.get_ranked_entries(region, tier, division)
        if not data:
            logger.error(f"No data returned for {tier} {division}")
            return None

        logger.info(f"Successfully fetched {len(data)} players from {tier} {division}")
        return data
    except Exception as e:
        logger.error(f"Error fetching {tier} {division} data: {e}")
        return None


def fetch_high_rank_players(rank_type: str):
    """
    Fetch players from high ranks (Master, Grandmaster, Challenger).

    Args:
        rank_type: The rank to fetch ('MASTER', 'GRANDMASTER', or 'CHALLENGER')

    Returns:
        List of player data or None if fetch failed
    """
    logger.info(f"Fetching {rank_type} player list...")

    try:
        if rank_type == "MASTER":
            data = g_fetch.get_master_league()
        elif rank_type == "GRANDMASTER":
            data = g_fetch.get_grandmaster_league()
        elif rank_type == "CHALLENGER":
            data = g_fetch.get_challenger_league()
        else:
            logger.error(f"Invalid rank type: {rank_type}")
            return None

        if not data:
            logger.error(f"No data returned for {rank_type}")
            return None

        logger.info(f"Successfully fetched {rank_type} players")
        return data
    except Exception as e:
        logger.error(f"Error fetching {rank_type} data: {e}")
        return None


def process_player_data(data, rank_type: str):
    """
    Process the raw player data into a structured format.

    Args:
        data: Raw player data
        rank_type: The rank type for processing logic

    Returns:
        Processed data ready for saving
    """
    logger.info(f"Processing {rank_type} player data...")

    try:
        if rank_type in ["MASTER", "GRANDMASTER", "CHALLENGER"]:
            processed_data = g_fetch.Higher_Rank_Id_filter(data)
        else:
            processed_data = g_fetch.filter_player_id(data)

        logger.info(f"Successfully processed {len(processed_data)} player records")
        return processed_data
    except Exception as e:
        logger.error(f"Error processing {rank_type} data: {e}")
        return None


def save_player_data(data, filename: str):
    """
    Save processed player data to a CSV file.

    Args:
        data: Processed player data
        filename: Name of the file to save
    """
    logger.info(f"Saving data to {filename}...")

    try:
        p_fetch.save_to_spreadsheet(data, SAVE_PATH, filename)
        logger.info(f"Successfully saved data to {os.path.join(SAVE_PATH, filename)}")
        return True
    except Exception as e:
        logger.error(f"Error saving data to {filename}: {e}")
        return False


def fetch_diamond_players():
    """Fetch Diamond I players."""
    data = fetch_ranked_players("na1", "DIAMOND", "I")
    if data:
        processed_data = process_player_data(data, "DIAMOND")
        if processed_data:
            return save_player_data(processed_data, "diamond_players.csv")
    return False


def fetch_master_players():
    """Fetch Master players."""
    data = fetch_high_rank_players("MASTER")
    if data:
        processed_data = process_player_data(data, "MASTER")
        if processed_data:
            return save_player_data(processed_data, "master_players.csv")
    return False


def fetch_grandmaster_players():
    """Fetch Grandmaster players."""
    data = fetch_high_rank_players("GRANDMASTER")
    if data:
        processed_data = process_player_data(data, "GRANDMASTER")
        if processed_data:
            return save_player_data(processed_data, "grandmaster_players.csv")
    return False


def fetch_challenger_players():
    """Fetch Challenger players."""
    data = fetch_high_rank_players("CHALLENGER")
    if data:
        processed_data = process_player_data(data, "CHALLENGER")
        if processed_data:
            return save_player_data(processed_data, "challenger_players.csv")
    return False


def run_pipeline(ranks_to_fetch=None):
    """
    Main function that orchestrates the fetching of player data from different ranks.

    Args:
        ranks_to_fetch: List of ranks to fetch. If None, fetches all ranks.

    Returns:
        Dictionary with results for each rank
    """
    logger.info("Starting League of Legends data pipeline")

    if ranks_to_fetch is None:
        ranks_to_fetch = ["DIAMOND", "MASTER", "GRANDMASTER", "CHALLENGER"]

    results = {}

    if "DIAMOND" in ranks_to_fetch:
        results["DIAMOND"] = "Success" if fetch_diamond_players() else "Failed"

    if "MASTER" in ranks_to_fetch:
        results["MASTER"] = "Success" if fetch_master_players() else "Failed"

    if "GRANDMASTER" in ranks_to_fetch:
        results["GRANDMASTER"] = "Success" if fetch_grandmaster_players() else "Failed"

    if "CHALLENGER" in ranks_to_fetch:
        results["CHALLENGER"] = "Success" if fetch_challenger_players() else "Failed"

    logger.info("League of Legends data pipeline completed")
    return results


if __name__ == "__main__":
    # Run the pipeline locally
    results = run_pipeline()
    print("\nPipeline execution results:")
    for rank, result in results.items():
        print(f"- {rank}: {result}")
