import argparse
import dataclasses
import pathlib
import re

from src.worker import Worker


@dataclasses.dataclass(frozen=True)
class Config:
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
    def __init__(self) -> None:
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
        return self.__config
