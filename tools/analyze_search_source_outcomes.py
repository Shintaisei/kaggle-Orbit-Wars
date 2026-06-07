from __future__ import annotations

import argparse
import json
import os
import tempfile
import time
from collections import Counter, defaultdict
from pathlib import Path
from statistics import mean
from typing import Any

from kaggle_environments import make

from analyze_turn_metrics import (
    build_agents,
    classify_failure,
    final_board_observation,
    first_turn,
    get_value,
    normalize_status,
    seat_metrics,
    split_csv,
)


PLANET_OWNER = 1
PLANET_SHIPS = 5
PLANET_PRODUCTION = 6


def parse_cases(value: str) -> list[tuple[int, int]]:
    cases: list[tuple[int, int]] = []
    for part in split_csv(value):
        seed_text, seat_text = part.split(":", 1)
        cases.append((int(seed_text), int(seat_text)))
    return cases


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not path.exists():
        return rows
    with path.open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                rows.append({"trace_error": "json_decode"})
    return rows


def planet_by_id(obs: Any) -> dict[int, list[Any]]:
    return {int(planet[0]): planet for planet in (get_value(obs, "planets", []) or [])}


def planet_owner(obs_by_turn: dict[int, Any], turn: int, planet_id: int) -> int | None:
    obs = obs_by_turn.get(turn)
    if obs is None:
        return None
    planet = planet_by_id(obs).get(int(planet_id))
    return None if planet is None else int(planet[PLANET_OWNER])


def planet_value(obs_by_turn: dict[int, Any], turn: int, planet_id: int, idx: int) -> int | None:
    obs = obs_by_turn.get(turn)
    if obs is None:
        return None
    planet = planet_by_id(obs).get(int(planet_id))
    return None if planet is None else int(planet[idx])


def source_first_lost_turn(obs_by_turn: dict[int, Any], start_turn: int, horizon: int, src_id: int, player: int) -> int | None:
    end_turn = min(max(obs_by_turn) if obs_by_turn else start_turn, start_turn + horizon)
    for turn in range(start_turn + 1, end_turn + 1):
        owner = planet_owner(obs_by_turn, turn, src_id)
        if owner is not None and owner != player:
            return turn
    return None


def turn_pressure(obs: Any, seats: int, tested_seat: int) -> dict[str, Any]:
    metrics = seat_metrics(obs, seats)
    tested = metrics[tested_seat]
    opp_items = [(idx, item) for idx, item in enumerate(metrics) if idx != tested_seat]
    _opp_seat, max_opp = max(opp_items, key=lambda item: int(item[1]["total_raw"]))
    return {
        "tested_fleet_raw_ratio": round(float(tested["fleet_raw_ratio"]), 4),
        "tested_production": int(tested["production"]),
        "max_opp_production": int(max_opp["production"]),
        "production_diff": int(tested["production"]) - int(max_opp["production"]),
        "tested_total_raw": int(tested["total_raw"]),
        "max_opp_total_raw": int(max_opp["total_raw"]),
        "raw_diff": int(tested["total_raw"]) - int(max_opp["total_raw"]),
        "tested_owned_planets": int(tested["owned_planets"]),
        "tested_production_share": round(float(tested["production_share"]), 4),
    }


def turn_rows_for_summary(obs_by_turn: dict[int, Any], seats: int, tested_seat: int) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    prev: dict[str, Any] | None = None
    for turn in sorted(obs_by_turn):
        pressure = turn_pressure(obs_by_turn[turn], seats, tested_seat)
        row = {
            "turn": turn,
            "tested_owned_planets": pressure["tested_owned_planets"],
            "tested_production": pressure["tested_production"],
            "max_opp_production": pressure["max_opp_production"],
            "tested_total_raw": pressure["tested_total_raw"],
            "raw_diff": pressure["raw_diff"],
            "tested_planet_ships": 0,
            "max_opp_planet_ships": 0,
            "tested_fleet_raw_ratio": pressure["tested_fleet_raw_ratio"],
            "tested_launched_ships": 0,
            "tested_production_share": pressure["tested_production_share"],
        }
        if prev is not None:
            row["delta_tested_production"] = int(row["tested_production"]) - int(prev["tested_production"])
        else:
            row["delta_tested_production"] = 0
        rows.append(row)
        prev = row
    return rows


def raw_diff_from_final(obs: Any, seats: int, tested_seat: int) -> tuple[int, int]:
    metrics = seat_metrics(obs, seats)
    tested = metrics[tested_seat]
    max_opp = max(
        (item for idx, item in enumerate(metrics) if idx != tested_seat),
        key=lambda item: int(item["total_raw"]),
    )
    return int(tested["total_raw"]), int(tested["total_raw"]) - int(max_opp["total_raw"])


