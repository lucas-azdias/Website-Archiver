# Copyright (C) 2026 Lucas Dias

"""Configuration loading module for the Website Archiver.

This module defines the application's runtime configuration schema and
provides a command-line based configuration loader.

Key responsibilities:
- Define the immutable `Config` dataclass used across the application
- Parse and validate CLI arguments via `argparse`
- Compile and normalize configurated values (URLs, filenames, MIME types)
- Provide a single source of truth for crawler execution parameters

This module is designed to be imported early in the application lifecycle
and used to bootstrap all other resources.
"""

import argparse
import dataclasses
import pathlib
import re

from src.worker import Worker


@dataclasses.dataclass(frozen=True)
class Config:
    """Immutable configuration object describing crawler runtime settings.

    Attributes:
        url:
            Root URL used as the starting point for the crawl process.

        output_folder:
            Filesystem path where downloaded website content is stored.

        logs_folder:
            Filesystem path where runtime logs are written.

        urls_blacklist:
            Tuple of compiled regular expressions representing URL patterns that
            must be excluded from crawling.

        urls_whitelist:
            Tuple of compiled regular expressions representing URL patterns that
            are allowed to be crawled (subject to blacklist overrides).

        max_crawler_workers:
            Maximum number of concurrent crawler worker threads/processes.

        max_worker_retries:
            Number of retry attempts allowed for failed crawling tasks.

        filename_invalid_chars_pattern:
            Regular expression used to match characters that must be sanitized
            before being used in filesystem filenames.

        search_url_pattern:
            Regular expression used to extract URLs from textual content.

        valid_textual_mime_types:
            Tuple of MIME type prefixes/values treated as textual content for
            link extraction and parsing.

    """

    url: str
    output_folder: pathlib.Path
    logs_folder: pathlib.Path
    urls_blacklist: tuple[re.Pattern[str], ...]
    urls_whitelist: tuple[re.Pattern[str], ...]
    max_crawler_workers: int
    max_worker_retries: int
    filename_invalid_chars_pattern: re.Pattern[str]
    search_url_pattern: re.Pattern[str]
    valid_textual_mime_types: tuple[str, ...]


class ConfigLoader:
    """Command-line configuration loader for the Website Archiver crawler.

    This class is responsible for defining CLI arguments, parsing user input,
    and producing a validated immutable `Config` object used throughout the
    application lifecycle.
    """

    def __init__(self) -> None:
        """Initialize the CLI argument parser and immediately parse user-provided arguments into a Config object."""
        # Argument parser for all parameters available for user via CLI
        self.__parser = argparse.ArgumentParser(
            prog="Website Archiver",
            description=(
                "A multithreaded website crawler designed to recursively download and "
                "archive an entire website for offline storage. The crawler follows "
                "internal links, preserves site structure, displays real-time download "
                "progress, and logs all crawling activity."
            ),
        )

        self.__parser.add_argument(
            "url",
            type=Worker.normalize_url,
            help="Starting URL to be crawled by the workers.",
        )

        self.__parser.add_argument(
            "-o",
            "--output",
            type=str,
            dest="output_folder",
            default="./crawled",
            help="Folder where crawled websites contents are stored.",
        )

        self.__parser.add_argument(
            "--logs",
            type=str,
            dest="logs_folder",
            default="./logs",
            help="Folder where crawler execution logs are written.",
        )

        self.__parser.add_argument(
            "--blacklist",
            type=lambda s: tuple(re.compile(p) for p in s.split(",")),
            dest="urls_blacklist",
            default=(),
            help=(
                "List of URL patterns that will be excluded from crawling. "
                "Any URL matching an entry in this list will not be downloaded or "
                "processed (use comma as separator)."
            ),
        )

        self.__parser.add_argument(
            "--whitelist",
            type=lambda s: tuple(re.compile(p) for p in s.split(",")),
            dest="urls_whitelist",
            default=(r".*",),
            help=(
                "List of URL patterns that will be included into crawling. "
                "Any URL matching an entry in this list will be downloaded or processed "
                "if not matched by a pattern in the blacklist (use comma as separator)."
            ),
        )

        self.__parser.add_argument(
            "--max-workers",
            type=int,
            dest="max_crawler_workers",
            default=32,
            help="Maximum number of concurrent crawler workers.",
        )

        self.__parser.add_argument(
            "--max-retries",
            type=int,
            dest="max_worker_retries",
            default=5,
            help="Maximum number of retry attempts for a failed crawl task of a worker.",
        )

        self.__parser.add_argument(
            "--invalid-chars",
            type=re.compile,
            dest="filename_invalid_chars_pattern",
            default=r"[<>:\"|?*]",
            help=("Pattern matching characters that must be converted before being assigned to a filename."),
        )

        self.__parser.add_argument(
            "-s",
            "--search",
            type=re.compile,
            dest="search_url_pattern",
            default=r"\"(\/[^\"]+)\"|href=\"([^\"]+)\"",
            help=("Pattern matching URLs inside any valid textual content found."),
        )

        self.__parser.add_argument(
            "--textual-mimes",
            type=lambda s: tuple(mime.strip() for mime in s.split(",")),
            dest="valid_textual_mime_types",
            default=(
                "text/",
                "application/javascript",
                "application/json",
                "application/xhtml+xml",
            ),
            help=(
                "MIME content types that should be treated as text and scanned for "
                "additional URLs (use comma as separator)."
            ),
        )

        self.__parser.add_argument(
            "--restricted-search",
            type=bool,
            action="store_true",
            help="Prevents link discovery for blacklisted URLs.",
        )

        # All user configurations saved
        self.__config = Config(**vars(self.__parser.parse_args()))

    def get_config(self) -> Config:
        """Return the parsed crawler configuration.

        Returns:
            Config:
                Immutable configuration object containing all CLI-provided
                and default crawler settings.

        """
        return self.__config
