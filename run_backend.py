"""
run_backend.py
Use this instead of `uvicorn backend.main:app` on Windows.
Sets WindowsProactorEventLoopPolicy before uvicorn creates any event loop,
which is required for Playwright's subprocess spawning to work.
"""
import asyncio
import os
import sys


def start_server():
    # Insert cwd into sys.path since multiprocessing spawn loses it
    sys.path.insert(0, os.getcwd())
    
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    
    from uvicorn import Config, Server

    from backend.main import app

    config = Config(app=app, host="0.0.0.0", port=8000, loop="none")
    server = Server(config)

    # Run on the configured event loop
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(server.serve())

if __name__ == "__main__":
    try:
        from watchfiles import run_process
        print("Starting backend with watchfiles auto-reload...")
        run_process('backend', 'src', target=start_server)
    except ImportError:
        print("watchfiles not installed. Running without auto-reload.")
        start_server()
