# Copyright (C) 2026 Lucas Dias

"""User interface module for the Website Archiver.

This module provides a thin abstraction over Rich's progress display system.
It is responsible for creating, updating, and removing progress tasks that
represent active crawler downloads.

Key responsibilities:
- Create and manage progress tasks for crawled URLs
- Display real-time download progress and status information
- Track URL-to-task associations
- Format URLs for terminal-friendly display
- Manage the lifecycle of the Rich progress interface

The UI class exposes a context manager interface that manages the lifecycle
of the underlying Rich Progress instance and provides helper methods for
tracking URL-specific download progress.
"""

import types
import urllib.parse

from rich.console import Console
from rich.progress import (
    BarColumn,
    DownloadColumn,
    Progress,
    TaskID,
    TextColumn,
    TimeRemainingColumn,
    TransferSpeedColumn,
)

from src.config_loader import ConfigLoader


class UserInterface:
    """Progress display service for crawler activity.

    This class wraps Rich's Progress component and provides a simplified
    interface for creating, updating, and removing progress tasks associated
    with crawled URLs. It maintains an internal mapping between URLs and
    progress task identifiers to enable efficient task management.

    The UI is intended to be shared across crawler components to provide
    consistent real-time visibility into download status and progress.
    """

    def __init__(self, console: Console) -> None:
        """Initialize the user interface.

        Creates and configures the Rich progress display used to visualize
        crawler activity and download progress.

        Args:
            console (Console):
                Rich console instance used for rendering progress output.

        """
        self.__starting_url = ConfigLoader().get_config().url

        self.__url_to_task: dict[str, TaskID] = {}

        self.__progress = Progress(
            TextColumn("[bold]{task.fields[status]:<12}", justify="right"),
            BarColumn(bar_width=20),
            TextColumn("{task.percentage:>6.1f}%"),
            DownloadColumn(),
            TransferSpeedColumn(),
            TimeRemainingColumn(),
            TextColumn("{task.fields[url]:.80s}"),
            console=console,
        )

    def __enter__(self) -> Progress:
        """Enter the progress display context.

        Returns:
            Progress:
                Active Rich progress instance.

        """
        return self.__progress.__enter__()

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: types.TracebackType | None,
    ) -> None:
        """Exit the progress display context.

        Args:
            exc_type (type[BaseException] | None):
                Exception type if an exception occurred.

            exc_val (BaseException | None):
                Exception instance if an exception occurred.

            exc_tb (types.TracebackType | None):
                Traceback associated with the exception.

        """
        self.__progress.__exit__(exc_type, exc_val, exc_tb)

    def add_task(self, url: str, status: str) -> None:
        """Create a progress task for a URL.

        Args:
            url (str):
                URL associated with the task.

            status (str):
                Current status label displayed for the task.

        """
        task_id = self.__progress.add_task(
            f"worker_task[{url}]",
            status=status,
            url_display=self.__format_display_urlpath(url),
            total=1,
            completed=0,
        )

        # Link URL to task id
        self.__url_to_task[url] = task_id

    def update_task(
        self,
        url: str,
        *,
        status: str | None = None,
        total: float | None = None,
        completed: float | None = None,
        advance: float | None = None,
    ) -> None:
        """Update an existing progress task.

        Args:
            url (str):
                URL associated with the task.

            status (str | None):
                Updated task status.

            total (float | None):
                Total work units expected for the task.

            completed (float | None):
                Current number of completed work units.

            advance (float | None):
                Increment to apply to the completed amount.

        """
        self.__progress.update(
            self.__url_to_task[url],
            status=status,
            total=total,
            completed=completed,
            advance=advance,
        )

    def remove_task(self, url: str) -> None:
        """Remove a progress task.

        Args:
            url (str):
                URL associated with the task.

        """
        self.__progress.remove_task(self.__url_to_task[url])
        self.__url_to_task.pop(url, None)

    @staticmethod
    def __format_display_urlpath(url: str, max_len: int = 60) -> str:
        unquoted = urllib.parse.unquote(url)

        path = urllib.parse.urlparse(unquoted).path

        if len(path) <= max_len:
            return path

        keep = max_len - 3  # for "..."
        head = keep // 2
        tail = keep - head

        return f"{path[:head]}...{path[-tail:]}"
