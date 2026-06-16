import argparse
import subprocess
import time
import urllib.request
import os
import sys
import atexit
from pathlib import Path

def _venv_python() -> str:
    """Return the path to the venv Python executable, cross-platform."""
    if sys.platform == "win32":
        return str(Path("venv") / "Scripts" / "python.exe")
    return str(Path("venv") / "bin" / "python")


TARGET_CONFIG = {
    "hardened_bot": {
        "dir": "benchmark_apps/hardened_variants",
        "backend_port": 8002
    },
    "hardened_rag": {
        "dir": "benchmark_apps/hardened_variants",
        "backend_port": 8002
    },
    "hardened_tool": {
        "dir": "benchmark_apps/hardened_variants",
        "backend_port": 8002
    },
    "sdk_chatbot": {
        "dir": "test_targets/vercel_boilerplate",
        "type": "static",
        "port": 8003
    },
    "streamlit_rag": {
        "dir": "test_targets/streamlit_rag",
        "type": "streamlit",
        "port": 8501
    }
}

processes = []

def cleanup():
    """Kill all background servers when the script exits."""
    if processes:
        print("\n[+] Cleaning up background servers...")
    for p in processes:
        try:
            p.terminate()
            p.kill()
        except:
            pass

atexit.register(cleanup)

def kill_process_on_port(port):
    """Kills any process listening on the given port to prevent port conflicts."""
    try:
        if os.name == "nt":
            result = subprocess.run(["netstat", "-ano"], capture_output=True, text=True)
            for line in result.stdout.splitlines():
                if f":{port}" in line and "LISTENING" in line:
                    parts = line.strip().split()
                    if len(parts) >= 5:
                        pid = parts[-1]
                        print(f"[*] Force killing zombie process (PID {pid}) on port {port}...")
                        subprocess.run(["taskkill", "/F", "/PID", pid], capture_output=True)
        else:
            # For Linux/Mac compatibility just in case
            subprocess.run(["fuser", "-k", f"{port}/tcp"], capture_output=True)
    except Exception as e:
        pass

def wait_for_server(url, name, timeout=30):
    print(f"[*] Waiting for {name} ({url}) to become ready...")
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            import urllib.error
            req = urllib.request.Request(url)
            urllib.request.urlopen(req, timeout=1)
            print(f"[+] {name} is up!")
            return
        except urllib.error.HTTPError:
            # Getting an HTTP error like 404 means the server is UP!
            print(f"[+] {name} is up!")
            return
        except Exception:
            time.sleep(1)
    
    print(f"[-] Timed out waiting for {name} to start.")
    print("    Check if you have missing dependencies or port conflicts.")
    sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="Automated Unified Runner for Security Framework")
    parser.add_argument("--target", required=True, help="Target type (e.g., 'rag') OR a live URL (e.g., 'https://example.com')")
    parser.add_argument("--iter", type=int, default=5)
    args = parser.parse_args()

    venv_python = os.path.abspath(_venv_python())

    # If the user provides a direct URL, bypass local server startup completely
    if args.target.startswith("http"):
        print("==================================================")
        print(f"🚀 Initializing External Live Target: {args.target}")
        print("==================================================")
        print(f"\n🤖 Launching Autonomous Agent against live URL...\n")
        try:
            subprocess.run([venv_python, "run_attack.py", args.target, "--iter", str(args.iter)], check=True)
        except subprocess.CalledProcessError:
            print("[-] Framework execution failed.")
        except KeyboardInterrupt:
            print("\n[!] Execution interrupted by user.")
        return

    # Otherwise, it must be a local benchmark target
    if args.target not in TARGET_CONFIG:
        print(f"[-] Invalid target '{args.target}'. Valid benchmarks are: {list(TARGET_CONFIG.keys())}")
        sys.exit(1)

    config = TARGET_CONFIG[args.target]
    base_dir = os.path.abspath(config["dir"])
    
    # Setup paths
    venv_python = os.path.abspath(_venv_python())
    npm_cmd = "npm.cmd" if os.name == "nt" else "npm"

    print("==================================================")
    print(f"🚀 Initializing Unified Runner: {args.target}")
    print("==================================================")

    # 1. Handle different target types
    if config.get("type") == "static":
        print(f"[*] Starting Static Server for {args.target} on port {config['port']}...")
        # Use python's http.server for simplicity
        proc = subprocess.Popen(
            [venv_python, "-m", "http.server", str(config["port"])],
            cwd=base_dir,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        processes.append(proc)
        wait_for_server(f"http://localhost:{config['port']}/", "Static Server")
        target_port = config["port"]

    elif config.get("type") == "streamlit":
        print(f"[*] Starting Streamlit App on port {config['port']}...")
        proc = subprocess.Popen(
            [venv_python, "-m", "streamlit", "run", "app.py", "--server.port", str(config["port"]), "--server.headless", "true"],
            cwd=base_dir,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        processes.append(proc)
        wait_for_server(f"http://localhost:{config['port']}/", "Streamlit App")
        target_port = config["port"]

    else:
        # Default behavior for Vite/FastAPI targets
        kill_process_on_port(config["backend_port"])
        kill_process_on_port(5173)

        # Start Backend
        backend_dir = os.path.join(base_dir, "backend")
        print(f"[*] Starting Backend on port {config['backend_port']}...")
        backend_proc = subprocess.Popen(
            [venv_python, "-m", "uvicorn", "main:app", "--port", str(config["backend_port"])],
            cwd=backend_dir,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        processes.append(backend_proc)

        # Start Frontend
        frontend_dir = os.path.join(base_dir, "frontend")
        print("[*] Starting React Frontend on port 5173...")
        frontend_proc = subprocess.Popen(
            [npm_cmd, "run", "dev", "--", "--port", "5173", "--strictPort"],
            cwd=frontend_dir
        )
        processes.append(frontend_proc)

        wait_for_server(f"http://127.0.0.1:{config['backend_port']}/", "Backend")
        wait_for_server("http://localhost:5173/", "Frontend")
        target_port = "5173"

    # 4. Execute the Red Team Agent!
    print(f"\n🤖 Launching Autonomous Agent against local {args.target}...\n")
    try:
        subprocess.run(
            [venv_python, "run_attack.py", args.target, "--port", str(target_port), "--iter", str(args.iter)],
            check=True
        )
    except KeyboardInterrupt:
        print("\n[!] Agent execution interrupted by user.")
    except subprocess.CalledProcessError:
        print("\n[-] Agent execution failed.")

if __name__ == "__main__":
    main()
