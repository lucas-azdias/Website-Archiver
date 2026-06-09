# Copyright (C) 2026 Lucas Dias

"""Configuration models used by the website crawler.

This module defines immutable configuration structures.
"""

import dataclasses
import pathlib
import re


@dataclasses.dataclass(frozen=True)
class ConfigDTO:
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

        should_overwrite:
            When True, existing files in the output directory are overwritten
            when saving crawled content. When False, existing files are
            preserved and write operations may be interrupted to avoid any
            loss of data.

        should_restrict_search:
            When True, the crawler does not discover or enqueue links found
            within URLs that are not allowed by the configured access rules.
            When False, the crawler skips downloading content from disallowed
            URLs but still inspects them for additional URLs to crawl.

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
    should_overwrite: bool
    should_restrict_search: bool
