"""Connection-synthesis layer ("Zestawianie").

Reads the local transcript corpus together and surfaces emergent connections
— shared threads, contradictions over time, latent ideas — as a calm weekly
digest note in the vault. 100% local, BYO-Claude. See Docs/POSITIONING.md.

Public orchestration entry points are wired in this module (see scheduler).
"""

from src.connections.scheduler import (  # noqa: F401
    DigestScheduler,
    enqueue_connection_analysis,
    run_digest_if_due,
)
