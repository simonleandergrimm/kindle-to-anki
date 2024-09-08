# Creating Ankis based on your Kindle highlights

Fetches Kindle highlights from Readwise, selects the most relevant excerpts using Claude Sonnet 3.5, and turns them into Anki cards. [Let me know](https://github.com/simonleandergrimm/kindle-to-anki/issues) if you find bugs or have ideas for improvement!

> [!IMPORTANT]
> This tool is only meant to help users process highlights books they own to create flashcards for private use. I recommend against sharing decks created with this tool, as doing so could potentially represent a copyright infringement.


## Prerequisites

- Python 3
- Use of Readwise, and the Readwise API token
- Anthropic API key

The code accesses Kindle highlights through Readwise, a service that collects notes and highlights from apps like Feedly, Pocket, or Kindle. You can get Readwise [here](https://readwise.io/). 

## Installation

1. Clone this repository
2. Install the required packages:

```bash
pip install -r requirements.txt
```

3. Copy [.env.example](.env.example), rename it to `.env`, and add your API keys:

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
- `deck_name`: Name of the Anki deck to create (default: {book title} ({author}))

Anki decks are saved within the automatically generated `./decks` directory. Each created card has a unique identifier, based on its location in the book. Hence, if you create another set of cards for the same book deck, no duplicate cards should end up in your Anki library.

## Customisation

The prompt used by Claude is in a separate file, called [selection_prompt.txt](selection_prompt.txt). You can edit the prompt to give Claude different directions on which highlights is should prioritise. Note that editing the output format (e.g., adding variables to the JSON object) will likely break the code in [utils.py](utils.py).

### Helper scripts

- `show_metadata.py`: Show Readwise metadata for a book. Simply use like so:

```bash
./show_metadata.py <book_id>
```
