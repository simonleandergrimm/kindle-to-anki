#!/usr/bin/env python3

import genanki
import utils
import argparse
from typing import Tuple, Dict, List


def main():
    utils.list_book_ids()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="List all books and their Readwise IDs."
    )

    main()
