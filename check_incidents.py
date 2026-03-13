import sqlite3

# Connect to the database
conn = sqlite3.connect("articles.db")
cursor = conn.cursor()

# Query the incidents table
cursor.execute("SELECT id, title, incident_type, location, deaths, injured FROM incidents LIMIT 10")
rows = cursor.fetchall()

# Print the results
for row in rows:
    print(row)

conn.close()