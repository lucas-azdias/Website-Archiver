import datetime
import logging
import pathlib
import typing

from rich.console import Console


class Logger:
    def __init__(self, logs_path: pathlib.Path, console: Console) -> None:
        self.__logs_path = logs_path
        self.__console = console

        logging.basicConfig(
            filename=self.__generate_log_path(),
            level=logging.INFO,
            format="%(asctime)s %(message)s",
        )

        self.__logger = logging.getLogger(__name__)

        # Default message in log file
        self.log(f"=== Runtime started: {datetime.datetime.now().astimezone().isoformat()} ===")
        self.log(f"=== Log file: {self.__logs_path} ===")

    def log(
        self,
        msg: str,
        msg_type: typing.Literal["info", "debug", "warning", "error"] = "info",
        *,
        should_print: bool = False,
    ) -> None:
        log_msg = msg.strip()

        match msg_type:
            case "info":
                self.__logger.info(log_msg)
            case "debug":
                self.__logger.debug(log_msg)
            case "warning":
                self.__logger.warning(log_msg)
            case "error":
                self.__logger.error(log_msg)

        if should_print:
            self.__console.print(msg)

    def __generate_log_path(self) -> pathlib.Path:
        return pathlib.Path(self.__logs_path) / f"crawl_{datetime.datetime.now().astimezone():%Y-%m-%d_%H-%M-%S}.log"
