# # # Scrapes only news-relevant URLs (/news/ and /crime/).

# # # Fetches the full article text.

# # # Cleans titles and duplicates.

# # # Stores data into a SQLite database (easy to start, can later switch to PostgreSQL)

# news_scraper.py
import requests
from bs4 import BeautifulSoup
import sqlite3
from datetime import datetime
import os
import time

# -----------------------------
# 1️⃣ Setup database in project root
# -----------------------------
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DB_PATH = os.path.join(PROJECT_ROOT, "articles.db")

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS raw_articles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT,
    url TEXT UNIQUE,
    content TEXT,
    source TEXT,
    date_scraped TEXT
)
""")
conn.commit()

# -----------------------------
# 2️⃣ News source
# -----------------------------
BASE_URL = "https://www.newtimes.co.rw/news"

# Sections and keywords likely to contain MCIs
RELEVANT_SECTIONS = ["/news/", "/crime/", "/rwanda/"]
MCI_KEYWORDS = ["kills", "injured", "dead", "fire", "explosion", "accident", "crash", "collapsed"]

def is_relevant_url(url):
    return any(section in url for section in RELEVANT_SECTIONS)

def is_mci_article(title, content=""):
    combined = (title + " " + (content or "")).lower()
    return any(word in combined for word in MCI_KEYWORDS)

# -----------------------------
# 3️⃣ Fetch full article content
# -----------------------------
def get_article_content(url):
    try:
        response = requests.get(url, timeout=10)
        soup = BeautifulSoup(response.text, "html.parser")
        # Try multiple selectors for content
        content_div = soup.find("div", class_="field-items") or \
                      soup.find("div", class_="node__content") or \
                      soup.find("article")
        if content_div:
            paragraphs = content_div.find_all("p")
            content = " ".join(p.text.strip() for p in paragraphs if p.text.strip())
            if not content:
                print(f"⚠️ Empty content in {url}")
            return content
        else:
            print(f"⚠️ No content div found in {url}")
    except Exception as e:
        print(f"Error fetching {url}: {e}")
    return ""  # fallback

# -----------------------------
# 4️⃣ Scrape main news page for links
# -----------------------------
def scrape_news():
    try:
        response = requests.get(BASE_URL, timeout=10)
        soup = BeautifulSoup(response.text, "html.parser")
        links = soup.find_all("a")
    except Exception as e:
        print(f"Error fetching main page: {e}")
        return []

    articles = []
    for link in links:
        title = link.text.strip()
        url = link.get("href")
        if not title or not url:
            continue
        if not is_relevant_url(url):
            continue
        # Make full URL if relative
        if url.startswith("/"):
            url = "https://www.newtimes.co.rw" + url
        articles.append((title, url))

    # Remove duplicates
    articles = list(dict.fromkeys(articles))
    return articles

# -----------------------------
# 5️⃣ Save to DB
# -----------------------------
def save_article(title, url, content, source="The New Times"):
    date_scraped = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        cursor.execute("""
            INSERT OR IGNORE INTO raw_articles (title, url, content, source, date_scraped)
            VALUES (?, ?, ?, ?, ?)
        """, (title, url, content, source, date_scraped))
        conn.commit()
    except Exception as e:
        print(f"Error saving {url}: {e}")

# -----------------------------
# 6️⃣ Main
# -----------------------------
def main():
    print("Scraping articles...")
    articles = scrape_news()
    print(f"Found {len(articles)} relevant articles")

    saved_count = 0
    for idx, (title, url) in enumerate(articles, 1):
        print(f"[{idx}/{len(articles)}] Processing: {title}")
        content = get_article_content(url)
        # Save article if title OR content matches MCI keywords
        if is_mci_article(title, content):
            save_article(title, url, content)
            saved_count += 1
        time.sleep(1)  # polite delay

    print(f"Scraping completed! Total MCI-like articles saved: {saved_count}")

if __name__ == "__main__":
    main()

