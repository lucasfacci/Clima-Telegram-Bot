import sqlite3

conn = sqlite3.connect("database.db")
cursor = conn.cursor()

cursor.execute("""CREATE TABLE IF NOT EXISTS city (cityid INTEGER PRIMARY KEY AUTOINCREMENT,
name TEXT NOT NULL, geocode TEXT NOT NULL, uf TEXT NOT NULL)""")

conn.close()