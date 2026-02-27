import requests
import json
import os
import smtplib
from email.mime.text import MIMEText
from datetime import datetime
from datetime import datetime

GENRES = ["fantasy", "romance", "fiction", "thriller"]
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
        with open(DATA_FILE, "r") as f:
            return set(json.load(f))
    return set()


def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(list(data), f)


# def check_genre(genre, known_ids):
#     url = f"https://openlibrary.org/search.json?subject={genre}&sort=new&limit=20"
#     response = requests.get(url)
#     books = response.json()["docs"]

#     new_found = False

#     for book in books:
#         # Skip if language field missing
#         if "language" not in book:
#             continue

#         # Keep only English books
#         if "eng" not in book["language"]:
#             continue

#         if book["key"] not in known_ids:
#             print(f"New {genre} book found:", book["title"])
#             send_email(book, genre)
#             known_ids.add(book["key"])



CURRENT_YEAR = datetime.now().year
MIN_EDITIONS = 3


def is_english_title(title):
    try:
        title.encode("ascii")
        return True
    except:
        return False


def check_genre(genre, known_ids):
    url = f"https://openlibrary.org/search.json?subject={genre}&sort=new&limit=40"
    response = requests.get(url)
    books = response.json()["docs"]

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

        # Publish year filter
        if book.get("first_publish_year") != CURRENT_YEAR:
            continue

        # Minimum editions filter
        if book.get("edition_count", 0) < MIN_EDITIONS:
            continue

        if book["key"] not in known_ids:
            print(f"New {genre} book found:", book["title"])
            send_email(book, genre)
            known_ids.add(book["key"])


def main():
    print("Running scheduled check...")

    known_ids = load_data()

    for genre in GENRES:
        check_genre(genre, known_ids)

    save_data(known_ids)

    print("Check complete.")


if __name__ == "__main__":
    main()