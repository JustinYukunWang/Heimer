import os, sys
import general_player_fetch as g_fetch
import primary_player_fetch as p_fetch
from fastapi import FastAPI
from prefect import flow

save_path = "/Users/justinwang/Desktop/League_Analysis/data/player_list"
app = FastAPI()
@app.get("/")
@flow
def get_DiamondI():
    diamondI = g_fetch.get_ranked_entries('na1', 'DIAMOND', 'I')
    diamondI_list = g_fetch.filter_player_id(diamondI)
    return diamondI_list

p_fetch.save_to_spreadsheet(get_DiamondI(), save_path, "diamondI_list.csv")

