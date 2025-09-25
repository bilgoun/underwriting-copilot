from __future__ import annotations

import mimetypes
from pathlib import Path


class InvalidPDFError(RuntimeError):
    pass


def validate_pdf(path: Path, max_megabytes: int = 15) -> None:
    if not path.exists() or not path.is_file():
        raise InvalidPDFError("PDF file not found")

    mime, _ = mimetypes.guess_type(str(path))
    if mime not in {"application/pdf", None}:
        raise InvalidPDFError("Unexpected MIME type for statement")

    size_mb = path.stat().st_size / (1024 * 1024)
    if size_mb > max_megabytes:
        raise InvalidPDFError("PDF exceeds maximum size")
