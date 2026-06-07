from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path


def summarize(paths: list[str]) -> None:
    by_file: dict[str, list[dict]] = defaultdict(list)
    for item in paths:
        path = Path(item)
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                by_file[path.stem].append(json.loads(line))

    for name, rows in sorted(by_file.items()):
        wins = sum(1 for row in rows if row.get("tested_reward") == 1)
        losses = sum(1 for row in rows if row.get("tested_reward") == -1)
        bad = sum(1 for row in rows if row.get("has_timeout_or_invalid"))
        avg_raw = sum(float(row.get("raw_score_diff", 0)) for row in rows) / len(rows)

        seat_parts = []
        by_seat: dict[int, list[dict]] = defaultdict(list)
        for row in rows:
            by_seat[int(row.get("tested_seat", -1))].append(row)
        for seat, seat_rows in sorted(by_seat.items()):
            seat_wins = sum(1 for row in seat_rows if row.get("tested_reward") == 1)
            seat_raw = sum(float(row.get("raw_score_diff", 0)) for row in seat_rows) / len(seat_rows)
            seat_parts.append(f"seat{seat}:{seat_wins}/{len(seat_rows)} raw={seat_raw:.1f}")

        print(
            f"{name}: wins={wins}/{len(rows)} losses={losses} "
            f"avg_raw={avg_raw:.1f} bad={bad} {'; '.join(seat_parts)}"
        )


def main() -> None:
    parser = argparse.ArgumentParser(description="Summarize Orbit Wars JSONL benchmark files.")
    parser.add_argument("jsonl", nargs="+")
    args = parser.parse_args()
    summarize(args.jsonl)


if __name__ == "__main__":
    main()
