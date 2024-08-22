import os
import json
import anthropic
import genanki
from dotenv import load_dotenv
from readwise import Readwise
from collections import defaultdicts

# integrate this package to parse audible bookmarks: https://github.com/jaredgth/audible-bookmark-transcriber


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
    ANTHROPIC_API_KEY, READWISE_TOKEN = load_env_variables()
    readwise_client = Readwise(READWISE_TOKEN)
    anthropic_client = anthropic.Anthropic(ANTHROPIC_API_KEY)
    return readwise_client, anthropic_client


readwise_client, anthropic_client = load_clients()


def get_books():
    """Generates a sequence of books from Readwise.

    Yields:
        dict: A dictionary representing a single book with its details.
    """
    for book in readwise_client.get_books(category="books"):
        yield book


def list_book_ids():
    """Get a list of books from a user's Readwise library."""
    for book in get_books():
        # Fix.
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
    """Get a list of books from a user's Readwise library."""
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


def list_book_details(book_id):
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
                        "document_tag": ", ".join(tag.name for tag in book.tags),
                    },
                    indent=2,
                )
            )


def fetch_highlights(book_id):
    target_highlights = {}
    for data in readwise_client.get_pagination_limit_20(
        "/export/", params={"ids": book_id}
    ):
        results = data["results"]
        for book in results:
            target_highlights["author"] = book["author"]
            target_highlights["title"] = book["title"]
            target_highlights["highlights"] = {}
            target_highlights["n_highlights"] = len(book["highlights"])

            for highlight in book["highlights"]:
                id = highlight["id"]
                text = highlight["text"]
                location = highlight["location"]

                target_highlights["highlights"][id] = {
                    "text": text,
                    "location": location,
                }

    return json.dumps(target_highlights, indent=2)


def select_highlights(highlights: str, max_cards: int, n_tries: int = 0) -> dict:
    N_MAX = max_cards
    N_HIGHLIGHTS = len(highlights)
    N_TOTAL = min(N_MAX, N_HIGHLIGHTS)
    print(f"Picking {N_TOTAL} highlights out of {N_HIGHLIGHTS}.")

    try:
        response = anthropic_client.messages.create(
            model="claude-3-5-sonnet-20240620",
            max_tokens=2048,
            system=f"""
        You are an AI assistant tasked with analyzing Kindle highlights from a book. Your job is to:

        1. Read through the provided Kindle highlights.
        2. Pull out the author's name and the book title, and add them to the beginnning of the JSON object as "author" and "title" fields.
        3. Select {N_TOTAL} highlights that are particularly relevant and unique to the book's content.
        4. Return these highlights as a JSON object.

        Format the highlights in the JSON object as follows:
        - The key should be a short description of the highlight that makes it clear why it is relevant.
        - The values should be the text of the highlight.
        - Make sure return valid JSON, i.e., escape quotes, no trailing commas, etc.

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
            #INSERT ID HERE.
                {{
                    "description": "The Israelis reaction to the White Paper.",
                    "highlight": "the Jews of Palestine created new vehicles for agrarian settlement (the communal kibbutz and cooperative moshav), a viable socialist economy with systems for national health, reforestation, and infrastructure development, a respectable university, and a symphony orchestra\u2014and to defend them all, an underground citizens\u2019 army, the Haganah."
                }},
                {{
                    "description": "Another description",
                    "highlight": "Another highlight."
                }}
            ]
        }}


        Selection criteria:
        - Focus on information unique to the book. I.e., something that can't easily be found somewhere else.
        - Prioritize events, important conceptual details, and key insights.
        - Avoid generic information or simple dates.
        - Avoid inlcuding highlights that contain obvious stuff or say trite things similar to "Authoriarianism is bad" or "Liberalism is good" etc.
        - Don't include thigs that could trigger Anthropic's content filters.

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
        return select_highlights(highlights, max_cards=max_cards, n_tries=n_tries)

    # Parsing Claude output
    highlight_selection = response.content[0].text
    highlight_dict = json.loads(highlight_selection)

    return highlight_dict


class CardModel(genanki.Model):
    1607392319,
    "Book Card Model",
    fields = (
        [
            {"name": "Prompt"},
            {"name": "Highlight"},
            {"name": "Source"},
        ],
    )
    templates = [
        {
            "name": "Card 1",
            "qfmt": "<div style=\"text-align: center; font-family: 'Times New Roman', Times, serif;\">{{Prompt}}</div>",
            "afmt": '<div style="text-align: center; font-family: \'Times New Roman\', Times, serif; margin: 0 auto;">{{FrontSide}}<hr id="answer">{{Highlight}}<br><br><a href="{{Source}}">Book Section</a></div>',
        },
    ]


class AnkiNote(genanki.Note):
    @property
    def guid(self):
        return genanki.guid_for(self.fields[0], self.fields[1])


def generate_anki_cards(highlights_dict: Dict[str, str]) -> List[genanki.Note]:
    anki_cards = []
    author = highlights_dict["author"]
    title = highlights_dict["title"]
    highlights = highlights_dict["highlights"]
    for description, highlight in highlights:
        highlight_text = highlight["highlight"]

        note = AnkiNote(
            model=CardModel,
            fields=[
                description,
                highlight_text,
                f"{author} - {title}",
            ],
            tags=[author, "kindle_highlight"],
        )
        anki_cards.append(note)

    return anki_cards


def generate_unique_deck_id(book_title: str) -> int:
    """
    Generate a unique deck ID based on the book title.

    Args:
    book_title (str): Title of the book.

    Returns:
    int: Unique deck ID.
    """
    return int(hash(book_title) % 10**9) + 10**8
