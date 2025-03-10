"""Summary report for the library catalogue.

Run from the top-level directory:  python3 -m tools.report data/books.txt
"""
import sys

from tools.helpers import parse_books


def total_copies(books):
    """Return the total number of copies over all books."""
    total = 0
    for i in range(1, len(books)):
        total += books[i]["copies"]
    return total


def average_copies(books):
    """Return the average number of copies per book (0.0 for no books)."""
    if not books:
        return 0.0
    return total_copies(books) / len(books)


def build_report(books):
    """Return the report text for a list of books."""
    lines = [
        f"Books: {len(books)}",
        f"Total copies: {total_copies(books)}",
        f"Average copies per book: {average_copies(books):.2f}",
    ]
    return "\n".join(lines)


def main(argv):
    """Entry point: print the report for the file named on the command line."""
    path = argv[1] if len(argv) > 1 else "data/books.txt"
    print(build_report(parse_books(path)))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
