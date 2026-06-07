from __future__ import annotations

import argparse
import json
import random
import time
from collections import Counter, defaultdict
from pathlib import Path
from statistics import mean
from typing import Any

from kaggle_environments import make


PLANET_OWNER = 1
PLANET_SHIPS = 5
PLANET_PRODUCTION = 6
FLEET_OWNER = 1
FLEET_SHIPS = 6


def get_value(obj: Any, key: str, default: Any = None) -> Any:
    if isinstance(obj, dict):
        return obj.get(key, default)
    return getattr(obj, key, default)


def normalize_status(status: Any) -> str:
    if status is None:
        return "UNKNOWN"
    return getattr(status, "name", str(status))


def split_csv(value: str) -> list[str]:
    return [part.strip() for part in value.split(",") if part.strip()]


def build_agents(agent: str, opponents: list[str], seats: int, tested_seat: int) -> list[str]:
    agents: list[str] = []
    opponent_index = 0
    for seat in range(seats):
        if seat == tested_seat:
            agents.append(agent)
        else:
            agents.append(opponents[opponent_index % len(opponents)])
            opponent_index += 1
    return agents


def final_board_observation(env: Any) -> Any:
    for step in reversed(env.steps):
        for state in step:
            obs = get_value(state, "observation")
            if obs is not None and get_value(obs, "planets") is not None:
                return obs
    raise RuntimeError("Could not find final observation")


def seat_metrics(obs: Any, seats: int) -> list[dict[str, float | int]]:
    planets = get_value(obs, "planets", []) or []
    fleets = get_value(obs, "fleets", []) or []
    metrics: list[dict[str, float | int]] = [
        {
            "owned_planets": 0,
            "production": 0,
            "planet_ships": 0,
            "fleet_ships": 0,
            "active_fleets": 0,
            "total_raw": 0,
        }
        for _ in range(seats)
    ]
    for planet in planets:
        owner = int(planet[PLANET_OWNER])
        if 0 <= owner < seats:
            m = metrics[owner]
            m["owned_planets"] += 1
            m["production"] += int(planet[PLANET_PRODUCTION])
            m["planet_ships"] += int(planet[PLANET_SHIPS])
    for fleet in fleets:
        owner = int(fleet[FLEET_OWNER])
        if 0 <= owner < seats:
            m = metrics[owner]
            m["fleet_ships"] += int(fleet[FLEET_SHIPS])
            m["active_fleets"] += 1
    for m in metrics:
        m["total_raw"] = int(m["planet_ships"]) + int(m["fleet_ships"])
    total_prod = sum(int(m["production"]) for m in metrics)
    total_raw = sum(int(m["total_raw"]) for m in metrics)
    for m in metrics:
        m["production_share"] = (float(m["production"]) / total_prod) if total_prod else 0.0
        m["raw_share"] = (float(m["total_raw"]) / total_raw) if total_raw else 0.0
        m["fleet_raw_ratio"] = (float(m["fleet_ships"]) / float(m["total_raw"])) if int(m["total_raw"]) else 0.0
    return metrics


def action_metrics(action: Any) -> dict[str, int]:
    if not isinstance(action, list):
        return {"launches": 0, "launched_ships": 0}
    launches = 0
    ships = 0
    for move in action:
        if isinstance(move, list) and len(move) == 3:
            launches += 1
            try:
                ships += int(move[2])
            except Exception:
                pass
    return {"launches": launches, "launched_ships": ships}


def classify_failure(turns: list[dict[str, Any]], final_raw_diff: int, reward: Any) -> str:
    if reward is not None and reward > 0:
        return "win"
    if not turns:
        return "no-turn-data"
    t25 = next((row for row in turns if row["turn"] >= 25), turns[-1])
    t40 = next((row for row in turns if row["turn"] >= 40), turns[-1])
    if int(t40["tested_production"]) + 5 < int(t40["max_opp_production"]):
        return "early-expansion-lag"
    overcommit = any(
        float(row["tested_fleet_raw_ratio"]) >= 0.45
        and int(row["tested_planet_ships"]) < int(row["max_opp_planet_ships"]) * 0.70
        for row in turns[:160]
    )
    if overcommit:
        return "overcommit-collapse"
    if int(t25["tested_production"]) >= int(t25["max_opp_production"]) and final_raw_diff < 0:
        return "midgame-defense-drain"
    if any(int(row["tested_launched_ships"]) >= max(25, int(row["tested_total_raw"]) * 0.30) for row in turns):
        return "failed-all-in"
    return "late-collapse"


