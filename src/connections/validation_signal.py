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
from typing import Iterable, List, Optional

from src.connections.signature import connection_signature
from src.logger import logger

#: Bump when the record shape changes in a non-additive way. v1 = legacy
#: kept/dismissed (``record_signal``); v2 = ``action_taken`` (``record_action``).
SCHEMA_VERSION = 1
ACTION_SCHEMA_VERSION = 2

KEPT = "kept"
DISMISSED = "dismissed"

# action_taken targets (where the insight was handed off) and the kind of move
# each implies. "none" = dismissed; "save" = the quiet Zachowaj archive.
TARGET_LLM = "llm"
TARGET_TASK = "task"
TARGET_CALENDAR = "calendar"
TARGET_CLIPBOARD = "clipboard"
TARGET_SAVE = "save"
TARGET_NONE = "none"

#: target → kind (develop | do | decide | none). The instrument's core axis.
_KIND_FOR_TARGET = {
    TARGET_LLM: "develop",
    TARGET_CLIPBOARD: "develop",
    TARGET_TASK: "do",
    TARGET_CALENDAR: "decide",
    TARGET_SAVE: "none",
    TARGET_NONE: "none",
}


def kind_for_target(target: str) -> str:
    """The move-kind a handoff target implies (develop/do/decide/none)."""
    return _KIND_FOR_TARGET.get(target, "none")


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


def record_action(
    target: str,
    *,
    sig: str = "",
    conn_type: str = "",
    notes: Optional[Iterable[str]] = None,
    directions: Optional[Iterable[int]] = None,
    tool: str = "",
    kind: str = "",
    label: str = "",
    path: Optional[Path] = None,
    now: Optional[datetime] = None,
) -> bool:
    """Append one ``action_taken`` event to the signal log (ADR-004, schema v2).

    This is the instrument that replaces kept/dismissed: it records *what the
    user did with an insight* — the only honest signal of value. Action-rate
    (share of surfaced connections that produce at least one non-``none`` action)
    is the core KPI.

    ``target`` is one of the ``TARGET_*`` constants; ``kind`` is derived from it
    unless given. ``sig`` is the canonical connection signature (carried from the
    deck so it never drifts); if absent it is recomputed from ``notes`` +
    ``conn_type``. ``directions`` are the indices of the selected directions the
    handoff acted on (selection is multi). Never raises — failures are logged and
    swallowed (A1).
    """
    try:
        out = Path(path) if path is not None else signal_log_path()
        if out is None:
            logger.warning("action signal dropped: no log path (config?)")
            return False

        if not sig:
            sig = connection_signature(notes or [], conn_type) if notes else ""

        dir_list: List[int] = [int(i) for i in (directions or [])]
        stamp = (now or datetime.now()).isoformat(timespec="seconds")
        record = {
            "v": ACTION_SCHEMA_VERSION,
            "ts": stamp,
            "action": "action_taken",
            "kind": kind or kind_for_target(target),
            "target": str(target),
            "conn_type": str(conn_type),
            "sig": sig,
            "directions": dir_list,
            "n_dir": len(dir_list),
            "tool": str(tool or ""),
            "label": str(label or ""),
        }

        out.parent.mkdir(parents=True, exist_ok=True)
        with out.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(record, ensure_ascii=False) + "\n")
        return True
    except Exception as exc:
        logger.warning("could not record action signal: %s", exc)
        return False
