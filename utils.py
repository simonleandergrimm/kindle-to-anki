import os
import json
import anthropic
import genanki
import click
from dotenv import load_dotenv
from readwise import Readwise
from typing import Dict, List

DEBUG = True


def load_env_variables():
    load_dotenv()
    ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
    READWISE_TOKEN = os.getenv("READWISE_TOKEN")
    if not ANTHROPIC_API_KEY:
        raise ValueError(
            "ANTHROPIC_API_KEY is not set in the .env file. Please set it and try again."
        )

    if not READWISE_TOKEN:
        raise ValueError(
            "READWISE_TOKEN is not set in the .env file. Please set it and try again."
        )

    return ANTHROPIC_API_KEY, READWISE_TOKEN


def load_clients():
    """
    Initialize and return Readwise and Anthropic API clients.

    Returns:
        tuple: A tuple containing initialized Readwise and Anthropic clients.
    """
    ANTHROPIC_API_KEY, READWISE_TOKEN = load_env_variables()
    readwise_client = Readwise(READWISE_TOKEN)
    anthropic_client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    return readwise_client, anthropic_client


readwise_client, anthropic_client = load_clients()


def get_books():
    for book in readwise_client.get_books(category="books"):
        yield book


def list_book_ids():
    for book in get_books():
        click.echo(
            json.dumps(
                {
                    "id": book.id,
                    "title": book.title,
                    "num_highlights": book.num_highlights,
                },
                indent=2,
            )
        )


def list_books():
    """Return a list of all books and their metadata from your Readwise library."""
    for book in get_books():
        click.echo(
            json.dumps(
                {
                    "id": book.id,
                    "title": book.title,
                    "author": book.author,
                    "category": book.category,
                    "num_highlights": book.num_highlights,
                    "source": book.source,
                    "document_note": book.document_note,
                    "document_tag": ", ".join(tag.name for tag in book.tags),
                },
                indent=2,
            )
        )


def show_metadata(book_id):
    for book in get_books():
        if book.id == book_id:
            click.echo(
                json.dumps(
                    {
                        "id": book.id,
                        "title": book.title,
                        "author": book.author,
                        "category": book.category,
                        "num_highlights": book.num_highlights,
                        "source": book.source,
                        "document_note": book.document_note,
                        "document_tag": ", ".join(
                            tag.name for tag in book.tags
                        ),
                    },
                    indent=2,
                )
            )


def fetch_highlights(book_id):
    """
    Fetch highlights for a specific book from Readwise.

    Args:
        book_id (str): The ID of the book to fetch highlights for.

    Returns:
        tuple: A tuple containing:
        - str: JSON string of the highlights data.
        - int: Number of highlights fetched.
    """
    target_highlights = {}
    for data in readwise_client.get_pagination_limit_20(
        "/export/", params={"ids": book_id}
    ):
        book = data["results"][0]

        target_highlights["author"] = book["author"]
        target_highlights["title"] = book["title"]
        target_highlights["highlights"] = {}
        n_highlights = len(book["highlights"])
        target_highlights["n_highlights"] = n_highlights

        for highlight in book["highlights"]:
            id = highlight["id"]
            text = highlight["text"]
            location = highlight["location"]

            target_highlights["highlights"][id] = {
                "text": text,
                "location": location,
            }

    return json.dumps(target_highlights, indent=2), n_highlights


