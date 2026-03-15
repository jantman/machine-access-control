"""Export OpenAPI spec from the Quart app for Sphinx docs."""

import asyncio
import json
import os
import pathlib


def export_openapi() -> None:
    """Export OpenAPI JSON spec to docs/source/openapi.json."""
    os.environ.setdefault("MACHINES_CONFIG", "tests/fixtures/machines.json")
    os.environ.setdefault("USERS_CONFIG", "tests/fixtures/users.json")

    from dm_mac import create_app

    async def _export() -> None:
        app = create_app()
        client = app.test_client()
        resp = await client.get("/openapi.json")
        data = await resp.get_json()
        pathlib.Path("docs/source/openapi.json").write_text(
            json.dumps(data, indent=2) + "\n"
        )

    asyncio.run(_export())


if __name__ == "__main__":
    export_openapi()
