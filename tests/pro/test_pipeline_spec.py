"""Executable spec for the PRO backend pipeline + licensing (v2.1.0).

Covers the daemon → Supabase → embeddings flow, license/JWT exchange, and the
auto-config wizard. SKIPPED until ``malinche_pro`` exists; see
Docs/TESTING-PRO-MCP.md.
"""

import pytest

pytest.importorskip(
    "malinche_pro",
    reason="malinche_pro is a private package shipped with PRO (v2.1.0)",
)

pytestmark = pytest.mark.pro


class TestDaemonUpload:
    def test_new_markdown_triggers_upload_and_embedding(self):
        # WHEN a .md file appears in the watched folder
        # THEN it is uploaded to Supabase and an embedding request is issued
        raise NotImplementedError

    def test_unchanged_file_is_idempotent_by_sha256(self):
        # Re-processing the same content must not create a duplicate row
        raise NotImplementedError

    def test_updated_file_replaces_existing_row(self):
        raise NotImplementedError


class TestLicenseJWT:
    def test_valid_key_exchanges_for_jwt_with_tier_and_expiry(self):
        raise NotImplementedError

    def test_offline_uses_cached_license_within_7_days(self):
        raise NotImplementedError

    def test_cache_older_than_7_days_falls_back_to_free(self):
        raise NotImplementedError

    def test_invalid_key_returns_actionable_error(self):
        raise NotImplementedError


class TestEmbeddingsClient:
    def test_workers_endpoint_never_persists_raw_transcript(self):
        # Privacy gate: /v1/embeddings returns vectors only, stores nothing
        raise NotImplementedError


class TestAutoConfigWizard:
    @pytest.mark.parametrize(
        "client",
        ["claude_desktop", "cursor", "continue", "claude_code"],
    )
    def test_writes_valid_mcp_config_for(self, client):
        # THEN the client's MCP config gains a valid malinche entry,
        # existing entries are preserved (merge, not overwrite)
        raise NotImplementedError
