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


class UI:
    def __init__(self, console: Console) -> None:
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
        return self.__progress.__enter__()

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: types.TracebackType | None,
    ) -> None:
        self.__progress.__exit__(exc_type, exc_val, exc_tb)

    def add_task(self, url: str, status: str) -> None:
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
        self.__progress.update(
            self.__url_to_task[url],
            status=status,
            total=total,
            completed=completed,
            advance=advance,
        )

    def remove_task(self, url: str) -> None:
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
