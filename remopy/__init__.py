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
    if hasattr(entrypoint, "__doc__") and isinstance(entrypoint.__doc__, str):
        return dedent(entrypoint.__doc__)
    return None


def delete_cache(github: str | None = None) -> None:
    _remopy.delete_cache(github)
