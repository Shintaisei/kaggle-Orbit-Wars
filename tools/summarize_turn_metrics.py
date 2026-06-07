from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path
from statistics import mean
from typing import Any


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows = []
    with path.open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def avg_value(rows: list[dict[str, Any]], key: str) -> str:
    vals = [row.get(key) for row in rows if row.get(key) is not None]
    if not vals:
        return "na"
    return f"{mean(float(v) for v in vals):.1f}"


def bucket(row: dict[str, Any]) -> str:
    return "win" if (row.get("tested_reward") or 0) > 0 else str(row.get("failure_bucket", "loss"))


def row_at_or_after(rows: list[dict[str, Any]], turn: int) -> dict[str, Any] | None:
    for row in rows:
        if int(row["turn"]) >= turn:
            return row
    return rows[-1] if rows else None


def summarize_summary(summary_rows: list[dict[str, Any]]) -> None:
    print("== Game Summary")
    print(f"games={len(summary_rows)}")
    print(f"buckets={dict(Counter(bucket(row) for row in summary_rows))}")
    by_seat: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for row in summary_rows:
        by_seat[int(row["tested_seat"])].append(row)
    for seat, rows in sorted(by_seat.items()):
        wins = sum(1 for row in rows if (row.get("tested_reward") or 0) > 0)
        raw0 = sum(1 for row in rows if row.get("raw_zero_collapse"))
        print(
            f"seat={seat} wins={wins}/{len(rows)} raw0={raw0} "
            f"avg_raw_diff={avg_value(rows, 'final_raw_diff')} "
            f"avg_first_large_launch={avg_value(rows, 'first_large_launch')} "
            f"avg_first_raw_lt_-500={avg_value(rows, 'first_raw_diff_lt_minus_500')} "
            f"avg_first_prod_lt_40={avg_value(rows, 'first_prod_share_lt_40')}"
        )
    for name, rows in sorted(defaultdict(list, {}).items()):
        print(name, rows)
    by_bucket: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in summary_rows:
        by_bucket[bucket(row)].append(row)
    for name, rows in sorted(by_bucket.items()):
        print(
            f"bucket={name} n={len(rows)} "
            f"avg_raw_diff={avg_value(rows, 'final_raw_diff')} "
            f"raw0={sum(1 for row in rows if row.get('raw_zero_collapse'))} "
            f"avg_first_large_launch={avg_value(rows, 'first_large_launch')} "
            f"avg_first_raw_lt_-500={avg_value(rows, 'first_raw_diff_lt_minus_500')} "
            f"avg_first_prod_lt_40={avg_value(rows, 'first_prod_share_lt_40')}"
        )


def summarize_turns(turn_rows: list[dict[str, Any]], turns: list[int]) -> None:
    print("\n== Turn Snapshots")
    by_game: dict[tuple[int, int], list[dict[str, Any]]] = defaultdict(list)
    for row in turn_rows:
        by_game[(int(row["seed"]), int(row["tested_seat"]))].append(row)
    for key in by_game:
        by_game[key].sort(key=lambda row: int(row["turn"]))

    summaries = []
    for (seed, seat), rows in by_game.items():
        final = rows[-1]
        outcome = "win" if int(final["raw_diff"]) >= 0 and int(final["tested_total_raw"]) > 0 else "loss"
        summaries.append((seed, seat, outcome, rows))

    for turn in turns:
        print(f"\n-- turn>={turn}")
        for outcome in ("win", "loss"):
            selected = []
            for _seed, _seat, item_outcome, rows in summaries:
                if item_outcome == outcome:
                    row = row_at_or_after(rows, turn)
                    if row is not None:
                        selected.append(row)
            if not selected:
                continue
            print(
                f"{outcome} n={len(selected)} "
                f"prod={avg_value(selected, 'tested_production')} "
                f"prod_diff={avg_value(selected, 'production_diff')} "
                f"raw={avg_value(selected, 'tested_total_raw')} "
                f"raw_diff={avg_value(selected, 'raw_diff')} "
                f"fleet_ratio={avg_value(selected, 'tested_fleet_raw_ratio')} "
                f"launch_ships={avg_value(selected, 'tested_launched_ships')}"
            )

    print("\n== Largest Launches In Losses")
    loss_rows = []
    for seed, seat, outcome, rows in summaries:
        if outcome != "loss":
            continue
        for row in rows:
            loss_rows.append((int(row["tested_launched_ships"]), seed, seat, int(row["turn"]), row))
    for ships, seed, seat, turn, row in sorted(loss_rows, reverse=True)[:20]:
        if ships <= 0:
            break
        print(
            f"ships={ships} seed={seed} seat={seat} turn={turn} "
            f"raw={row['tested_total_raw']} raw_diff={row['raw_diff']} "
            f"prod={row['tested_production']} prod_diff={row['production_diff']} "
            f"fleet_ratio={row['tested_fleet_raw_ratio']}"
        )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--summary", required=True)
    parser.add_argument("--turns", required=True)
    parser.add_argument("--check-turns", default="25,40,60,80,100,140")
    args = parser.parse_args()

    summary_rows = load_jsonl(Path(args.summary))
    turn_rows = load_jsonl(Path(args.turns))
    check_turns = [int(part) for part in args.check_turns.split(",") if part.strip()]
    summarize_summary(summary_rows)
    summarize_turns(turn_rows, check_turns)


if __name__ == "__main__":
    main()
