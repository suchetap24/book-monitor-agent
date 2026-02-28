import requests
import json
import os
import smtplib
from email.mime.text import MIMEText
from datetime import datetime
from datetime import datetime

GENRES = ["fantasy", "romance", "fiction", "thriller","mistery"]
DATA_FILE = "data.json"

EMAIL_ADDRESS = os.environ.get("EMAIL_ADDRESS")
EMAIL_PASSWORD = os.environ.get("EMAIL_PASSWORD")
RECIPIENT_EMAIL = os.environ.get("RECIPIENT_EMAIL")

def send_email(book, genre):
    subject = f"New {genre.capitalize()} Book Added!"
    body = f"""
Title: {book['title']}
Author: {', '.join(book.get('author_name', ['Unknown']))}
First Published: {book.get('first_publish_year', 'N/A')}
Link: https://openlibrary.org{book['key']}
Detected At: {datetime.now()}
"""

    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = EMAIL_ADDRESS
    msg["To"] = RECIPIENT_EMAIL

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        server.send_message(msg)


def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r") as f:
                content = f.read().strip()
                if not content:
                    return {}
                return json.loads(content)
        except json.JSONDecodeError:
            print("Corrupted data.json detected. Resetting.")
            return {}
    return {}

#Add AI Decision Placeholder
def ai_decide(book):
    title = book.get("title", "").lower()

    # simple intelligent rule (placeholder)
    if "guide" in title or "summary" in title:
        return "NO"

    return "YES"

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f,indent=4)


CURRENT_YEAR = datetime.now().year
MIN_EDITIONS = 3


def is_english_title(title):
    try:
        title.encode("ascii")
        return True
    except:
        return False


def check_genre(genre, memory):
    url = f"https://openlibrary.org/search.json?subject={genre}&sort=new&limit=40"

    try:
        response = requests.get(url, timeout=10)

        if response.status_code != 200:
            print(f"API error for {genre}: Status {response.status_code}")
            return

        data = response.json()
        books = data.get("docs", [])

    except Exception as e:
        print(f"Failed to fetch {genre}: {e}")
        return

    for book in books:

        # Language metadata filter
        if "language" not in book:
            continue
        if "eng" not in book["language"]:
            continue

        # ASCII title filter (removes Korean/Japanese)
        if not is_english_title(book.get("title", "")):
            continue

        # Remove web novel / chapter spam
        title_lower = book.get("title", "").lower()
        if "chapter" in title_lower or "episodes" in title_lower:
            continue


        publish_year = book.get("first_publish_year", 0)

        if publish_year < CURRENT_YEAR - 1:
            continue

        # Minimum editions filter
        if book.get("edition_count", 0) < MIN_EDITIONS:
            continue

        book_id = book["key"]

        # If already evaluated → skip completely
        if book_id in memory:
            continue

        decision = ai_decide(book)

        memory[book_id] = {
            "title": book.get("title"),
            "genre": genre,
            "ai_decision": decision,
            "notified": decision == "YES",
            "evaluated_at": datetime.now().isoformat()
        }

        if decision == "YES":
            print(f"AI approved {genre} book:", book["title"])
            send_email(book, genre)


def main():
    print("Running scheduled check...")

    memory = load_data()
    for genre in GENRES:
        check_genre(genre, memory)
    save_data(memory)    

    print("Check complete.")


if __name__ == "__main__":
    main()
