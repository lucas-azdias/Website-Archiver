# Copyright (C) 2026 Lucas Dias

"""Website Archiver application entry point.

This module serves as the main bootstrap for the application. It is responsible
for initializing all core runtime components and starting the crawling engine.

Responsibilities:
- Load user configuration via ConfigLoader
- Initialize Rich console interface
- Set up logging system
- Initialize UI layer
- Instantiate and start the crawler engine

Execution flow:
1. Parse CLI configuration
2. Create console and logging infrastructure
3. Initialize UI subsystem
4. Create crawler with injected dependencies
5. Start crawling process

This file should be executed directly as the program entry point.
"""

from rich.console import Console

from src.config.config_loader import ConfigLoader
from src.crawler import Crawler
from src.display.logger import Logger


def main() -> None:
    """Entry point for the application.

    Initializes core system components including configuration loading,
    console interface, logging, UI layer, and the crawler engine.
    Then starts the crawling process.
    """
    # Loads user configurations
    config = ConfigLoader().get_config()

    # Creates console interface
    console = Console()

    # Creates logger
    logger = Logger(config.logs_folder, console)

    # Creates crawler
    crawler = Crawler(config, logger, console)

    # Starts crawling
    crawler.start()


if __name__ == "__main__":
    main()
