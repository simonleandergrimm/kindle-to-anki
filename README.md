# Creating Ankis based on your Kindle highlights
Fetches Kindle highlights, selects the most relevant highlights, and turns them into Anki cards.

This project fetches Kindle highlights from Readwise, selects the most relevant highlights using Claude, and turns them into Anki cards.

## Prerequisites

- Python 3
- Readwise API token
- Anthropic API key

## Installation

1. Clone this repository
2. Install the required packages:

```bash
pip install -r requirements.txt
```

3. Create a `.env` file in the project root and add your API keys:

```
ANTHROPIC_API_KEY=your_anthropic_api_key
READWISE_TOKEN=your_readwise_token
```

## Usage

To create an Anki deck from a book's highlights:

```bash
python create_deck.py --book_id <book_id> --max-cards <max_cards> --deck_name <deck_name>
```

- `book_id`: The ID of the book in Readwise (required)
- `max-cards`: Maximum number of cards to generate (default: 20)
- `deck_name`: Name of the Anki deck to create (default: book title)

To list book IDs in your Readwise account do

```bash
./list_book_ids.py
```

## Project Structure

- `create_deck.py`: Main script to generate Anki decks
- `list_book_ids.py`: Script to list book IDs in your Readwise account
- `utils.py`: Utility functions for fetching highlights, selecting relevant ones, and creating Anki cards

