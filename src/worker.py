# Copyright (C) 2026 Lucas Dias

"""Worker module for the Website Archiver.

This module implements the low-level crawling and download logic executed by
worker threads. It is responsible for retrieving resources, saving content,
discovering new URLs, and coordinating queue-based crawl execution.

Key responsibilities:
- Fetch resources from remote servers
- Download and persist website content
- Discover and normalize URLs from textual resources
- Apply whitelist and blacklist filtering rules
- Manage per-thread HTTP sessions
- Retry failed requests and handle network errors
- Update crawler progress and runtime logs
"""

import html
import http
import queue
import re
import threading
import time
import urllib.parse

import requests
import requests.adapters

from src.config_loader import Config
from src.logger import Logger
from src.user_interface import UserInterface


class ThreadLocal(threading.local):
    """Thread-local storage container.

    This class stores per-thread resources used by worker instances. It is
    currently used to maintain a dedicated HTTP session for each thread,
    allowing connection reuse while avoiding cross-thread session sharing.
    """

    session: requests.Session | None = None


class Worker:
    """Crawling worker responsible for processing queued URLs.

    This class encapsulates all operations required to process a single crawl
    task, including downloading resources, saving content, discovering new
    links, and updating application state. Worker instances are executed by
    multiple threads concurrently and share crawl coordination structures such
    as the URL queue and visited URL registry.

    The worker is intended to be managed by the crawler engine and should not
    be used directly as a standalone component.
    """

    __thread_local = ThreadLocal()

    def __init__(self, config: Config, logger: Logger, ui: UserInterface) -> None:
        """Initialize the worker.

        Loads crawler configuration, initializes shared services, and obtains a
        thread-local HTTP session for future network operations.

        Args:
            config (Config):
                Application configuration containing crawler settings.

            logger (Logger):
                Logging service used to record runtime events.

            ui (UI):
                User interface used to display task progress.

        """
        self.__output_folder = config.output_folder
        self.__max_retries = config.max_worker_retries
        self.__urls_blacklist = config.urls_blacklist
        self.__urls_whitelist = config.urls_whitelist
        self.__filename_invalid_chars_pattern = config.filename_invalid_chars_pattern
        self.__search_url_pattern = config.search_url_pattern
        self.__valid_textual_mime_types = config.valid_textual_mime_types
        self.__logger = logger
        self.__ui = ui
        self.__session = self.__get_session()

    def job(self, url_queue: queue.Queue[str | None], visited: set[str], lock: threading.Lock) -> None:
        """Process crawl tasks from the shared URL queue.

        Continuously retrieves URLs from the queue and processes them until a
        shutdown sentinel is received. Failed requests are retried according to
        the configured retry policy.

        Args:
            url_queue (queue.Queue[str | None]):
                Shared queue containing URLs to process.

            visited (set[str]):
                Registry of URLs already discovered during the crawl.

            lock (threading.Lock):
                Synchronization primitive used when modifying shared state.

        """
        while True:
            # Tries to get any new task
            try:
                url = url_queue.get(timeout=1)
            except queue.Empty:
                continue

            # Ends activities if receiving a `None`
            if url is None:
                url_queue.task_done()
                break

            # Creates task
            self.__ui.add_task(url, "Connecting")

            # Task retry loop
            for retry_count in range(self.__max_retries + 1):
                self.__ui.update_task(url, completed=0)

                try:
                    self.__process_task(url, url_queue, visited, lock)

                except requests.RequestException as e:
                    if retry_count < self.__max_retries:
                        # If another retry is available
                        self.__logger.log(
                            f"[RETRY] {retry_count + 1}/{self.__max_retries} {url}: {e}",
                            msg_type="warning",
                        )
                        self.__ui.update_task(url, status=f"Retrying {retry_count + 1}/{self.__max_retries}")

                        # Waits to retry again
                        time.sleep(2)

                    else:
                        # No more retries are available
                        self.__logger.log(f"[ERROR] {url}: {e}", msg_type="error")
                        self.__ui.update_task(url, status="Error found")

                else:
                    # If ended successfully, breaks from retry loop
                    break

            # Marks task as done
            url_queue.task_done()

    def __process_task(
        self,
        url: str,
        url_queue: queue.Queue[str | None],
        visited: set[str],
        lock: threading.Lock,
    ) -> None:
        # Fetches the URL
        response = self.__fetch_response(url)

        # Checks if it got any response
        if not response:
            return

        # Downloads content in chunks
        content = self.__download_content(url, response)

        # Saves file if URL is allowed
        if self.__is_url_allowed(url):
            self.__save_content(url, content)

        # Search for new URLs if content is textual
        if self.__is_valid_textual_mime_type(response):
            matches = self.__search_urls(url, content)

            # With lock, adds matches to queue if not visited
            with lock:
                for match in matches:
                    if match not in visited:
                        visited.add(match)
                        url_queue.put(match)

            self.__logger.log(f"[COUNT] {url_queue.unfinished_tasks} (+{len(matches)}) URLs to check")

        # Task is done
        self.__logger.log(f"[DONE] {url}")
        self.__ui.update_task(url, status="Done")
        self.__ui.remove_task(url)

    def __fetch_response(self, url: str) -> requests.Response | None:
        # Getting URL
        self.__logger.log(f"[GET] Getting... {url}")
        response = self.__session.get(url, timeout=(5, 10), allow_redirects=True, stream=True)
        self.__logger.log(f"[GET] Got {response.status_code} {url}")

        # Checking URL response
        if response.status_code >= http.HTTPStatus.BAD_REQUEST:
            # Unreachable URL
            self.__logger.log(f"[UNREACHABLE] Unreachable URL {url}", msg_type="warning")
            self.__ui.update_task(url, status="Not found")

            # Waits for user to visualize status
            time.sleep(2)

            # Removes task from UI
            self.__ui.remove_task(url)

            return None

        return response

    def __download_content(self, url: str, response: requests.Response) -> bytearray:
        content = bytearray()

        self.__logger.log(f"[DOWNLOAD] Starting... {url}")
        self.__ui.update_task(url, status="Downloading", total=int(response.headers.get("Content-Length", 0)) or 1)

        # Downloads content in chunks of 64 KB
        for chunk in response.iter_content(65536):
            content.extend(chunk)
            self.__ui.update_task(url, advance=len(chunk))

        self.__logger.log(f"[DOWNLOAD] Ended {url}")

        return content

    def __save_content(self, url: str, content: bytearray) -> None:
        self.__logger.log(f"[SAVE] Starting... {url}")

        parsed = urllib.parse.urlparse(url)
        path = parsed.path

        # Treats directory-like paths properly
        if path.endswith("/") or not path:
            path += "index.html"

        # Removes starting path slash
        path = path.lstrip("/")

        # Builds file path inside current website folder in output path
        file_path = self.__output_folder / parsed.netloc / self.__filename_safe_unquote(path)

        # Guarantees that parent folder exists
        file_path.parent.mkdir(parents=True, exist_ok=True)

        # Writes file in new path
        file_path.write_bytes(content)

        self.__logger.log(f"[SAVE] Ended {url}")

    def __search_urls(self, url: str, content: bytearray) -> set[str]:
        self.__logger.log(f"[READ] Reading... {url}")

        # Decodes content
        text = content.decode(errors="ignore")

        # Matches URL searching pattern with content
        matches: list[str] = [
            (match[0] if isinstance(match, (tuple, list)) else match)
            for match in self.__search_url_pattern.findall(text)
        ]

        # Normalizes URL and removes repeated
        unique_matches: set[str] = {
            self.normalize_url(urllib.parse.urljoin(url, html.unescape(match))) for match in matches
        }

        self.__logger.log(f"[READ] Ended {url}")

        return unique_matches

    def __is_url_allowed(self, url: str) -> bool:
        is_blacklisted = any(pattern.search(url) for pattern in self.__urls_blacklist)
        is_whitelisted = any(pattern.search(url) for pattern in self.__urls_whitelist)

        return not is_blacklisted and is_whitelisted

    def __filename_safe_unquote(self, url: str) -> str:
        return re.sub(
            self.__filename_invalid_chars_pattern,
            lambda m: f"%{ord(m.group(0)):02X}",
            urllib.parse.unquote(url),
        )

    def __is_valid_textual_mime_type(self, response: requests.Response) -> bool:
        content_type = response.headers.get("Content-Type", "").lower()
        return any(content_type.startswith(ct) for ct in self.__valid_textual_mime_types)

    @classmethod
    def __get_session(cls) -> requests.Session:
        # If local doesn't have a session already instantiated, creates one
        if cls.__thread_local.session is None:
            s = requests.Session()

            # Creates a new HTTP adapter
            adapter = requests.adapters.HTTPAdapter(
                pool_connections=100,
                pool_maxsize=100,
                max_retries=5,
            )

            # Overrides default adapter
            s.mount("http://", adapter)
            s.mount("https://", adapter)

            # Updates headers
            s.headers.update({"User-Agent": "Googlebot/2.1"})

            # Saves new session
            cls.__thread_local.session = s

        return cls.__thread_local.session

    @staticmethod
    def normalize_url(url: str) -> str:
        """Normalize a URL into a canonical form.

        Normalization includes path decoding, directory-path normalization,
        path re-encoding, and removal of query parameters and fragments.

        Args:
            url (str):
                URL to normalize.

        Returns:
            str:
                Normalized URL.

        """
        parsed = urllib.parse.urlparse(url)

        # Decode path (%20 -> space)
        path = urllib.parse.unquote(parsed.path)

        # Ensure directory consistency
        if not path.endswith("/") and "." not in path.split("/")[-1]:
            path += "/"

        # Re-encode safely
        path = urllib.parse.quote(path, safe="/")

        # Replace old path and removes queries and fragments
        normalized = parsed._replace(path=path, query="", fragment="")

        return str(urllib.parse.urlunparse(normalized))
