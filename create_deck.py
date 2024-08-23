#!/usr/bin/env python3

import genanki
import utils
import argparse
import os
from typing import Tuple, Dict, List


def main(book_id: int, max_cards: int, deck_name: str = None):
    if book_id is None:
        raise ValueError("book_id must be provided. ")
    output_dir = "decks"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Fetch all highlights from Readwise
    highlights, n_highlights = utils.fetch_highlights(book_id)

    # Get Claude to select highlights
    selected_highlights = utils.select_highlights(highlights, max_cards, n_highlights)

    # Create Anki cards
    anki_cards = utils.generate_anki_cards(selected_highlights)

    # Create Anki deck title
    if deck_name is None:
        title = selected_highlights["title"]
        author = selected_highlights["author"]
        deck_name = f"{title} ({author})"

    # Create Anki deck
    unique_deck_id = utils.generate_unique_deck_id(deck_name)
    book_deck = genanki.Deck(deck_id=unique_deck_id, name=f"{deck_name}")

    for card in anki_cards:
        book_deck.add_note(card)
    deck_path = os.path.join(output_dir, f"{deck_name}.apkg")
    print(f"Saving deck to {deck_path}")
    genanki.Package(book_deck).write_to_file(deck_path)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate Anki cards from Claude-selected book highlights."
    )
    parser.add_argument(
        "--book-id",
        "-id",
        type=int,
        required=True,
        help="The ID of the book to generate Anki cards for. You can list the book ids in your Readwise account by running ./list_book_ids.py",
    )

    parser.add_argument(
        "--max-cards",
        "-m",
        type=int,
        help="The maximum number of cards to generate. Defaults to 20. Note that if a book has fewer than 20 highlights, all of them will be selected.",
        default=20,
    )
    parser.add_argument(
        "--deck_name",
        type=str,
        help="The title of the Anki deck to create. Defaults to the book title and author.",
        default=None,
    )

    args = parser.parse_args()

    main(args.book_id, args.max_cards, args.deck_name)
