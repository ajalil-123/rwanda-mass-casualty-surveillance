# import sqlite3
# import os

# # -----------------------------
# # 1️⃣ Compute absolute path robustly
# # -----------------------------
# PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
# DB_PATH = os.path.join(PROJECT_ROOT, "data_collection", "articles.db")

# # Check if DB exists
# if not os.path.exists(DB_PATH):
#     raise FileNotFoundError(f"Database not found at: {DB_PATH}")

# # -----------------------------
# # 2️⃣ Connect and fetch articles
# # -----------------------------
# conn = sqlite3.connect(DB_PATH)
# cursor = conn.cursor()

# cursor.execute("SELECT id, title, url FROM raw_articles")
# articles = cursor.fetchall()

# print(f"Total articles in DB: {len(articles)}")
# for a in articles:
#     print(a)

import sqlite3
import os

DB_PATH = os.path.abspath("data_collection/articles.db")
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

cursor.execute("SELECT id, title, url, content FROM raw_articles LIMIT 5")
articles = cursor.fetchall()
for a in articles:
    print(a)


# import spacy
# nlp = spacy.load("en_core_web_sm")
# doc = nlp("Kinshasa drone strike leaves three dead")
# print([(ent.text, ent.label_) for ent in doc.ents])