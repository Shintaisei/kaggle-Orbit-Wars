from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path
from statistics import mean
from typing import Any


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def split_csv(value: str) -> list[str]:
    return [part.strip() for part in value.split(",") if part.strip()]


def outcome(summary: dict[str, Any]) -> str:
    return "win" if (summary.get("tested_reward") or 0) > 0 else "loss"


def fleet_ratio_bucket(value: Any) -> str:
    ratio = float(value)
    if ratio >= 0.75:
        return "fleet>=0.75"
    if ratio >= 0.65:
        return "fleet0.65-0.75"
    if ratio >= 0.55:
        return "fleet0.55-0.65"
    if ratio >= 0.45:
        return "fleet0.45-0.55"
    return "fleet<0.45"


def production_bucket(value: Any) -> str:
    diff = int(value)
    if diff >= 5:
        return "prod>=5"
    if diff >= 1:
        return "prod1-4"
    if diff >= 0:
        return "prod0"
    if diff >= -4:
        return "prod-1..-4"
    return "prod<=-5"


def raw_bucket(value: Any) -> str:
    diff = int(value)
    if diff >= 500:
        return "raw>=500"
    if diff >= 0:
        return "raw0-499"
    if diff >= -500:
        return "raw-1..-499"
    return "raw<=-500"


def in_mode_filter(mode: str, filters: list[str]) -> bool:
    if not filters:
        return True
    return any(mode == item or mode.startswith(item) for item in filters)


def summarize_window(
    *,
    window_label: str,
    trace_rows: list[dict[str, Any]],
    turns_by_key: dict[tuple[int, int, int], dict[str, Any]],
    summary_by_game: dict[tuple[int, int], dict[str, Any]],
    start_turn: int,
    end_turn: int,
    stop_at_cliff: bool,
    mode_filters: list[str],
    limit: int,
) -> None:
    games = sorted(summary_by_game)
    game_outcomes = {game: outcome(summary_by_game[game]) for game in games}
    aggregate: dict[tuple[str, str, str, str, str], list[int]] = defaultdict(list)
    aggregate_counts: dict[tuple[str, str, str, str, str], list[int]] = defaultdict(list)
    per_game_ships: dict[tuple[int, int, str, str, str, str], int] = defaultdict(int)
    per_game_count: dict[tuple[int, int, str, str, str, str], int] = defaultdict(int)
    skipped = Counter()
    modes_seen = Counter()

    for row in trace_rows:
        if row.get("trace_error"):
            skipped["trace_error"] += 1
            continue
        if row.get("commit_allowed") is False:
            skipped["dropped"] += 1
            continue
        if "seed" not in row or "tested_seat" not in row:
            skipped["missing_game_key"] += 1
            continue
        if row.get("player") is not None and int(row["player"]) != int(row["tested_seat"]):
            skipped["player_mismatch"] += 1
            continue
        turn = int(row.get("step", 0))
        if turn < start_turn or turn >= end_turn:
            skipped["outside_window"] += 1
            continue
        game = (int(row["seed"]), int(row["tested_seat"]))
        summary = summary_by_game.get(game)
        if summary is None:
            skipped["missing_summary"] += 1
            continue
        cliff = summary.get("first_prod_share_lt_40")
        if stop_at_cliff and cliff is not None and turn >= int(cliff):
            skipped["post_cliff"] += 1
            continue
        mode = str(row.get("mode_label", "unknown"))
        modes_seen[mode] += 1
        if not in_mode_filter(mode, mode_filters):
            skipped["mode_filter"] += 1
            continue
        turn_row = turns_by_key.get((game[0], game[1], turn))
        if turn_row is None:
            skipped["missing_turn"] += 1
            continue
        pressure = (
            fleet_ratio_bucket(turn_row["tested_fleet_raw_ratio"]),
            production_bucket(turn_row["production_diff"]),
            raw_bucket(turn_row["raw_diff"]),
        )
        key = (game[0], game[1], mode, *pressure)
        per_game_ships[key] += int(row.get("ships", 0))
        per_game_count[key] += 1

    modes = sorted({key[2] for key in per_game_ships})
    pressure_keys = sorted({key[3:] for key in per_game_ships})
    for game in games:
        out = game_outcomes[game]
        for mode in modes:
            for pressure in pressure_keys:
                gkey = (game[0], game[1], mode, *pressure)
                akey = (out, mode, *pressure)
                aggregate[akey].append(per_game_ships.get(gkey, 0))
                aggregate_counts[akey].append(per_game_count.get(gkey, 0))

    print(f"\n# Window {window_label} start={start_turn} end={end_turn} stop_at_cliff={stop_at_cliff}")
    print(f"games={len(games)} outcomes={dict(Counter(game_outcomes.values()))} skipped={dict(skipped)}")
    print(f"modes_seen={dict(modes_seen.most_common(20))}")

    rows = []
    for key, values in aggregate.items():
        avg_ships = mean(values) if values else 0.0
        if avg_ships <= 0:
            continue
        avg_count = mean(aggregate_counts[key]) if aggregate_counts[key] else 0.0
        out, mode, fleet_b, prod_b, raw_b = key
        nonzero_games = sum(1 for value in values if value > 0)
        rows.append((avg_ships, out, mode, fleet_b, prod_b, raw_b, avg_count, nonzero_games, len(values)))

    print("\n== Avg ships per game by outcome/mode/pressure")
    for avg_ships, out, mode, fleet_b, prod_b, raw_b, avg_count, nonzero, denom in sorted(rows, reverse=True)[:limit]:
        print(
            f"{out:4s} {mode:34s} {fleet_b:14s} {prod_b:10s} {raw_b:12s} "
            f"ships={avg_ships:7.1f} commits={avg_count:5.1f} games={nonzero}/{denom}"
        )

    print("\n== Loss minus win by mode/pressure")
    diff_rows = []
    mode_pressure = sorted({key[1:] for key in aggregate})
    for mode, fleet_b, prod_b, raw_b in mode_pressure:
        win_vals = aggregate.get(("win", mode, fleet_b, prod_b, raw_b), [])
        loss_vals = aggregate.get(("loss", mode, fleet_b, prod_b, raw_b), [])
        if not win_vals and not loss_vals:
            continue
        win_avg = mean(win_vals) if win_vals else 0.0
        loss_avg = mean(loss_vals) if loss_vals else 0.0
        diff = loss_avg - win_avg
        if abs(diff) >= 10:
            diff_rows.append((abs(diff), diff, mode, fleet_b, prod_b, raw_b, loss_avg, win_avg))
    for _absdiff, diff, mode, fleet_b, prod_b, raw_b, loss_avg, win_avg in sorted(diff_rows, reverse=True)[:limit]:
        print(
            f"{mode:34s} {fleet_b:14s} {prod_b:10s} {raw_b:12s} "
            f"diff={diff:7.1f} loss={loss_avg:7.1f} win={win_avg:7.1f}"
        )


