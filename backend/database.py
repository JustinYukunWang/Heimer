import sqlite3
import pandas as pd

# This will create 'my_database.db' if it doesn't exist
conn = sqlite3.connect('my_database.db')

df = pd.read_csv(r"data\ryan_KSante_data.csv")

df.to_sql("ryan_KSante_data", conn, if_exists="append", index=False)