from datetime import timedelta
from prefect import flow, task, get_run_logger
import general_player_fetch as g_fetch
import primary_player_fetch as p_fetch

SAVE_PATH = "/Users/justinwang/Desktop/League_Analysis/data/player_list"

@task
def fetch_and_save_ranked_entries(region: str, tier: str, division: str, filename: str):
    logger = get_run_logger()
    logger.info(f"Fetching {tier} {division} player list...")
    data = g_fetch.get_ranked_entries(region, tier, division)

    if not data:
        logger.error(f"Failed to fetch {tier} {division} data.")
        return

    try:
        filtered = g_fetch.filter_player_id(data)
        p_fetch.save_to_spreadsheet(filtered, SAVE_PATH, filename)
        logger.info(f"Saved {tier} {division} data to {filename}.")
    except Exception as e:
        logger.error(f"Error filtering/saving {tier} {division} data: {e}")


@task
def fetch_and_save_high_rank(api_func, rank_name: str, filename: str):
    logger = get_run_logger()
    logger.info(f"Fetching {rank_name} player list...")
    data = api_func()
    if not data:
        logger.error(f"{rank_name} data fetch failed.")
        return

    try:
        filtered = g_fetch.Higher_Rank_Id_filter(data)
        p_fetch.save_to_spreadsheet(filtered, SAVE_PATH, filename)
        logger.info(f"Saved {rank_name} data to {filename}.")
    except Exception as e:
        logger.error(f"Error filtering/saving {rank_name} data: {e}")


@flow(name="Get Diamond I")
def get_DiamondI():
    fetch_and_save_ranked_entries("na1", "DIAMOND", "I", "diamondI_list.csv")


@flow(name="Get Master")
def get_Master():
    fetch_and_save_high_rank(g_fetch.get_master_league, "MASTER", "master_list.csv")


@flow(name="Get Grandmaster")
def get_Grandmaster():
    fetch_and_save_high_rank(g_fetch.get_grandmaster_league, "GRANDMASTER", "grandmaster_list.csv")


@flow(name="Get Challenger")
def get_Challenger():
    fetch_and_save_high_rank(g_fetch.get_challenger_league, "CHALLENGER", "challenger_list.csv")


@flow(name="Weekly Full Fetch")
def weekly_fetch_all():
    get_DiamondI()
    get_Master()
    get_Grandmaster()
    get_Challenger()


if __name__ == "__main__":
    weekly_fetch_all()