def main() -> None:
    parser = argparse.ArgumentParser(description="Join Orbit Wars mode trace to turn pressure metrics.")
    parser.add_argument("--trace", required=True)
    parser.add_argument("--turns", required=True)
    parser.add_argument("--summary", required=True)
    parser.add_argument("--start-turn", type=int, default=80)
    parser.add_argument("--end-turns", default="100,120", help="Comma-separated exclusive end turns.")
    parser.add_argument("--mode-prefixes", default="hammer,mega-hammer,search-expand,doom-evac")
    parser.add_argument("--include-post-cliff", action="store_true")
    parser.add_argument("--limit", type=int, default=40)
    args = parser.parse_args()

    trace_rows = load_jsonl(Path(args.trace))
    turn_rows = load_jsonl(Path(args.turns))
    summary_rows = load_jsonl(Path(args.summary))
    turns_by_key = {
        (int(row["seed"]), int(row["tested_seat"]), int(row["turn"])): row
        for row in turn_rows
    }
    summary_by_game = {
        (int(row["seed"]), int(row["tested_seat"])): row
        for row in summary_rows
    }
    mode_filters = split_csv(args.mode_prefixes)
    for end_turn in [int(item) for item in split_csv(args.end_turns)]:
        summarize_window(
            window_label=f"{args.start_turn}-{end_turn}",
            trace_rows=trace_rows,
            turns_by_key=turns_by_key,
            summary_by_game=summary_by_game,
            start_turn=args.start_turn,
            end_turn=end_turn,
            stop_at_cliff=not args.include_post_cliff,
            mode_filters=mode_filters,
            limit=args.limit,
        )


if __name__ == "__main__":
    main()
