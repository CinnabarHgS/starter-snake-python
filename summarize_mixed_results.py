import csv
from pathlib import Path

SUMMARY_PATH = Path("logs/mixed_slot_summaries.csv")

def main():
    if not SUMMARY_PATH.exists():
        print("No mixed slot summary file found.")
        return

    with SUMMARY_PATH.open("r", encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))

    if not rows:
        print("No rows found.")
        return

    total_valid = sum(int(r["valid_games"]) for r in rows)

    avg_placement = sum(float(r["avg_placement"]) * int(r["valid_games"]) for r in rows) / total_valid
    avg_turns = sum(float(r["avg_turns_survived"]) * int(r["valid_games"]) for r in rows) / total_valid
    avg_length = sum(float(r["avg_final_length"]) * int(r["valid_games"]) for r in rows) / total_valid
    avg_score = sum(float(r["avg_performance_score"]) * int(r["valid_games"]) for r in rows) / total_valid
    win_rate = sum(float(r["win_rate"]) * int(r["valid_games"]) for r in rows) / total_valid

    print("===== Overall Mixed Match Summary =====")
    print(f"Total valid games: {total_valid}")
    print(f"Average placement: {avg_placement:.2f}")
    print(f"Average turns survived: {avg_turns:.2f}")
    print(f"Average final length: {avg_length:.2f}")
    print(f"Average performance score: {avg_score:.4f}")
    print(f"Win rate: {win_rate:.2%}")

if __name__ == "__main__":
    main()