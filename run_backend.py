"""
run_backend.py
Use this instead of `uvicorn backend.main:app` on Windows.
Sets WindowsProactorEventLoopPolicy before uvicorn creates any event loop,
which is required for Playwright's subprocess spawning to work.
"""
import sys
import asyncio

# ── Must happen before ANY asyncio / uvicorn import ───────────────────────────
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    loop = asyncio.ProactorEventLoop()
    asyncio.set_event_loop(loop)

import uvicorn

if __name__ == "__main__":
    from uvicorn import Config, Server
    from backend.main import app

    config = Config(app=app, host="0.0.0.0", port=8000, loop="none")
    server = Server(config)

    # Run on the configured event loop
    loop = asyncio.get_event_loop()
    loop.run_until_complete(server.serve())
