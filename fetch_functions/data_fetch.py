import general_player_fetch as g_fetch
import primary_player_fetch as p_fetch
from fastapi import FastAPI

app = FastAPI()

@app.get("/jgj")
async def get_DiamondI():
    diamondI = g_fetch.get_ranked_entries('na1', 'DIAMOND', 'I')
    diamondI_list = g_fetch.filter_player_id(diamondI)
    return diamondI_list