import genanki
import utils
import argparse
from typing import Tuple, Dict, List


def main(book_id: int, max_cards: int, anki_deck_name: str):
    # Fetch all highlights from Readwise
    highlights = utils.fetch_highlights(book_id)

    # Get Claude to select highlights
    highlights_dict = utils.select_highlights(highlights, max_cards)

    # Create Anki cards
    anki_cards = utils.generate_anki_cards(highlights_dict)

    # Create Anki deck
    deck_id = utils.generate_unique_deck_id(anki_deck_name)
    book_deck = genanki.Deck(utils.unique_deck_id, f"{anki_deck_name}")

    genanki.Package(book_deck).write_to_file(f"{anki_deck_name}.apkg")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate Anki cards from Claude-selected book highlights."
    )
    parser.add_argument(
        "--book_id",
        "-id",
        type=int,
        help="The ID of the book to generate Anki cards for. You can list the book ids in your Readwise account by running #TOINCLUDE",
    )

    parser.add_argument(
        "--max-cards",
        "-m",
        type=int,
        help="The maximum number of cards to generate. Defaults to 20. Note that if a book has fewer than 20 highlights, all of them will be generated.",
        default=20,
    )
    parser.add_argument(
        "--deck_name",
        type=str,
        help="The title of the Anki deck to create. Defaults to the book title.",
        default=None,
    )

    args = parser.parse_args()

    main(args.book_id, args.max_cards, args.anki_deck_name)
