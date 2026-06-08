from rich.console import Console

from src.config_loader import ConfigLoader
from src.crawler import Crawler
from src.logger import Logger
from src.ui import UI


def main() -> None:
    # Loads user configurations
    config = ConfigLoader().get_config()

    # Creates console interface
    console = Console()

    # Creates logger
    logger = Logger(config.logs_folder, console)

    # Creates UI
    ui = UI(console)

    # Creates crawler
    crawler = Crawler(config, logger, ui)

    # Starts crawling
    crawler.start()


if __name__ == "__main__":
    main()
