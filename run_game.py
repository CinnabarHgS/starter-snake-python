import json
import subprocess
import time
from pathlib import Path

MAX_TURNS = 300
LOG_PATH = Path("game.json")


def build_cmd(seed: int):
    return [
        r".\battlesnake.exe", "play",
        "-W", "11", "-H", "11",
        "-g", "standard",
        "-m", "hz_hazard_pits",
        "--name", "Snake1", "--url", "http://127.0.0.1:8000",
        "--name", "Snake2", "--url", "http://127.0.0.1:8001",
        "--name", "Snake3", "--url", "http://127.0.0.1:8002",
        "--name", "Snake4", "--url", "http://127.0.0.1:8003",
        "--foodSpawnChance", "25",
        "--minimumFood", "2",
        "--seed", str(seed),
        "--timeout", "1000",
        "--output", str(LOG_PATH),
    ]


def load_last_state(path: Path):
    if not path.exists():
        return None

    with path.open("r", encoding="utf-8") as f:
        lines = f.read().splitlines()

    for line in reversed(lines):
        if not line.strip():
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(obj, dict) and "turn" in obj:
            return obj

    return None


def main(seed: int = 123) -> bool:
    if LOG_PATH.exists():
        LOG_PATH.unlink()

    proc = None
    last_turn = -1
    last_state = None

    try:
        proc = subprocess.Popen(build_cmd(seed))

        while proc.poll() is None:
            state = load_last_state(LOG_PATH)
            if state is not None:
                last_state = state
                turn = int(state.get("turn", -1))

                if turn != -1 and turn != last_turn:
                    last_turn = turn
                    print(f"turn={turn}")

                if turn >= MAX_TURNS:
                    print(f"Reached cap at turn {turn}. Stopping game.")
                    proc.terminate()
                    try:
                        proc.wait(timeout=3)
                    except subprocess.TimeoutExpired:
                        proc.kill()
                    break

            time.sleep(0.1)

        # 进程结束后，再等一下，确保 output file 写完
        time.sleep(0.3)

        # 再读一次最终状态
        final_state = load_last_state(LOG_PATH)
        if final_state is not None:
            last_state = final_state

    except Exception as e:
        print(f"Error running game: {e}")
        return False

    finally:
        if proc is not None and proc.poll() is None:
            proc.kill()

    print("Game end")

    # 只要能读到最终状态，就算成功
    if last_state is None:
        print("No final state found.")
        return False

    for snake in last_state["board"]["snakes"]:
        print(snake["name"], snake["length"])

    return True


if __name__ == "__main__":
    main()