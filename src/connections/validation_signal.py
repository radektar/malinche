"""Append-only validation signal for the Insights window.

Every Zachowaj/Odrzuć the user makes on a connection is one event in
``{vault}/.malinche/signal.jsonl``. After a 2–4 week run, ``kept`` vs
``dismissed`` **by connection type** is one ``jq`` away — the positive
validation signal the digest otherwise lacks (today dismiss is the only,
negative-only, signal).

Design (ADR-003):

* **Pure + AppKit-free + side-effect-isolated** — the recorder lives here, not in
  the pure ``InsightDeck`` (which must stay I/O-free to remain testable) and not
  buried in the AppKit controller. The controller just calls :func:`record_signal`.
* **Best-effort for the UI, loud in the log (A1)** — a write failure never
  reaches the click handler, but it is *logged* (``logger.warning``), so a broken
  vault path surfaces in ``make logs`` instead of silently voiding weeks of data.
* **Shared ``.malinche`` dir (A3)** — the path is derived from the same place
  ``insight_pipeline`` resolves its sidecar, so the two can never drift apart.
* **Versioned + keyed records (A2)** — ``v`` lets fields be added mid-run without
  breaking old lines; ``key`` (a hash of the note set) dedups the same insight
  surfaced across multiple digests.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Iterable, Optional

from src.logger import logger

#: Bump when the record shape changes in a non-additive way.
SCHEMA_VERSION = 1

KEPT = "kept"
DISMISSED = "dismissed"


def signal_log_path() -> Optional[Path]:
    """Path to ``signal.jsonl``, or ``None`` if config is unavailable.

    Derived from the insights sidecar's directory (A3) so the validation log and
    the digest sidecar always share the one ``.malinche`` folder.
    """
    try:
        from src.ui.insight_pipeline import latest_insights_file

        sidecar = latest_insights_file()
        if sidecar is None:
            return None
        return Path(sidecar).parent / "signal.jsonl"
    except Exception as exc:  # pragma: no cover - defensive
        logger.debug("could not resolve signal log path: %s", exc)
        return None


def signal_key(notes: Optional[Iterable[str]]) -> str:
    """Stable short hash of a connection's note set.

    Order-independent (notes are sorted) so the same pair surfaced in a later
    digest yields the same ``key`` and can be deduped at analysis time. Empty /
    missing notes hash to a constant — still a valid, comparable key.
    """
    items = sorted(str(n).strip() for n in (notes or []) if str(n).strip())
    digest = hashlib.sha1("\n".join(items).encode("utf-8")).hexdigest()
    return digest[:8]


def record_signal(
    action: str,
    conn_type: str,
    label: str = "",
    *,
    key: Optional[str] = None,
    notes: Optional[Iterable[str]] = None,
    path: Optional[Path] = None,
    now: Optional[datetime] = None,
) -> bool:
    """Append one validation event to the signal log.

    Returns ``True`` if the line was written, ``False`` otherwise. Never raises —
    a failure is logged (A1) and swallowed so the click handler is unaffected.

    ``key`` may be passed explicitly; otherwise it is derived from ``notes``.
    ``path``/``now`` are injectable for tests; in production both default from
    config / the wall clock.
    """
    try:
        target = Path(path) if path is not None else signal_log_path()
        if target is None:
            logger.warning("validation signal dropped: no log path (config?)")
            return False

        if key is None:
            key = signal_key(notes)

        stamp = (now or datetime.now()).isoformat(timespec="seconds")
        record = {
            "v": SCHEMA_VERSION,
            "ts": stamp,
            "action": str(action),
            "conn_type": str(conn_type),
            "label": str(label or ""),
            "key": key,
        }

        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(record, ensure_ascii=False) + "\n")
        return True
    except Exception as exc:
        # A1: best-effort for the UI, but never silent — a broken path must show
        # up in `make logs`, or a whole validation run is lost without a trace.
        logger.warning("could not record validation signal: %s", exc)
        return False
