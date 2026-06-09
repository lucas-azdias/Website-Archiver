# Copyright (C) 2026 Lucas Dias

"""Command-line configuration loading and parsing.

This module provides the ``ConfigLoader`` class, responsible for defining,
parsing, and validating command-line arguments used by the website crawler.

The loader converts user-supplied CLI options into a ``ConfigDTO`` instance
that encapsulates crawler settings.

It serves as the primary entry point for transforming command-line input into
application configuration consumed by crawler components.
"""

import argparse
import pathlib
import re

from src.config.config_dto import ConfigDTO
from src.worker import Worker


class ConfigLoader:
    """Command-line configuration loader for the Website Archiver crawler.

    This class is responsible for defining CLI arguments, parsing user input,
    and producing a validated immutable `ConfigDTO` object used throughout the
    application lifecycle.
    """

    def __init__(self) -> None:
        """Initialize the CLI argument parser and immediately parse user-provided arguments into a ConfigDTO object."""
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
            type=pathlib.Path,
            dest="output_folder",
            default="./crawled",
            help="Folder where crawled websites contents are stored.",
        )

        self.__parser.add_argument(
            "--logs",
            type=pathlib.Path,
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
            default=(re.compile(r".*"),),
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
            default=re.compile(r"[<>:\"|?*]"),
            help=("Pattern matching characters that must be converted before being assigned to a filename."),
        )

        self.__parser.add_argument(
            "-s",
            "--search",
            type=re.compile,
            dest="search_url_pattern",
            default=re.compile(r"\"(\/[^\"]+)\"|href=\"([^\"]+)\""),
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
            "-O",
            "--overwrite",
            dest="should_overwrite",
            action="store_true",
            help="Overwrite existing destination files/folders if they already exist.",
        )

        self.__parser.add_argument(
            "--restricted-search",
            dest="should_restrict_search",
            action="store_true",
            help="Prevents link discovery for blacklisted URLs.",
        )

        # All user configurations saved
        self.__config = ConfigDTO(**vars(self.__parser.parse_args()))

    def get_config(self) -> ConfigDTO:
        """Return the parsed crawler configuration.

        Returns:
            ConfigDTO:
                Immutable configuration object containing all CLI-provided
                and default crawler settings.

        """
        return self.__config