def first_turn(turns: list[dict[str, Any]], predicate) -> int | None:
    for row in turns:
        if predicate(row):
            return int(row["turn"])
    return None


def run_game(seed: int, agent: str, opponents: list[str], seats: int, tested_seat: int) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    agents = build_agents(agent, opponents, seats, tested_seat)
    start = time.perf_counter()
    random.seed(seed)
    env = make("orbit_wars", configuration={"seed": seed}, debug=True)
    env.run(agents)
    elapsed_s = time.perf_counter() - start

    final_states = env.steps[-1]
    rewards = [get_value(state, "reward") for state in final_states]
    statuses = [normalize_status(get_value(state, "status")) for state in final_states]
    final_metrics = seat_metrics(final_board_observation(env), seats)
    tested_final = final_metrics[tested_seat]
    max_opp_final = max(
        (m for idx, m in enumerate(final_metrics) if idx != tested_seat),
        key=lambda m: int(m["total_raw"]),
    )
    raw_diff = int(tested_final["total_raw"]) - int(max_opp_final["total_raw"])

    rows: list[dict[str, Any]] = []
    prev_row: dict[str, Any] | None = None
    for turn, step in enumerate(env.steps):
        if tested_seat >= len(step):
            continue
        state = step[tested_seat]
        obs = get_value(state, "observation")
        if obs is None or get_value(obs, "planets") is None:
            continue
        metrics = seat_metrics(obs, seats)
        tested = metrics[tested_seat]
        opp_items = [(idx, m) for idx, m in enumerate(metrics) if idx != tested_seat]
        max_opp_seat, max_opp = max(opp_items, key=lambda item: int(item[1]["total_raw"]))
        action = action_metrics(get_value(state, "action"))
        row = {
            "seed": seed,
            "seats": seats,
            "tested_seat": tested_seat,
            "turn": turn,
            "max_opp_seat": max_opp_seat,
            "tested_owned_planets": int(tested["owned_planets"]),
            "tested_production": int(tested["production"]),
            "tested_planet_ships": int(tested["planet_ships"]),
            "tested_fleet_ships": int(tested["fleet_ships"]),
            "tested_active_fleets": int(tested["active_fleets"]),
            "tested_total_raw": int(tested["total_raw"]),
            "tested_production_share": round(float(tested["production_share"]), 4),
            "tested_raw_share": round(float(tested["raw_share"]), 4),
            "tested_fleet_raw_ratio": round(float(tested["fleet_raw_ratio"]), 4),
            "max_opp_owned_planets": int(max_opp["owned_planets"]),
            "max_opp_production": int(max_opp["production"]),
            "max_opp_planet_ships": int(max_opp["planet_ships"]),
            "max_opp_fleet_ships": int(max_opp["fleet_ships"]),
            "max_opp_active_fleets": int(max_opp["active_fleets"]),
            "max_opp_total_raw": int(max_opp["total_raw"]),
            "raw_diff": int(tested["total_raw"]) - int(max_opp["total_raw"]),
            "production_diff": int(tested["production"]) - int(max_opp["production"]),
            "tested_launches": int(action["launches"]),
            "tested_launched_ships": int(action["launched_ships"]),
        }
        if prev_row is not None:
            for key in ("tested_owned_planets", "tested_production", "tested_total_raw", "raw_diff"):
                row[f"delta_{key}"] = row[key] - prev_row[key]
        else:
            for key in ("tested_owned_planets", "tested_production", "tested_total_raw", "raw_diff"):
                row[f"delta_{key}"] = 0
        rows.append(row)
        prev_row = row

    reward = rewards[tested_seat] if tested_seat < len(rewards) else None
    summary = {
        "seed": seed,
        "map_random_seed": seed,
        "seats": seats,
        "tested_seat": tested_seat,
        "agents": agents,
        "tested_agent": agent,
        "opponents": opponents,
        "tested_reward": reward,
        "statuses": statuses,
        "tested_status": statuses[tested_seat] if tested_seat < len(statuses) else "UNKNOWN",
        "final_raw": int(tested_final["total_raw"]),
        "final_raw_diff": raw_diff,
        "final_rank": 1 + sum(int(m["total_raw"]) > int(tested_final["total_raw"]) for m in final_metrics),
        "raw_zero_collapse": int(tested_final["total_raw"]) == 0,
        "failure_bucket": classify_failure(rows, raw_diff, reward),
        "first_raw_diff_lt_minus_500": first_turn(rows, lambda r: int(r["raw_diff"]) < -500),
        "first_raw_diff_lt_minus_1000": first_turn(rows, lambda r: int(r["raw_diff"]) < -1000),
        "first_prod_share_lt_40": first_turn(rows, lambda r: float(r["tested_production_share"]) < 0.40 and int(r["turn"]) >= 10),
        "first_zero_owned_planets": first_turn(rows, lambda r: int(r["tested_owned_planets"]) == 0),
        "first_zero_production": first_turn(rows, lambda r: int(r["tested_production"]) == 0 and int(r["turn"]) >= 10),
        "first_large_launch": first_turn(rows, lambda r: int(r["tested_launched_ships"]) >= max(25, int(r["tested_total_raw"]) * 0.30)),
        "turns": len(rows),
        "elapsed_s": round(elapsed_s, 4),
        "has_timeout_or_invalid": any(
            "TIMEOUT" in status.upper() or "INVALID" in status.upper() or "ERROR" in status.upper()
            for status in statuses
        ),
    }
    return summary, rows


