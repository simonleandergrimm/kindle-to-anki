#!/usr/bin/env python3
import utils
import sys


def main(book_id: int):
    utils.show_metadata(book_id)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: ./show_metadata.py <book_id>")
        sys.exit(1)

    try:
        book_id = int(sys.argv[1])
    except ValueError:
        print("Error: book_id must be an integer")
        sys.exit(1)

    main(book_id)
