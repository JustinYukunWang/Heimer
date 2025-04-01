from datetime import timedelta
from prefect import flow
from prefect.server.schemas.schedules import IntervalSchedule
import general_player_fetch as g_fetch
import primary_player_fetch as p_fetch

save_path = "/Users/justinwang/Desktop/League_Analysis/data/player_list"

@flow
def get_DiamondI():
    diamondI = g_fetch.get_ranked_entries('na1', 'DIAMOND', 'I')
    diamondI_list = g_fetch.filter_player_id(diamondI)
    p_fetch.save_to_spreadsheet(diamondI_list, save_path, "diamondI_list.csv")

@flow
def get_Master():
    master_data = g_fetch.get_master_league()
    master_list = g_fetch.Higher_Rank_Id_filter(master_data)
    p_fetch.save_to_spreadsheet(master_list, save_path, "master_list.csv")

@flow
def get_Grandmaster():
    gm_data = g_fetch.get_grandmaster_league()
    gm_list = g_fetch.Higher_Rank_Id_filter(gm_data)
    p_fetch.save_to_spreadsheet(gm_list, save_path, "grandmaster_list.csv")

@flow
def get_Challenger():
    challenger_data = g_fetch.get_challenger_league()
    challenger_list = g_fetch.Higher_Rank_Id_filter(challenger_data)
    p_fetch.save_to_spreadsheet(challenger_list, save_path, "challenger_list.csv")

@flow
def weekly_fetch_all():
    get_DiamondI()
    get_Master()
    get_Grandmaster()
    get_Challenger()
