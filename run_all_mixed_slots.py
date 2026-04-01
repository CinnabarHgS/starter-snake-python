import os
import subprocess
import sys
import time
from pathlib import Path

PORTS = [8000, 8001, 8002, 8003]
WAIT_SERVER_START = 2.0
WAIT_BETWEEN_SLOTS = 2.0


def launch_servers(candidate_slot: int):
    """
    candidate_slot:
        0 -> 8000 跑 MCTS
        1 -> 8001 跑 MCTS
        2 -> 8002 跑 MCTS
        3 -> 8003 跑 MCTS
    """
    procs = []
    log_dir = Path("logs/server_logs")
    log_dir.mkdir(parents=True, exist_ok=True)

    for idx, port in enumerate(PORTS):
        script = "main_mcts.py" if idx == candidate_slot else "main_heuristic.py"

        env = os.environ.copy()
        env["PORT"] = str(port)

        log_path = log_dir / f"slot{candidate_slot}_port{port}.log"
        log_file = open(log_path, "w", encoding="utf-8")

        proc = subprocess.Popen(
            [sys.executable, script],
            env=env,
            stdout=log_file,
            stderr=subprocess.STDOUT,
        )
        procs.append((proc, log_file, script, port))

    time.sleep(WAIT_SERVER_START)
    return procs


def stop_servers(procs):
    for proc, log_file, script, port in procs:
        try:
            proc.terminate()
        except Exception:
            pass

    for proc, log_file, script, port in procs:
        try:
            proc.wait(timeout=3)
        except subprocess.TimeoutExpired:
            proc.kill()
        finally:
            log_file.close()


def run_one_slot(slot_index: int):
    env = os.environ.copy()
    env["SLOT_INDEX"] = str(slot_index)

    print(f"\n===== Running slot {slot_index} =====")

    result = subprocess.run(
        [sys.executable, "batch_run_mixed.py"],
        env=env,
    )
    return result.returncode


def main():
    for slot_index in range(4):
        print(f"\n==============================")
        print(f"Starting mixed-match slot {slot_index}")
        print(f"Candidate will run on port {PORTS[slot_index]}")
        print(f"==============================")

        procs = launch_servers(slot_index)

        try:
            code = run_one_slot(slot_index)
            print(f"batch_run_mixed.py finished with code {code}")
        finally:
            stop_servers(procs)

        time.sleep(WAIT_BETWEEN_SLOTS)

    print("\nAll 4 slot configurations finished.")


if __name__ == "__main__":
    main()