import csv
import time
from pathlib import Path
import run_game

SUMMARY_PATH = Path("logs/game_summaries.csv")
TARGET_SNAKE = "Snake4"
NUM_GAMES = 10
START_SEED = 1000
SLEEP_BETWEEN_GAMES = 3.0


def read_summary_rows():
    if not SUMMARY_PATH.exists():
        return []
    with SUMMARY_PATH.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def get_new_rows(old_count: int):
    rows = read_summary_rows()
    return rows[old_count:]


def main():
    print(f"Running {NUM_GAMES} games for {TARGET_SNAKE}...\n")

    all_target_rows = []
    failed_games = []
    missing_summary_games = []

    initial_rows = read_summary_rows()
    old_count = len(initial_rows)

    for i in range(NUM_GAMES):
        seed = START_SEED + i
        print(f"=== Game {i + 1}/{NUM_GAMES} | seed={seed} ===")

        ok = run_game.main(seed=seed)

        time.sleep(SLEEP_BETWEEN_GAMES)

        if not ok:
            print(f"Game failed for seed={seed}\n")
            failed_games.append(seed)
            continue

        new_rows = get_new_rows(old_count)
        old_count += len(new_rows)

        target_rows = [r for r in new_rows if r["snake_name"] == TARGET_SNAKE]
        if not target_rows:
            print(f"No summary row found for {TARGET_SNAKE} (seed={seed})\n")
            missing_summary_games.append(seed)
            continue

        row = target_rows[0]
        all_target_rows.append(row)

        print(
            f"placement={row['placement']}, "
            f"turns_survived={row['turns_survived']}, "
            f"final_length={row['final_length']}, "
            f"score={row['performance_score']}"
        )
        print()

    if not all_target_rows:
        print("No valid results collected.")
        print(f"Failed games: {failed_games}")
        print(f"Missing summary games: {missing_summary_games}")
        return

    avg_placement = sum(int(r["placement"]) for r in all_target_rows) / len(all_target_rows)
    avg_turns = sum(int(r["turns_survived"]) for r in all_target_rows) / len(all_target_rows)
    avg_length = sum(int(r["final_length"]) for r in all_target_rows) / len(all_target_rows)
    avg_score = sum(float(r["performance_score"]) for r in all_target_rows) / len(all_target_rows)
    win_rate = sum(1 for r in all_target_rows if int(r["placement"]) == 1) / len(all_target_rows)

    print("===== Summary =====")
    print(f"Requested games: {NUM_GAMES}")
    print(f"Valid games: {len(all_target_rows)}")
    print(f"Snake: {TARGET_SNAKE}")
    print(f"Average placement: {avg_placement:.2f}")
    print(f"Average turns survived: {avg_turns:.2f}")
    print(f"Average final length: {avg_length:.2f}")
    print(f"Average performance score: {avg_score:.4f}")
    print(f"Win rate: {win_rate:.2%}")

    print("\n===== Diagnostics =====")
    print(f"Failed games: {len(failed_games)}")
    if failed_games:
        print(f"Seeds with failed games: {failed_games}")

    print(f"Missing summary games: {len(missing_summary_games)}")
    if missing_summary_games:
        print(f"Seeds with missing summary: {missing_summary_games}")


if __name__ == "__main__":
    main()