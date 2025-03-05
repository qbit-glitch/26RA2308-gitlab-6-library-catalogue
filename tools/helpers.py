"""Helpers for reading the catalogue data file."""


def parse_books(path):
    """Return a list of book dictionaries read from a pipe-delimited file."""
    books = []
    with open(path, encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            book_id, title, author, year, copies = line.split("|")
            books.append({
                "id": int(book_id),
                "title": title,
                "author": author,
                "year": int(year),
                "copies": int(copies),
            })
    return books
