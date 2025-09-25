# ─────────────────────────────────────────────────────────────
# bank_parser/constants.py
# Central place for every magic number / tune‑able list so PMs can
# update behaviour without touching core logic.
# ─────────────────────────────────────────────────────────────
from __future__ import annotations

from typing import Sequence

# Threshold above which a single transaction is considered “large”
LARGE_TX_THRESHOLD: int = 500

# Keywords used to flag suspicious / loan‑related transactions
SUSPICIOUS_KEYWORDS: Sequence[str] = [
    "zeel",
    "зээл",
    "өр",
    "бэт",
    "ur",
    "or",
    "bet",
    "bbsb",
    "ббсб",
    "буцаалт",
    "butsaalt",
    "butsalt",
    "буцалт",
]

# Words to ignore when tokenising descriptions for NLP stats
IGNORE_TOKENS: set[str] = {
    "хаанаас",
    "eb",
    "ухаалаг",
    "мэдээ",
    "үйлчилгээний",
    "хураамж",
    "апп-р",
    "хийсэн",
    "гүйлгээний",
    "320000",
    "390000",
    "040000",
    "150000",
    "520000",
}

# X‑coordinates for vertical guide lines used by pdfplumber to detect columns
VERTICAL_GUIDES: dict[str, Sequence[float]] = {
    "KHAN_KIOSK": (10, 68.4, 105, 160, 260, 380, 480, 590, 720),
    "KHAN_LINE": (43, 80, 105, 142, 204.3, 228, 370, 420, 480, 530, 570),
    "GOLOMT": (29, 130, 255, 305),  # right‑most added dynamically
    "TDB": (
        13,
        39,
        80,
        130,
        250,
        290,
        318,
        355,
        420,
        485,
    ),
}

# Helper colour tuples (RGB 0‑1) so design can be tweaked easily
GUIDE_COLOURS = {
    "KHAN_LINE": (1, 0, 0),
    "KHAN_KIOSK": (0, 0, 0),
    "GOLOMT": (0, 1, 0),
    "TDB": (0, 0, 0),
}

# ---------------------------------------------------------------------------
__all__ = [
    "LARGE_TX_THRESHOLD",
    "SUSPICIOUS_KEYWORDS",
    "IGNORE_TOKENS",
    "VERTICAL_GUIDES",
    "GUIDE_COLOURS",
]
