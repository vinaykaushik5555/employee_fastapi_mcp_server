from __future__ import annotations

import sys

import uvicorn

from app.app_factory import create_app
from app.mcp_server import mcp

app = create_app()


if __name__ == "__main__":
    # Usage:
    #   REST API: python main.py
    #   MCP:      python main.py mcp
    if len(sys.argv) > 1 and sys.argv[1].lower() == "mcp":
        mcp.run()
    else:
        uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