def run_game_with_search_outcomes(
    *,
    seed: int,
    agent: str,
    opponents: list[str],
    seats: int,
    tested_seat: int,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    agents = build_agents(agent, opponents, seats, tested_seat)
    previous_trace = os.environ.get("ORBIT_MODE_TRACE")
    previous_trace_all = os.environ.get("ORBIT_MODE_TRACE_ALL")
    start = time.perf_counter()
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            trace_path = Path(tmpdir) / "mode_trace.jsonl"
            os.environ["ORBIT_MODE_TRACE"] = str(trace_path)
            os.environ["ORBIT_MODE_TRACE_ALL"] = "1"
            env = make("orbit_wars", configuration={"seed": seed}, debug=True)
            env.run(agents)
            trace_rows = load_jsonl(trace_path)
    finally:
        if previous_trace is None:
            os.environ.pop("ORBIT_MODE_TRACE", None)
        else:
            os.environ["ORBIT_MODE_TRACE"] = previous_trace
        if previous_trace_all is None:
            os.environ.pop("ORBIT_MODE_TRACE_ALL", None)
        else:
            os.environ["ORBIT_MODE_TRACE_ALL"] = previous_trace_all

    elapsed_s = time.perf_counter() - start
    final_states = env.steps[-1]
    rewards = [get_value(state, "reward") for state in final_states]
    statuses = [normalize_status(get_value(state, "status")) for state in final_states]
    final_raw, final_raw_diff = raw_diff_from_final(final_board_observation(env), seats, tested_seat)

    obs_by_turn: dict[int, Any] = {}
    for turn, step in enumerate(env.steps):
        if tested_seat >= len(step):
            continue
        obs = get_value(step[tested_seat], "observation")
        if obs is not None and get_value(obs, "planets") is not None:
            obs_by_turn[turn] = obs

    turns = turn_rows_for_summary(obs_by_turn, seats, tested_seat)
    reward = rewards[tested_seat] if tested_seat < len(rewards) else None
    summary = {
        "seed": seed,
        "seats": seats,
        "tested_seat": tested_seat,
        "agents": agents,
        "tested_agent": agent,
        "opponents": opponents,
        "tested_reward": reward,
        "statuses": statuses,
        "tested_status": statuses[tested_seat] if tested_seat < len(statuses) else "UNKNOWN",
        "final_raw": final_raw,
        "final_raw_diff": final_raw_diff,
        "raw_zero_collapse": final_raw == 0,
        "failure_bucket": classify_failure(turns, final_raw_diff, reward),
        "first_prod_share_lt_40": first_turn(
            turns,
            lambda row: float(row["tested_production_share"]) < 0.40 and int(row["turn"]) >= 10,
        ),
        "turns": len(turns),
        "elapsed_s": round(elapsed_s, 4),
        "has_timeout_or_invalid": any(
            "TIMEOUT" in status.upper() or "INVALID" in status.upper() or "ERROR" in status.upper()
            for status in statuses
        ),
    }

    outcome_rows: list[dict[str, Any]] = []
    for row in trace_rows:
        if row.get("trace_error"):
            continue
        if row.get("mode_label") != "search-expand":
            continue
        if row.get("commit_allowed") is False:
            continue
        if row.get("player") is not None and int(row["player"]) != tested_seat:
            continue
        turn = int(row.get("step", 0))
        obs = obs_by_turn.get(turn)
        if obs is None:
            continue
        src_id = int(row["src"])
        target_id = int(row["target"])
        first_id = row.get("first_id")
        first_id = None if first_id is None else int(first_id)
        pressure = turn_pressure(obs, seats, tested_seat)
        residual_after = int(row.get("src_ships", 0)) - int(row.get("spent_plus_ships", 0))
        arrival_turn = turn + int(row.get("turns", 0))
        first_arrival_turn = turn + int(row.get("first_turns") or row.get("turns", 0))
        src_owner_at_launch = planet_owner(obs_by_turn, turn, src_id)
        target_owner_at_launch = planet_owner(obs_by_turn, turn, target_id)
        source_lost_10 = source_first_lost_turn(obs_by_turn, turn, 10, src_id, tested_seat)
        source_lost_20 = source_first_lost_turn(obs_by_turn, turn, 20, src_id, tested_seat)
        source_lost_30 = source_first_lost_turn(obs_by_turn, turn, 30, src_id, tested_seat)
        target_owner_arrival = planet_owner(obs_by_turn, arrival_turn, target_id)
        target_owner_arrival_10 = planet_owner(obs_by_turn, arrival_turn + 10, target_id)
        first_owner_arrival = None if first_id is None else planet_owner(obs_by_turn, first_arrival_turn, first_id)
        horizon_turn = min(max(obs_by_turn), turn + 20)
        source_owned_h20 = planet_owner(obs_by_turn, horizon_turn, src_id) == tested_seat
        outcome_rows.append({
            "seed": seed,
            "seats": seats,
            "tested_seat": tested_seat,
            "tested_reward": reward,
            "final_raw_diff": final_raw_diff,
            "failure_bucket": summary["failure_bucket"],
            "step": turn,
            "src": src_id,
            "target": target_id,
            "first_id": first_id,
            "ships": int(row.get("ships", 0)),
            "turns": int(row.get("turns", 0)),
            "src_ships": int(row.get("src_ships", 0)),
            "spent_before": int(row.get("spent_before", 0)),
            "spent_plus_ships": int(row.get("spent_plus_ships", 0)),
            "residual_after": residual_after,
            "src_owner_at_launch": src_owner_at_launch,
            "src_prod": planet_value(obs_by_turn, turn, src_id, PLANET_PRODUCTION),
            "src_ships_obs": planet_value(obs_by_turn, turn, src_id, PLANET_SHIPS),
            "source_owned_h20": source_owned_h20,
            "source_lost_turn_10": source_lost_10,
            "source_lost_turn_20": source_lost_20,
            "source_lost_turn_30": source_lost_30,
            "source_lost_within_20": source_lost_20 is not None,
            "source_ships_h20": planet_value(obs_by_turn, horizon_turn, src_id, PLANET_SHIPS) if source_owned_h20 else None,
            "target_owner_at_launch": target_owner_at_launch,
            "target_owner_trace": row.get("target_owner"),
            "target_prod": row.get("target_prod"),
            "target_owner_arrival": target_owner_arrival,
            "target_owner_arrival_10": target_owner_arrival_10,
            "target_captured_by_us_arrival": target_owner_arrival == tested_seat,
            "target_captured_by_us_arrival_10": target_owner_arrival_10 == tested_seat,
            "first_target_mismatch": bool(row.get("first_target_mismatch")),
            "first_owner_arrival": first_owner_arrival,
            "first_captured_by_us_arrival": first_owner_arrival == tested_seat,
            **pressure,
        })
    return summary, outcome_rows


def summarize(rows: list[dict[str, Any]]) -> None:
    print(f"rows={len(rows)} outcomes={dict(Counter('win' if (r.get('tested_reward') or 0) > 0 else 'loss' for r in rows))}")
    for out in ("win", "loss"):
        group = [row for row in rows if ("win" if (row.get("tested_reward") or 0) > 0 else "loss") == out]
        if not group:
            continue
        lost20 = [1 if row["source_lost_within_20"] else 0 for row in group]
        captured = [1 if row["target_captured_by_us_arrival_10"] else 0 for row in group]
        residuals = [int(row["residual_after"]) for row in group]
        print(
            f"{out}: n={len(group)} source_lost20={mean(lost20):.3f} "
            f"target_capture10={mean(captured):.3f} avg_residual={mean(residuals):.1f}"
        )
    buckets: Counter[tuple[Any, ...]] = Counter()
    for row in rows:
        out = "win" if (row.get("tested_reward") or 0) > 0 else "loss"
        residual_bucket = "res<8" if int(row["residual_after"]) < 8 else "res8+"
        prod_bucket = f"srcprod{row.get('src_prod')}"
        target_bucket = f"tgtprod{row.get('target_prod')}"
        buckets[(out, prod_bucket, residual_bucket, target_bucket, row["source_lost_within_20"], row["target_captured_by_us_arrival_10"])] += 1
    for key, count in buckets.most_common(30):
        print(count, key)


def main() -> None:
    parser = argparse.ArgumentParser(description="Analyze source/target outcomes for committed search-expand rows.")
    parser.add_argument("--agent", default="candidates\\loop_027b_loop021_mode_trace.py")
    parser.add_argument("--opponents", default="main.py")
    parser.add_argument("--seats", type=int, choices=[2, 4], default=2)
    parser.add_argument("--cases", type=parse_cases, required=True)
    parser.add_argument("--rows-out", required=True)
    parser.add_argument("--summary-out", required=True)
    args = parser.parse_args()

    opponents = split_csv(args.opponents)
    rows_path = Path(args.rows_out)
    summary_path = Path(args.summary_out)
    rows_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.parent.mkdir(parents=True, exist_ok=True)

    all_rows: list[dict[str, Any]] = []
    with rows_path.open("w", encoding="utf-8") as rows_fh, summary_path.open("w", encoding="utf-8") as summary_fh:
        for seed, tested_seat in args.cases:
            summary, rows = run_game_with_search_outcomes(
                seed=seed,
                agent=args.agent,
                opponents=opponents,
                seats=args.seats,
                tested_seat=tested_seat,
            )
            summary_fh.write(json.dumps(summary, ensure_ascii=False) + "\n")
            for row in rows:
                rows_fh.write(json.dumps(row, ensure_ascii=False) + "\n")
            rows_fh.flush()
            summary_fh.flush()
            all_rows.extend(rows)
            print(
                f"seed={seed} seat={tested_seat} reward={summary['tested_reward']} "
                f"raw_diff={summary['final_raw_diff']} bucket={summary['failure_bucket']} "
                f"search_rows={len(rows)} elapsed={summary['elapsed_s']:.3f}s"
            )
    summarize(all_rows)


if __name__ == "__main__":
    main()
