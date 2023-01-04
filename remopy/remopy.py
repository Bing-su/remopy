from __future__ import annotations

import os
import shutil
import sys
from dataclasses import dataclass
from importlib import import_module, util
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any

import requests


@dataclass
class RepoInfo:
    owner: str
    name: str
    ref: str | None = None


def default_headers(token: str | None = None) -> dict[str, str]:
    headers = {"Accept": "application/vnd.github+json"}
    if not token:
        token = os.environ.get("GITHUB_TOKEN", None)
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def remove_if_exists(path: str | os.PathLike) -> None:
    if os.path.exists(path):
        if os.path.isfile(path):
            os.remove(path)
        else:
            shutil.rmtree(path)


def parse_repo_info(github: str) -> RepoInfo:
    if ":" in github:
        repo_info, ref = github.split(":")
    else:
        repo_info, ref = github, None
    owner, name = repo_info.split("/")
    return RepoInfo(owner, name, ref)


def get_latest_commit_sha(owner: str, name: str) -> str:
    url = f"https://api.github.com/repos/{owner}/{name}/commits"
    headers = default_headers()
    params = {"per_page": 1}
    response = requests.get(url, headers=headers, params=params, allow_redirects=True)
    response.raise_for_status()
    return response.json()[0]["sha"]


def normalize_repo_info(repo_info: RepoInfo) -> str:
    "https://github.com/pytorch/pytorch/blob/f7939b21e1f09521857515f913cd03d13ea2287b/torch/hub.py#L172"
    if not repo_info.ref:
        return "_".join([repo_info.owner, repo_info.name])
    ref = repo_info.ref.replace("/", "_")
    return "_".join([repo_info.owner, repo_info.name, ref])


def download_repository_zipfile(repo_info: RepoInfo) -> bytes:
    url = f"https://api.github.com/repos/{repo_info.owner}/{repo_info.name}/zipball"
    if repo_info.ref:
        url += f"/{repo_info.ref}"
    headers = default_headers()
    resp = requests.get(url, headers=headers, allow_redirects=True)
    resp.raise_for_status()
    return resp.content


def download_repository_single_file(repo_info: RepoInfo, filename: str) -> bytes:
    ref = repo_info.ref
    if not ref:
        ref = "master"
    url = f"https://raw.githubusercontent.com/{repo_info.owner}/{repo_info.name}/{ref}/{filename}"
    resp = requests.get(url, allow_redirects=True)
    resp.raise_for_status()
    return resp.content


class Remopy:
    def __init__(self, cache_dir: str | os.PathLike | None = None) -> None:
        if cache_dir:
            self._cache_dir = Path(cache_dir).absolute()
        elif "REMOPY_CACHE_DIR" in os.environ:
            self._cache_dir = Path(os.environ["REMOPY_CACHE_DIR"]).absolute()
        else:
            self._cache_dir = Path.home().joinpath(".cache", "remopy")

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(cache_dir={self.cache_dir})"

    @property
    def cache_dir(self) -> Path:
        return self._cache_dir

    @cache_dir.setter
    def cache_dir(self, path: str | os.PathLike) -> None:
        self._cache_dir = Path(path).absolute()

    def repoinfo_to_pathname(
        self, repo_info: RepoInfo, filename: str | None = None
    ) -> str:
        pathname = normalize_repo_info(repo_info)
        if filename:
            pathname = "_".join([pathname, filename])
        return pathname

    def repoinfo_to_cache_path(
        self, repo_info: RepoInfo, filename: str | None = None
    ) -> Path:
        cache_name = self.repoinfo_to_pathname(repo_info, filename)
        cache_path = self.cache_dir.joinpath(cache_name)
        return cache_path

    def load(
        self,
        github: str,
        filename: str,
        entry: str | None = None,
        force_download: bool = False,
        single_file: bool = False,
    ) -> Any:
        repo_info = parse_repo_info(github)
        if not single_file:
            cache_path = self._download_repository(
                repo_info, force_download=force_download
            )
            entrypoint = self._import_from_dir(cache_path, filename, entry)
        else:
            cache_path = self._download_single_file(
                repo_info, filename, force_download=force_download
            )
            entrypoint = self._import_from_file(cache_path, entry)
        return entrypoint

    __call__ = load

    def _download_repository(
        self, repo_info: RepoInfo, force_download: bool = False
    ) -> Path:
        cache_path = self.repoinfo_to_cache_path(repo_info)
        if force_download or not cache_path.exists():
            remove_if_exists(cache_path)
            zip_bytes = download_repository_zipfile(repo_info)

            with TemporaryDirectory() as tmp:
                zip_file_path = Path(tmp).joinpath("repo.zip")
                zip_file_path.write_bytes(zip_bytes)
                shutil.unpack_archive(zip_file_path, tmp)
                folder = next(p for p in Path(tmp).iterdir() if p.is_dir())
                shutil.move(folder.as_posix(), cache_path.as_posix())
        return cache_path

    def _download_single_file(
        self, repo_info: RepoInfo, filename: str, force_download: bool = False
    ) -> Path:
        cache_path = self.repoinfo_to_cache_path(repo_info, filename)
        if force_download or not cache_path.exists():
            remove_if_exists(cache_path)
            file_bytes = download_repository_single_file(repo_info, filename)
            cache_path.parent.mkdir(parents=True, exist_ok=True)
            cache_path.write_bytes(file_bytes)
        return cache_path

    def _import_from_dir(
        self, path: Path, filename: str, entry: str | None = None
    ) -> Any:
        str_path = path.as_posix()
        sys.path.insert(0, str_path)
        import_name = Path(filename).stem
        module = import_module(import_name)
        sys.path.remove(str_path)

        if not entry:
            return module
        return getattr(module, entry)

    def _import_from_file(self, path: Path, entry: str | None = None) -> Any:
        str_path = path.as_posix()
        spec = util.spec_from_file_location(path.stem, str_path)
        module = util.module_from_spec(spec)
        spec.loader.exec_module(module)

        if not entry:
            return module
        return getattr(module, entry)

    def delete_cache(self, github: str | None = None) -> None:
        if github:
            repo_info = parse_repo_info(github)
            cache_path = self.repoinfo_to_cache_path(repo_info)
            remove_if_exists(cache_path)
            remove_if_exists(self.cache_dir.joinpath("__pycache__"))
        else:
            remove_if_exists(self.cache_dir)
