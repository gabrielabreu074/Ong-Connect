import sqlite3

conn = sqlite3.connect('database.db')
cursor = conn.execute('SELECT * FROM voluntarios')
for row in cursor:
    print(row)
conn.close()