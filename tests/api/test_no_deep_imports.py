"""
tests/api/test_no_deep_imports.py — F.5 regression guard (static tests, no asyncio)

Moved from test_session2_close.py (PR6a Cleanup-4) to avoid PytestWarning:
the pytestmark = pytest.mark.asyncio on that module applied to sync test methods.

These tests verify that after PR5b:
  - intake_routes.py has no app.services.deep imports
  - client_routes.py has no app.services.deep imports
  - app/services/deep/ directory does not exist
"""


class TestIntakeRoutesHasNoDeepImports:
    """
    PR5b regression-prevention: after F.3 deletes app/services/deep/,
    intake_routes.py must not reference it. This test would have been RED
    before F.3 (TriggerDetector was imported at line 1562).

    Method: read the source file and assert no deep-service import strings.
    This catches future accidental re-introduction without requiring a running
    server (static analysis via file content check).
    """

    def test_intake_routes_has_no_deep_service_import(self):
        """
        F.5 GREEN (would have been RED before F.3).

        REQ-14: no new rows on deep_branches, and the deep service module must
        be entirely removed from the import surface of intake_routes.py.
        """
        import pathlib

        src_path = pathlib.Path(__file__).parent.parent.parent / "app" / "api" / "intake_routes.py"
        content = src_path.read_text(encoding="utf-8")

        assert "app.services.deep" not in content, (
            "intake_routes.py still references 'app.services.deep'. "
            "This import must be removed in PR5b (F.3)."
        )
        assert "from app.services.deep" not in content, (
            "intake_routes.py contains a 'from app.services.deep' import. "
            "All deep service imports must be removed in PR5b."
        )

    def test_client_routes_has_no_deep_service_import(self):
        """
        F.5 companion: client_routes.py must also be free of deep service imports.
        """
        import pathlib

        src_path = pathlib.Path(__file__).parent.parent.parent / "app" / "api" / "client_routes.py"
        content = src_path.read_text(encoding="utf-8")

        assert "app.services.deep" not in content, (
            "client_routes.py still references 'app.services.deep'."
        )

    def test_deep_service_module_does_not_exist(self):
        """
        F.5 hard guard: app/services/deep/ directory must not exist after PR5b.

        If someone accidentally recreates it, this test fails immediately.
        """
        import pathlib

        deep_dir = pathlib.Path(__file__).parent.parent.parent / "app" / "services" / "deep"
        assert not deep_dir.exists(), (
            f"app/services/deep/ directory exists at {deep_dir}. "
            "It must be deleted in PR5b (F.3). Do not re-create it."
        )
