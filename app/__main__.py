"""
app/__main__ — Package entry point for `python -m app`.

Delegates to app.cli:main so the package can be invoked as:
  python -m app create_admin --email ... --password ...

This shim keeps app/cli.py importable without side effects (no asyncio.run()
at module level), which matters for unit tests that import cli functions.
"""

from app.cli import main

main()
