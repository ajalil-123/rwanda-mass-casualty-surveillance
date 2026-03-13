import sqlite3
import re
import spacy
from datetime import datetime
import os

# -----------------------------
# 1️⃣ Central DB path
# -----------------------------
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../data_collection"))
DB_PATH = os.path.join(PROJECT_ROOT, "articles.db")

if not os.path.exists(DB_PATH):
    raise FileNotFoundError(f"Database not found at {DB_PATH}. Run the scraper first!")

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# -----------------------------
# 2️⃣ Ensure incidents table exists
# -----------------------------
cursor.execute("""
CREATE TABLE IF NOT EXISTS incidents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    article_id INTEGER,
    date_detected TEXT,
    location TEXT,
    incident_type TEXT,
    deaths INTEGER,
    injured INTEGER,
    title TEXT,
    url TEXT,
    content TEXT,
    source TEXT
)
""")
conn.commit()

# -----------------------------
# 3️⃣ Load spaCy model
# -----------------------------
try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    import en_core_web_sm
    nlp = en_core_web_sm.load()

# -----------------------------
# 4️⃣ Helper functions
# -----------------------------
WORD_NUM_MAP = {
    "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
    "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10
}
def word_to_num(word):
    return WORD_NUM_MAP.get(word.lower(), None)

# MCI keywords and regex patterns
MCI_KEYWORDS = [
    r"accident", r"crash", r"collision", r"road mishap",
    r"killed", r"dead", r"died", r"fatal", r"casualty",
    r"injured", r"wounded", r"hurt", r"hospitalized",
    r"fire", r"explosion", r"flood", r"landslide", r"collapse",
    r"attack", r"murder", r"robbery", r"rape", r"shooting"
]

def is_mci_article(text):
    text_lower = text.lower()
    return any(re.search(word, text_lower) for word in MCI_KEYWORDS)

def extract_deaths(text):
    # Match "leaves X dead", "X dead", "X killed", "X died"
    match = re.search(r'(\d+|one|two|three|four|five|six|seven|eight|nine|ten)\s*(dead|killed|died)', text.lower())
    if match:
        number = match.group(1)
        return int(number) if number.isdigit() else word_to_num(number)
    return None

def extract_injured(text):
    # Match "X injured", "X wounded", "X hospitalized"
    match = re.search(r'(\d+|one|two|three|four|five|six|seven|eight|nine|ten)\s*(injured|wounded|hospitalized)', text.lower())
    if match:
        number = match.group(1)
        return int(number) if number.isdigit() else word_to_num(number)
    return None

def extract_location(text):
    doc = nlp(text)
    # Prefer GPE > LOC > ORG as fallback
    locations = [ent.text for ent in doc.ents if ent.label_ in ["GPE", "LOC", "ORG"]]
    if locations:
        return locations[0]
    # Fallback: first capitalized word as a naive location guess
    fallback = re.findall(r'\b[A-Z][a-z]+(?:\s[A-Z][a-z]+)?\b', text)
    return fallback[0] if fallback else None

def extract_incident_type(text):
    text_lower = text.lower()
    if any(x in text_lower for x in ["accident", "crash", "collision"]):
        return "Road Accident"
    elif "fire" in text_lower:
        return "Fire"
    elif "explosion" in text_lower:
        return "Explosion"
    elif "flood" in text_lower:
        return "Flood"
    elif "landslide" in text_lower:
        return "Landslide"
    elif "collapse" in text_lower:
        return "Structural Collapse"
    elif any(x in text_lower for x in ["rape", "robbery", "murder", "shooting", "attack"]):
        return "Violent Incident"
    else:
        return "Other"

# -----------------------------
# 5️⃣ Process articles
# -----------------------------
def process_articles():
    cursor.execute("SELECT id, title, url, content, source FROM raw_articles")
    articles = cursor.fetchall()
    mci_count = 0

    for article in articles:
        article_id, title, url, content, source = article
        text_to_check = (content or "") + " " + (title or "")

        if not text_to_check.strip() or not is_mci_article(text_to_check):
            continue

        location = extract_location(text_to_check)
        deaths = extract_deaths(text_to_check)
        injured = extract_injured(text_to_check)
        incident_type = extract_incident_type(text_to_check)
        date_detected = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        cursor.execute("""
            INSERT INTO incidents
            (article_id, date_detected, location, incident_type, deaths, injured, title, url, content, source)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (article_id, date_detected, location, incident_type, deaths, injured, title, url, content, source))
        conn.commit()
        mci_count += 1
        print(f"Saved MCI: {title} | Type: {incident_type} | Location: {location} | Deaths: {deaths} | Injured: {injured}")

    print(f"Processing completed. {mci_count} MCIs detected and saved.")

if __name__ == "__main__":
    process_articles()

