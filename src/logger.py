# Copyright (C) 2026 Lucas Dias

"""Logging module for the Website Archiver.

This module provides a centralized logging interface used throughout the
application. It is responsible for creating timestamped log files, recording
runtime events, and optionally displaying log messages to the user through
the console interface.

Key responsibilities:
- Create unique log files for each crawler execution
- Record informational, debug, warning, and error messages
- Provide optional console output integration
- Maintain a persistent audit trail of crawler activity
"""

import datetime
import logging
import pathlib
import typing

from rich.console import Console


class Logger:
    """Application logging service.

    This class wraps Python's built-in logging framework and provides a
    simplified interface for recording crawler events. Log entries are written
    to a timestamped file and may optionally be displayed through the console.

    The logger is intended to be shared across all application components to
    provide consistent runtime diagnostics and execution tracking.
    """

    def __init__(self, logs_path: pathlib.Path, console: Console) -> None:
        """Initialize the logging service.

        Creates a timestamped log file, configures the logging subsystem, and
        records startup information for the current application run.

        Args:
            logs_path (pathlib.Path):
                Directory where log files should be created.

            console (Console):
                Rich console instance used for optional user-facing output.

        """
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
        """Record a message in the log file.

        The message is written using the logging level specified by
        `msg_type`. Optionally, the message may also be displayed through
        the application's console interface.

        Args:
            msg (str):
                Message to record.

            msg_type (Literal["info", "debug", "warning", "error"]):
                Logging severity level.

            should_print (bool):
                Whether the message should also be printed to the console.

        """
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
