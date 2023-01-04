from textwrap import dedent
from typing import Any

from .remopy import Remopy

_remopy = Remopy()


def load(
    github: str,
    filename: str,
    entry: str | None = None,
    force_download: bool = False,
    single_file: bool = False,
) -> Any:
    return _remopy(github, filename, entry, force_download, single_file)


def help(  # noqa: A001
    github: str,
    filename: str,
    entry: str | None = None,
    force_download: bool = False,
    single_file: bool = False,
) -> str | None:
    entrypoint = _remopy(github, filename, entry, force_download, single_file)
    if hasattr(entrypoint, "__doc__"):
        return dedent(entrypoint.__doc__)
    return None
