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


def outcome(row: dict[str, Any]) -> str:
    return "win" if (row.get("tested_reward") or 0) > 0 else "loss"


def bucket_turn(turn: int, size: int) -> str:
    start = (turn // size) * size
    return f"{start:03d}-{start + size - 1:03d}"


def avg(values: list[float]) -> str:
    if not values:
        return "0.0"
    return f"{mean(values):.1f}"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--trace", required=True)
    parser.add_argument("--summary", required=True)
    parser.add_argument("--bucket-size", type=int, default=20)
    parser.add_argument("--limit", type=int, default=40)
    args = parser.parse_args()

    trace_rows = load_jsonl(Path(args.trace))
    summary_rows = load_jsonl(Path(args.summary))
    summary_by_game = {
        (int(row["seed"]), int(row["tested_seat"])): row for row in summary_rows
    }

    per_game_mode_ships: dict[tuple[int, int, str, str], int] = defaultdict(int)
    per_game_mode_count: dict[tuple[int, int, str, str], int] = defaultdict(int)
    skipped = Counter()

    for row in trace_rows:
        if row.get("trace_error"):
            skipped["trace_error"] += 1
            continue
        key = (int(row["seed"]), int(row["tested_seat"])) if "seed" in row and "tested_seat" in row else None
        if key is None:
            skipped["missing_game_key"] += 1
            continue
        summary = summary_by_game.get(key)
        if summary is None:
            skipped["missing_summary"] += 1
            continue
        cliff = summary.get("first_prod_share_lt_40")
        if cliff is None:
            cliff = 10**9
        turn = int(row.get("step", 0))
        if turn >= int(cliff):
            skipped["post_cliff"] += 1
            continue
        if row.get("commit_allowed") is False:
            skipped["dropped"] += 1
            continue
        mode = str(row.get("mode_label", "unknown"))
        bucket = bucket_turn(turn, args.bucket_size)
        gkey = (key[0], key[1], mode, bucket)
        per_game_mode_count[gkey] += 1
        per_game_mode_ships[gkey] += int(row.get("ships", 0))

    games = sorted(summary_by_game)
    outcomes = {key: outcome(summary_by_game[key]) for key in games}

    print(f"trace_rows={len(trace_rows)} games={len(games)} skipped={dict(skipped)}")
    print(f"outcomes={dict(Counter(outcomes.values()))}")

    aggregate: dict[tuple[str, str, str], list[int]] = defaultdict(list)
    aggregate_counts: dict[tuple[str, str, str], list[int]] = defaultdict(list)
    modes = sorted({key[2] for key in per_game_mode_ships})
    buckets = sorted({key[3] for key in per_game_mode_ships})
    for game in games:
        out = outcomes[game]
        for mode in modes:
            for bucket in buckets:
                gkey = (game[0], game[1], mode, bucket)
                aggregate[(out, mode, bucket)].append(per_game_mode_ships.get(gkey, 0))
                aggregate_counts[(out, mode, bucket)].append(per_game_mode_count.get(gkey, 0))

    print("\n== Avg launched ships before production cliff")
    rows = []
    for (out, mode, bucket), values in aggregate.items():
        avg_ships = mean(values) if values else 0.0
        avg_count = mean(aggregate_counts[(out, mode, bucket)]) if values else 0.0
        if avg_ships <= 0:
            continue
        rows.append((avg_ships, out, mode, bucket, avg_count))
    for avg_ships, out, mode, bucket, avg_count in sorted(rows, reverse=True)[: args.limit]:
        print(f"{out:4s} {bucket} {mode:22s} ships={avg_ships:7.1f} commits={avg_count:5.1f}")

    print("\n== Loss minus win by mode/bucket")
    diff_rows = []
    for mode in modes:
        for bucket in buckets:
            win_vals = aggregate.get(("win", mode, bucket), [])
            loss_vals = aggregate.get(("loss", mode, bucket), [])
            if not win_vals and not loss_vals:
                continue
            win_avg = mean(win_vals) if win_vals else 0.0
            loss_avg = mean(loss_vals) if loss_vals else 0.0
            diff = loss_avg - win_avg
            if abs(diff) >= 10:
                diff_rows.append((abs(diff), diff, mode, bucket, loss_avg, win_avg))
    for _absdiff, diff, mode, bucket, loss_avg, win_avg in sorted(diff_rows, reverse=True)[: args.limit]:
        print(f"{bucket} {mode:22s} diff={diff:7.1f} loss={loss_avg:7.1f} win={win_avg:7.1f}")


if __name__ == "__main__":
    main()
