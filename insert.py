import sqlite3

conn = sqlite3.connect("database.db")
cursor = conn.cursor()

with open("cidades.txt", "r") as f:
    content = f.readlines()

for line in content:
    first = line.find(":")
    second = line.find("/")
    name = line[:first]
    geocode = line[first + 1:second]
    uf = line[second + 1:second + 3]
    cursor.execute("INSERT INTO city (name, geocode, uf) VALUES (?, ?, ?)", (name, geocode, uf))
    conn.commit()

conn.close()