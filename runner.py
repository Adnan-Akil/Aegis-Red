import argparse
import atexit
import os
import subprocess
import sys
import time
from pathlib import Path

import yaml


def _venv_python() -> str:
    """Return the path to the venv Python executable, cross-platform."""
    if sys.platform == "win32":
        return str(Path("venv") / "Scripts" / "python.exe")
    return str(Path("venv") / "bin" / "python")


TARGET_CONFIG = {
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
        except Exception:
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
    except Exception:
        pass

def wait_for_server(url, name, timeout=30):
    print(f"[*] Waiting for {name} ({url}) to become ready...")
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            import urllib.error
            import urllib.request
            req = urllib.request.Request(url)
            urllib.request.urlopen(req, timeout=1)
            print(f"[+] {name} is up!")
            return
        except urllib.error.HTTPError:
            # Getting an HTTP error like 404/400 means the server is UP!
            print(f"[+] {name} is up!")
            return
        except Exception:
            time.sleep(1)
    
    print(f"[-] Timed out waiting for {name} to start.")
    print("    Check if you have missing dependencies or port conflicts.")
    sys.exit(1)

def run_single_attack(venv_python: str, target_id: str, target_type: str, port: int, iterations: int, mutations: int, declared_type: str | None = None):
    """Invokes the run_attack.py script against the targeted local port."""
    cmd = [venv_python, "run_attack.py", f"http://127.0.0.1:{port}/chat", "--iter", str(iterations), "--mutations", str(mutations)]
    if declared_type:
        cmd += ["--declared_type", declared_type]
    print(f"\n[*] Launching Autonomous Agent campaign against local {target_id} ({target_type})...\n")
    try:
        subprocess.run(cmd, check=True)
    except KeyboardInterrupt:
        print("\n[!] Agent execution interrupted by user.")
        raise
    except subprocess.CalledProcessError:
        print("\n[-] Agent execution failed.")

def main():
    parser = argparse.ArgumentParser(description="Automated Unified Runner for Security Framework")
    parser.add_argument("--target", help="Target type/id OR a live URL (e.g., 'https://example.com')")
    parser.add_argument("--suite", help="Path to the master benchmark suite YAML file")
    parser.add_argument("--iter", type=int, default=5)
    parser.add_argument("--mutations", type=int, default=3, help="Max mutations per iteration")
    args = parser.parse_args()

    venv_python = os.path.abspath(_venv_python())

    # Mode 1: Running a Benchmark Suite YAML
    if args.suite:
        suite_path = Path(args.suite)
        if not suite_path.exists():
            print(f"[-] Benchmark suite file not found: {suite_path}")
            sys.exit(1)

        with open(suite_path, "r", encoding="utf-8") as f:
            suite = yaml.safe_load(f)

        suite_name = suite.get("suite_name", "Aegis-Red Benchmark Run")
        targets = suite.get("targets", [])
        factory_port = suite.get("port", 8002)

        print("==================================================")
        print(f"[*] Initializing Benchmark Suite: {suite_name}")
        print(f"[*] Total Targets to Scan: {len(targets)}")
        print("==================================================")

        for i, target in enumerate(targets, 1):
            target_id = target.get("id")
            target_name = target.get("name")
            target_type = target.get("type", "chatbot")
            
            print(f"\n[{i}/{len(targets)}] Starting Target: {target_name} ({target_id})")
            print("--------------------------------------------------")
            
            # Kill anything occupying our factory port
            kill_process_on_port(factory_port)

            # Start the dynamic benchmark factory server
            factory_script = os.path.abspath(Path("benchmark_apps") / "factory_server.py")
            
            # Start process in background
            proc = subprocess.Popen(
                [venv_python, factory_script, "--port", str(factory_port)],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            processes.append(proc)
            
            wait_for_server(f"http://127.0.0.1:{factory_port}/health", f"Factory Target ({target_id})")

            # Configure the factory server with target specification
            import json
            import urllib.request
            req = urllib.request.Request(
                f"http://127.0.0.1:{factory_port}/configure",
                data=json.dumps(target).encode("utf-8"),
                headers={"Content-Type": "application/json"}
            )
            try:
                urllib.request.urlopen(req)
                print(f"[+] Factory configured successfully for target ID: {target_id}")
            except Exception as e:
                print(f"[-] Failed to configure target factory: {e}")
                proc.terminate()
                continue

            # Execute attack campaign against the configured factory endpoint
            try:
                run_single_attack(venv_python, target_id, target_type, factory_port, args.iter, args.mutations, declared_type=target_type)
            except KeyboardInterrupt:
                break
            finally:
                # Clean up target backend process for next suite iteration
                proc.terminate()
                proc.wait()
                if proc in processes:
                    processes.remove(proc)
                    
                if i < len(targets):
                    print("[*] Sleeping 15s before next target to respect rate limits...")
                    time.sleep(15)

        print("\n[+] Benchmark Suite Execution Completed.")
        return

    # Mode 2: Standard/Direct CLI Target Runs
    if not args.target:
        print("[-] Error: You must specify either --target or --suite to run.")
        sys.exit(1)

    # If the user provides a direct URL, bypass local server startup completely
    if args.target.startswith("http"):
        print("==================================================")
        print(f"[*] Initializing External Live Target: {args.target}")
        print("==================================================")
        print("\n[*] Launching Autonomous Agent against live URL...\n")
        try:
            subprocess.run([venv_python, "run_attack.py", args.target, "--iter", str(args.iter), "--mutations", str(args.mutations)], check=True)
        except subprocess.CalledProcessError:
            print("[-] Framework execution failed.")
        except KeyboardInterrupt:
            print("\n[!] Execution interrupted by user.")
        return

    # Check if this is a legacy local benchmark target config
    if args.target in TARGET_CONFIG:
        config = TARGET_CONFIG[args.target]
        base_dir = os.path.abspath(config["dir"])

        print("==================================================")
        print(f"[*] Initializing Unified Runner: {args.target}")
        print("==================================================")

        if config.get("type") == "static":
            print(f"[*] Starting Static Server for {args.target} on port {config['port']}...")
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

        # Run attack campaign
        run_single_attack(venv_python, args.target, "legacy", target_port, args.iter, args.mutations)
    else:
        # Otherwise try to match target from our master blueprint
        suite_path = Path("benchmark_suite.yaml")
        if not suite_path.exists():
            print(f"[-] Invalid target '{args.target}' and no default benchmark_suite.yaml blueprint found.")
            sys.exit(1)

        with open(suite_path, "r", encoding="utf-8") as f:
            suite = yaml.safe_load(f)

        target_data = next((t for t in suite.get("targets", []) if t.get("id") == args.target), None)
        if not target_data:
            print(f"[-] Target ID '{args.target}' not found in suite blueprint.")
            sys.exit(1)

        # Startup factory server for this single target
        factory_port = suite.get("port", 8002)
        kill_process_on_port(factory_port)
        
        factory_script = os.path.abspath(Path("benchmark_apps") / "factory_server.py")
        proc = subprocess.Popen(
            [venv_python, factory_script, "--port", str(factory_port)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        processes.append(proc)
        
        wait_for_server(f"http://127.0.0.1:{factory_port}/health", f"Factory Target ({args.target})")

        # Configure
        import json
        import urllib.request
        req = urllib.request.Request(
            f"http://127.0.0.1:{factory_port}/configure",
            data=json.dumps(target_data).encode("utf-8"),
            headers={"Content-Type": "application/json"}
        )
        urllib.request.urlopen(req)

        # Run
        try:
            run_single_attack(venv_python, args.target, target_data.get("type", "chatbot"), factory_port, args.iter, args.mutations, declared_type=target_data.get("type"))
        finally:
            proc.terminate()

if __name__ == "__main__":
    main()

