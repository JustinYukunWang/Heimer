import primary_user_fetch as fetch
import cassiopeia as cass
from cassiopeia.data import Queue
from cassiopeia.core import Account

cass.set_riot_api_key("RGAPI-c88daaab-100d-4fa6-8a4b-d0ee048d0737")

masters = cass.get_master_league(queue=Queue.ranked_solo_fives, region='NA')
player1 = masters[0].summoner.account
data = fetch.fetch_player_data_with_account(player1, 1)

fetch.save_to_spreadsheet(data, r"C:\Users\IKUN\Desktop\League Project\data", "higher_rank")