def summarize(summaries: list[dict[str, Any]]) -> None:
    if not summaries:
        print("No games were run.")
        return
    print("\n== Aggregate")
    by_bucket = Counter(row["failure_bucket"] for row in summaries)
    print(f"failure_buckets={dict(by_bucket)}")
    by_seat: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for row in summaries:
        by_seat[int(row["tested_seat"])].append(row)
    for seat, rows in sorted(by_seat.items()):
        wins = sum(1 for row in rows if (row["tested_reward"] or 0) > 0)
        avg_raw = mean(int(row["final_raw_diff"]) for row in rows)
        raw_zero = sum(1 for row in rows if row["raw_zero_collapse"])
        print(f"seat={seat} wins={wins}/{len(rows)} avg_raw_diff={avg_raw:.1f} raw_zero={raw_zero}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Orbit Wars turn-by-turn metric analyzer.")
    parser.add_argument("--agent", default="main.py")
    parser.add_argument("--opponents", default="main.py")
    parser.add_argument("--games", type=int, default=5)
    parser.add_argument("--seats", type=int, choices=[2, 4], default=2)
    parser.add_argument("--seed-start", type=int, default=0)
    parser.add_argument("--agent-slot", type=int, default=0)
    parser.add_argument("--rotate-seats", action="store_true")
    parser.add_argument("--summary-out", required=True)
    parser.add_argument("--turns-out", required=True)
    args = parser.parse_args()

    opponents = split_csv(args.opponents)
    summary_path = Path(args.summary_out)
    turns_path = Path(args.turns_out)
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    turns_path.parent.mkdir(parents=True, exist_ok=True)

    summaries: list[dict[str, Any]] = []
    with summary_path.open("w", encoding="utf-8") as summary_fh, turns_path.open("w", encoding="utf-8") as turns_fh:
        tested_seats = range(args.seats) if args.rotate_seats else [args.agent_slot]
        for tested_seat in tested_seats:
            for offset in range(args.games):
                seed = args.seed_start + offset
                summary, turns = run_game(seed, args.agent, opponents, args.seats, tested_seat)
                summaries.append(summary)
                summary_fh.write(json.dumps(summary, ensure_ascii=False) + "\n")
                for row in turns:
                    turns_fh.write(json.dumps(row, ensure_ascii=False) + "\n")
                summary_fh.flush()
                turns_fh.flush()
                print(
                    f"seed={seed} seat={tested_seat} reward={summary['tested_reward']} "
                    f"raw_diff={summary['final_raw_diff']} bucket={summary['failure_bucket']} "
                    f"raw0={summary['raw_zero_collapse']} elapsed={summary['elapsed_s']:.3f}s"
                )
    summarize(summaries)


if __name__ == "__main__":
    main()
