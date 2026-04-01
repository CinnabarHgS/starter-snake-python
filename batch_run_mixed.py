import csv
import os
import time
from pathlib import Path

import run_game_mixed

SUMMARY_PATH = Path("logs/game_summaries.csv")
TARGET_SNAKE = "Candidate"
GAMES_PER_SLOT = 5
START_SEED = 2000
SLEEP_BETWEEN_GAMES = 3.0

SLOT_CONFIGS_GROUP = [
    ["Candidate", "Base1", "Base2", "Base3"],
    ["Base1", "Candidate", "Base2", "Base3"],
    ["Base1", "Base2", "Candidate", "Base3"],
    ["Base1", "Base2", "Base3", "Candidate"],
]

SLOT_INDEX = int(os.environ.get("SLOT_INDEX", "0"))
SLOT_CONFIG = SLOT_CONFIGS_GROUP[SLOT_INDEX]


def read_summary_rows():
    if not SUMMARY_PATH.exists():
        return []
    with SUMMARY_PATH.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def get_new_rows(old_count: int):
    rows = read_summary_rows()
    return rows[old_count:]


def summarize(rows: list[dict]):
    avg_placement = sum(int(r["placement"]) for r in rows) / len(rows)
    avg_turns = sum(int(r["turns_survived"]) for r in rows) / len(rows)
    avg_length = sum(int(r["final_length"]) for r in rows) / len(rows)
    avg_score = sum(float(r["performance_score"]) for r in rows) / len(rows)
    win_rate = sum(1 for r in rows if int(r["placement"]) == 1) / len(rows)

    print("===== Mixed Match Summary =====")
    print(f"Slot index: {SLOT_INDEX}")
    print(f"Slot config: {SLOT_CONFIG}")
    print(f"Valid games: {len(rows)}")
    print(f"Snake: {TARGET_SNAKE}")
    print(f"Average placement: {avg_placement:.2f}")
    print(f"Average turns survived: {avg_turns:.2f}")
    print(f"Average final length: {avg_length:.2f}")
    print(f"Average performance score: {avg_score:.4f}")
    print(f"Win rate: {win_rate:.2%}")

def append_slot_summary(valid_rows, failed_games):
    out_path = Path("logs/mixed_slot_summaries.csv")
    write_header = not out_path.exists()

    avg_placement = sum(int(r["placement"]) for r in valid_rows) / len(valid_rows)
    avg_turns = sum(int(r["turns_survived"]) for r in valid_rows) / len(valid_rows)
    avg_length = sum(int(r["final_length"]) for r in valid_rows) / len(valid_rows)
    avg_score = sum(float(r["performance_score"]) for r in valid_rows) / len(valid_rows)
    win_rate = sum(1 for r in valid_rows if int(r["placement"]) == 1) / len(valid_rows)

    with out_path.open("a", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "slot_index",
                "slot_config",
                "valid_games",
                "failed_games",
                "avg_placement",
                "avg_turns_survived",
                "avg_final_length",
                "avg_performance_score",
                "win_rate",
            ],
        )
        if write_header:
            writer.writeheader()

        writer.writerow(
            {
                "slot_index": SLOT_INDEX,
                "slot_config": str(SLOT_CONFIG),
                "valid_games": len(valid_rows),
                "failed_games": len(failed_games),
                "avg_placement": round(avg_placement, 4),
                "avg_turns_survived": round(avg_turns, 4),
                "avg_final_length": round(avg_length, 4),
                "avg_performance_score": round(avg_score, 4),
                "win_rate": round(win_rate, 4),
            }
        )

def main():
    print(f"Running mixed-match evaluation for {TARGET_SNAKE}\n")
    print(f"=== Slot config: {SLOT_CONFIG} ===")

    all_target_rows = []
    failed_games = []

    initial_rows = read_summary_rows()
    old_count = len(initial_rows)

    seed = START_SEED + SLOT_INDEX * 10000

    for game_idx in range(GAMES_PER_SLOT):
        print(f"--- Game {game_idx + 1}/{GAMES_PER_SLOT} | seed={seed} ---")
        ok = run_game_mixed.main(seed=seed, names=SLOT_CONFIG)

        time.sleep(SLEEP_BETWEEN_GAMES)

        if not ok:
            print(f"Game failed for seed={seed}\n")
            failed_games.append(seed)
            seed += 1
            continue

        new_rows = get_new_rows(old_count)
        old_count += len(new_rows)

        target_rows = [r for r in new_rows if r["snake_name"] == TARGET_SNAKE]
        if not target_rows:
            print(f"No summary row found for {TARGET_SNAKE} (seed={seed})\n")
            failed_games.append(seed)
            seed += 1
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

        seed += 1

    if not all_target_rows:
        print("No valid results collected.")
        print(f"Failed seeds: {failed_games}")
        return

    summarize(all_target_rows)
    append_slot_summary(all_target_rows, failed_games)

    print("\n===== Diagnostics =====")
    print(f"Failed games: {len(failed_games)}")
    if failed_games:
        print(f"Seeds with failed games: {failed_games}")


if __name__ == "__main__":
    main()