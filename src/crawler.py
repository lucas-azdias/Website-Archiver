# Copyright (C) 2026 Lucas Dias

"""Crawler module for the Website Archiver.

This module implements the core concurrent crawling engine responsible for
recursively discovering and processing URLs using a pool of worker threads.

Key responsibilities:
- Manage crawling lifecycle and coordination
- Maintain a shared URL queue for worker consumption
- Spawn and control worker threads
- Enforce concurrency limits
- Handle graceful shutdown on interruption signals
"""

import queue
import threading
import time
import urllib.parse

from rich.console import Console

from src.config_loader import Config
from src.logger import Logger
from src.user_interface import UserInterface
from src.worker import Worker


class Crawler:
    """High-level crawling orchestrator.

    This class coordinates worker threads, manages the URL frontier, and
    controls the crawler execution lifecycle.

    The crawler acts as the central coordinator between:
    - Configuration (Config)
    - Logging system (Logger)
    - User interface (UI)
    - Worker execution pool (Worker)
    """

    def __init__(self, config: Config, logger: Logger, console: Console) -> None:
        """Initialize the crawler and validate output environment.

        Args:
            config (Config):
                Application configuration containing crawling parameters.

            logger (Logger):
                Logging interface used for status, warnings, and errors.

            console (Console):
                Rich console instance used for displaying runtime progress.

        Raises:
            SystemExit:
                If the target output directory for the given hostname already exists.
                This prevents accidental overwriting of previously crawled data.

        """
        self.__hostname = urllib.parse.urlparse(config.url).netloc
        self.__starting_url = config.url
        self.__output_folder = config.output_folder
        self.__max_workers = config.max_crawler_workers
        self.__logger = logger
        self.__ui = UserInterface(console)
        self.__worker = Worker(config, logger, self.__ui)

        # Checks for existence of a host named folder inside output folder
        if (self.__output_folder / self.__hostname).exists():
            self.__logger.log("Output website folder already exists.", msg_type="error", should_print=True)
            raise SystemExit(1)

    def start(self) -> None:
        """Start the crawling process and manage UI lifecycle.

        This method initializes the URL queue, starts the UI context manager,
        launches the crawling thread, and keeps the main thread alive until
        completion or interruption.
        """
        url_queue: queue.Queue[str | None] = queue.Queue()

        try:
            with self.__ui:
                t = threading.Thread(target=self.crawl, args=(url_queue,))
                t.start()

                while t.is_alive():
                    time.sleep(0.5)

        except KeyboardInterrupt:
            self.__logger.log("[CTRL+C] Shutdown signal sent.", msg_type="warning", should_print=True)

    def crawl(self, url_queue: queue.Queue[str | None]) -> None:
        """Core crawling routine executed in a dedicated thread.

        This method initializes worker threads, seeds the URL queue with the
        starting URL, and coordinates the lifecycle of the crawling process.

        Args:
            url_queue (queue.Queue[str | None]):
                Shared queue used to distribute URLs to worker threads.
                A value of `None` is used as a sentinel to signal shutdown.

        """
        visited: set[str] = set()

        # Register starting URL
        url_queue.put(self.__starting_url)
        visited.add(self.__starting_url)

        # Initializes every job
        jobs: list[threading.Thread] = [
            threading.Thread(target=self.__worker.job, daemon=True) for _ in range(self.__max_workers)
        ]

        # Starts every job
        for job in jobs:
            job.start()

        try:
            url_queue.join()

        except KeyboardInterrupt:  # CTRL+C (kill signal)
            # Clears entire queue
            try:
                while True:
                    url_queue.get_nowait()
                    url_queue.task_done()
            except queue.Empty:
                pass

            self.__logger.log("[CTRL+C] Shutdown signal sent.", msg_type="warning", should_print=True)

        finally:
            # Flag every job to stop
            for _ in jobs:
                url_queue.put(None)

            # Wait until every job has stopped
            for job in jobs:
                job.join()