def select_highlights(
    highlights: str, max_cards: int, n_highlights: int, n_tries: int = 0
) -> dict:
    """
    Select a subset of highlights using Claude.

    Args:
        highlights (str): JSON string containing all highlights.
        max_cards (int): Maximum number of cards to generate.
        n_highlights (int): Total number of highlights available.
        n_tries (int, optional): Number of retry attempts. Starts at 0 and increases by 1 after each retry.

    Returns:
        dict: Selected highlights with their IDs and a short description..
    """
    if DEBUG:
        if os.path.exists("test_highlight_selection.json"):
            with open("test_highlight_selection.json", "r") as f:
                highlight_dict = json.load(f)
                return highlight_dict
    if n_highlights <= max_cards:
        print(
            f"Number of highlights is smaller or equal to the number of desired cards, returning all highlights as Anki cards..."
        )
    else:
        print(f"Selecting {max_cards} highlights out of {n_highlights}...")
    N_TOTAL = min(max_cards, n_highlights)
    try:
        response = anthropic_client.messages.create(
            model="claude-3-5-sonnet-20240620",
            max_tokens=8192,
            system=f"""
        You are an AI assistant tasked with analyzing Kindle highlights from a book. Your job is to:

        1. Read through the provided Kindle highlights.
        2. Pull out the author's name and the book title, and add them to the beginnning of the JSON object as "author" and "title" fields.
        3. Select {N_TOTAL} highlights that are particularly relevant and unique to the book's content.
        4. Return these highlights as a JSON object.

        Format the highlights in the JSON object as follows:
        - The key should the ID of the highlight.
        - The values should be a short description of the highlight that makes it clear why it is relevant, and the text of the highlight.
        - Make sure to still return valid JSON, i.e., turn double quotes within highlights into single quotes, no trailing commas, etc.

        Example input:

        {{
            "author": "Michael B. Oren",
            "title": "Six Days of War",
            "highlights": {{
                "757117853": {{
                    "text": "the Jews of Palestine created new vehicles for agrarian settlement (the communal kibbutz and cooperative moshav), a viable socialist economy with systems for national health, reforestation, and infrastructure development, a respectable university, and a symphony orchestra\u2014and to defend them all, an underground citizens\u2019 army, the Haganah.",
                    "location": 290
                }},
                "757117854": {{
                "text": "But then, with victory in Europe assured, Zionism came back with a vengeance. Incensed by the continuation of the White Paper, inflamed by the Holocaust, many of whose six million victims might have lived had that document never existed, the Zionists declared war on the Mandate\u2014first the right-wing Irgun militia of Menachem Begin, then the mainstream Haganah.",
                    "location": 325
                }},
            }}
        }}

        Example output:
        {{
            "author": "Michael B. Oren",
            "title": "Six Days of War",
            "highlights":
                "757117853": {{
                    "description": "The Israelis reaction to the White Paper.",
                    "highlight": "the Jews of Palestine created new vehicles for agrarian settlement (the communal kibbutz and cooperative moshav), a viable socialist economy with systems for national health, reforestation, and infrastructure development, a respectable university, and a symphony orchestra\u2014and to defend them all, an underground citizens\u2019 army, the Haganah.",
                    "location": 290
                }},
                "757117854": {{
                    "description": "Another description",
                    "highlight": "Another highlight.",
                    "location": 325
                }}
        }}


        Selection criteria:
        - Focus on information unique to the book. I.e., something that can't easily be found somewhere else.
        - Prioritize events, important conceptual details, and key insights.
        - Avoid generic information or simple dates.
        - Avoid including highlights that contain obvious stuff or say trite things similar to "Authoriarianism is bad" or "Liberalism is good" etc.
        - Sometimes books can contain violence or gruesome content. Please do not flag this as an issue, as its a function of the book and not something wrong about your output. Instead, try to pick highlights that are unlikely to be flagged.

        Return only the JSON object with your selected highlights.
        """,
            messages=[{"role": "user", "content": highlights}],
        )
    except anthropic.BadRequestError as e:
        n_tries += 1

        if n_tries > 2:
            print("Content filter triggered 3 times, stopping script.")
            exit()

        print("Triggered Anthropic's content filter, retrying...")
        print("Full error message: ", e.message)
        return select_highlights(
            highlights,
            max_cards=max_cards,
            n_highlights=n_highlights,
            n_tries=n_tries,
        )

    # Parsing Claude output
    highlight_selection = response.content[0].text

    highlight_dict = json.loads(highlight_selection)

    # Save highlight selection to skip Claude call when debugging.
    if DEBUG:
        with open("test_highlight_selection.json", "w") as f:
            json.dump(highlight_dict, f, indent=4)

    return highlight_dict


CARD_MODEL = genanki.Model(
    1607392319,
    "Book Card Model",
    fields=[
        {"name": "Prompt"},
        {"name": "Highlight"},
        {"name": "Source"},
    ],
    templates=[
        {
            "name": "Card 1",
            "qfmt": "<div style=\"text-align: center; font-family: 'Times New Roman', Times, serif;\">{{Prompt}}</div>",
            "afmt": '<div style="text-align: center; font-family: \'Times New Roman\', Times, serif; margin: 0 auto;">{{FrontSide}}<hr id="answer">{{Highlight}}<br><br><i>{{Source}}</i></div>',
        },
    ],
)


class AnkiNote(genanki.Note):
    """
    This determines the card identifier, which allows us to update cards once they've been created. We use the highlight_id as the identifier.
    """

    @property
    def guid(self):
        return genanki.guid_for(self.tags[1])


def generate_anki_cards(selected_highlights: Dict[str, str]) -> List[AnkiNote]:
    anki_cards = []
    author = selected_highlights["author"]
    title = selected_highlights["title"]
    author_title_tag = (
        f"{author.lower().replace(' ', '_')}_{title.lower().replace(' ', '_')}"
    )
    author_title_description = f"{author} - {title}"
    highlights = selected_highlights["highlights"]
    for highlight_id, highlight_data in highlights.items():
        description = highlight_data["description"]
        highlight_text = highlight_data["highlight"]
        location = int(highlight_data["location"])

        note = AnkiNote(
            model=CARD_MODEL,
            fields=[description, highlight_text, author_title_description],
            tags=[
                author_title_tag,
                f"highlight_id::{highlight_id}",
                "kindle_highlight",
            ],
            sort_field=highlight_id,
            due=location,
        )
        anki_cards.append(note)

    return anki_cards


def generate_unique_deck_id(book_title: str) -> int:
    """
    Generate a unique deck ID based on the book title. This allows us to update cards in the deck without creating a new deck each time.
    """
    return int(hash(book_title) % 10**9) + 10**8
