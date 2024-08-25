# Creating Ankis based on your Kindle highlights

Fetches Kindle highlights from Readwise, selects the most relevant highlights using Claude, and turns them into Anki cards. [Let me know](https://github.com/simonleandergrimm/kindle-to-anki/issues) if you find bugs or have ideas for improvement!

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

3. Create a `.env` file and add your API keys:

```
ANTHROPIC_API_KEY=your_anthropic_api_key
READWISE_TOKEN=your_readwise_token
```
You can generate an Anthropic API key [here](https://console.anthropic.com/account/keys), and a Readwise API key [here](https://readwise.io/access_token).

## Usage

To fetch a book's highlights from Readwise, you need to know its Readwise ID. To list all books and their IDs present in your Readwise account, do:

```bash
./list_book_ids.py
```

Once you have the book ID, you can create an Anki deck.

```bash
./create_deck.py --book_id <book_id> --max-cards <max_cards> --deck_name <deck_name>
```

- `book_id`: The ID of the book in Readwise (required)
- `max-cards`: Maximum number of cards to generate (default: 20)
- `deck_name`: Name of the Anki deck to create (default: {book title} ({author)

### Helper scripts

- `show_metadata.py`: Show Readwise metadata for a book. Simply use like so:

```bash
./show_metadata.py <book_id>
```
