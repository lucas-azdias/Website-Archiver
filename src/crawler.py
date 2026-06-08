import queue
import sys
import threading
import time
import urllib.parse

from src.config_loader import Config
from src.logger import Logger
from src.ui import UI
from src.worker import Worker


class Crawler:
    def __init__(self, config: Config, logger: Logger, ui: UI) -> None:
        self.__hostname = urllib.parse.urlparse(config.url).netloc
        self.__starting_url = config.url
        self.__output_folder = config.output_folder
        self.__max_workers = config.max_crawler_workers
        self.__logger = logger
        self.__ui = ui
        self.__worker = Worker(config, logger, ui)

        # Checks for existence of a host named folder inside output folder
        if (self.__output_folder / self.__hostname).exists():
            self.__logger.log("Output website folder already exists.", msg_type="error", should_print=True)
            sys.exit(1)

    def start(self):
        url_queue: queue.Queue[str | None] = queue.Queue()

        try:
            with self.__ui:
                t = threading.Thread(target=self.crawl, args=(url_queue,))
                t.start()

                while t.is_alive():
                    time.sleep(0.5)

        except KeyboardInterrupt:
            self.__logger.log("[CTRL+C] Shutdown signal sent.", msg_type="warning", should_print=True)

    def crawl(self, url_queue: queue.Queue[str | None]):
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
