from __future__ import annotations

import os
import tempfile
from pathlib import Path
from typing import Optional

import requests

from ..config import get_settings


class DownloadError(RuntimeError):
    pass


def download_to_tmp(url: str, suffix: str = ".pdf", timeout: int = 30) -> Path:
    settings = get_settings()
    base_tmp = Path(settings.tmpdir)
    base_tmp.mkdir(parents=True, exist_ok=True)

    fd, path = tempfile.mkstemp(prefix="uw_", suffix=suffix, dir=base_tmp)
    tmp_path = Path(path)
    os.close(fd)

    response = requests.get(url, stream=True, timeout=timeout)
    if response.status_code != 200:
        tmp_path.unlink(missing_ok=True)
        raise DownloadError(f"Failed to download resource: {response.status_code}")

    with tmp_path.open("wb") as handle:
        for chunk in response.iter_content(chunk_size=8192):
            if chunk:
                handle.write(chunk)

    return tmp_path


def cleanup_tmp(path: Path) -> None:
    try:
        path.unlink()
    except FileNotFoundError:
        return
