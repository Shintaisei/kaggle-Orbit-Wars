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


def parse_seats(value: str) -> list[int]:
    seats = [int(part) for part in split_csv(value)]
    bad = [seat for seat in seats if seat not in (2, 4)]
    if bad:
        raise argparse.ArgumentTypeError(f"--seats supports only 2 or 4, got {bad}")
    return seats


def raw_score_from_observation(obs: Any, num_players: int) -> list[int]:
    scores = [0 for _ in range(num_players)]
    planets = get_value(obs, "planets", []) or []
    fleets = get_value(obs, "fleets", []) or []

    for planet in planets:
        owner = int(planet[PLANET_OWNER])
        if 0 <= owner < num_players:
            scores[owner] += int(planet[PLANET_SHIPS])

    for fleet in fleets:
        owner = int(fleet[FLEET_OWNER])
        if 0 <= owner < num_players:
            scores[owner] += int(fleet[FLEET_SHIPS])

    return scores


def final_board_observation(env: Any) -> Any:
    for step in reversed(env.steps):
        for state in step:
            obs = get_value(state, "observation")
            if obs is not None and get_value(obs, "planets") is not None:
                return obs
    raise RuntimeError("Could not find a final observation with planets")


def build_agents(agent: str, opponents: list[str], seats: int, tested_seat: int) -> list[str]:
    if seats < 2:
        raise ValueError("seats must be at least 2")
    if not opponents:
        opponents = ["random"]

    agents: list[str] = []
    opponent_index = 0
    for seat in range(seats):
        if seat == tested_seat:
            agents.append(agent)
        else:
            agents.append(opponents[opponent_index % len(opponents)])
            opponent_index += 1
    return agents


def run_game(seed: int, agent: str, opponents: list[str], seats: int, tested_seat: int) -> dict[str, Any]:
    agents = build_agents(agent, opponents, seats, tested_seat)
    start = time.perf_counter()
    random.seed(seed)
    env = make("orbit_wars", configuration={"seed": seed}, debug=True)
    env.run(agents)
    elapsed_s = time.perf_counter() - start

    final_states = env.steps[-1]
    rewards = [get_value(state, "reward") for state in final_states]
    statuses = [normalize_status(get_value(state, "status")) for state in final_states]
    raw_scores = raw_score_from_observation(final_board_observation(env), seats)

    tested_raw = raw_scores[tested_seat]
    opponent_raws = [score for seat, score in enumerate(raw_scores) if seat != tested_seat]
    max_opp_raw = max(opponent_raws) if opponent_raws else 0
    top_raw = max(raw_scores) if raw_scores else 0
    raw_rank = 1 + sum(score > tested_raw for score in raw_scores)

    return {
        "seed": seed,
        "map_random_seed": seed,
        "seats": seats,
        "tested_seat": tested_seat,
        "agents": agents,
        "tested_agent": agent,
        "opponents": opponents,
        "rewards": rewards,
        "tested_reward": rewards[tested_seat] if tested_seat < len(rewards) else None,
        "statuses": statuses,
        "tested_status": statuses[tested_seat] if tested_seat < len(statuses) else "UNKNOWN",
        "raw_scores": raw_scores,
        "tested_raw_score": tested_raw,
        "raw_score_diff": tested_raw - max_opp_raw,
        "raw_rank": raw_rank,
        "raw_tied_for_first": tested_raw == top_raw,
        "winner_seats_by_raw": [seat for seat, score in enumerate(raw_scores) if score == top_raw],
        "steps": len(env.steps),
        "elapsed_s": round(elapsed_s, 4),
        "has_timeout_or_invalid": any(
            "TIMEOUT" in status.upper() or "INVALID" in status.upper() or "ERROR" in status.upper()
            for status in statuses
        ),
    }


def summarize(records: list[dict[str, Any]]) -> None:
    if not records:
        print("No games were run.")
        return

    by_key: dict[tuple[int, int], list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        by_key[(record["seats"], record["tested_seat"])].append(record)

    print("\n== Aggregate")
    for (seats, tested_seat), group in sorted(by_key.items()):
        rewards = [0 if item["tested_reward"] is None else item["tested_reward"] for item in group]
        raw_diffs = [item["raw_score_diff"] for item in group]
        firsts = [1 if item["raw_tied_for_first"] else 0 for item in group]
        bad = [1 if item["has_timeout_or_invalid"] else 0 for item in group]
        status_counts = Counter(item["tested_status"] for item in group)
        print(
            f"seats={seats} tested_seat={tested_seat} "
            f"games={len(group)} avg_reward={mean(rewards):.3f} "
            f"avg_raw_diff={mean(raw_diffs):.2f} raw_first_rate={mean(firsts):.3f} "
            f"bad_games={sum(bad)} statuses={dict(status_counts)}"
        )


def main() -> None:
    parser = argparse.ArgumentParser(description="Local Orbit Wars evaluator with raw-score JSONL output.")
    parser.add_argument("--agent", default="main.py", help="Agent file/name to evaluate.")
    parser.add_argument("--opponents", default="random", help="Comma-separated opponent files/names.")
    parser.add_argument("--opponent", default=None, help="Backward-compatible single opponent alias.")
    parser.add_argument("--games", type=int, default=5)
    parser.add_argument("--seats", type=parse_seats, default=[2], help="2, 4, or comma-separated list such as 2,4.")
    parser.add_argument("--seed-start", type=int, default=0)
    parser.add_argument("--agent-slot", type=int, default=0, help="Tested seat when --rotate-seats is not used.")
    parser.add_argument("--rotate-seats", action="store_true", help="Run the tested agent in every seat.")
    parser.add_argument("--out", default=None, help="Optional JSONL output path.")
    args = parser.parse_args()

    opponent_spec = args.opponent if args.opponent is not None else args.opponents
    opponents = split_csv(opponent_spec)

    out_handle = None
    if args.out:
        out_path = Path(args.out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_handle = out_path.open("w", encoding="utf-8")

    records: list[dict[str, Any]] = []
    try:
        for seats in args.seats:
            tested_seats = range(seats) if args.rotate_seats else [args.agent_slot]
            for tested_seat in tested_seats:
                if tested_seat < 0 or tested_seat >= seats:
                    raise ValueError(f"--agent-slot {tested_seat} is outside seats={seats}")
                for offset in range(args.games):
                    seed = args.seed_start + offset
                    record = run_game(seed, args.agent, opponents, seats, tested_seat)
                    records.append(record)
                    if out_handle is not None:
                        out_handle.write(json.dumps(record, ensure_ascii=False) + "\n")
                        out_handle.flush()
                    print(
                        f"seed={seed} seats={seats} tested_seat={tested_seat} "
                        f"reward={record['tested_reward']} raw={record['tested_raw_score']} "
                        f"raw_diff={record['raw_score_diff']} rank={record['raw_rank']} "
                        f"status={record['tested_status']} elapsed={record['elapsed_s']:.3f}s "
                        f"bad={record['has_timeout_or_invalid']}"
                    )
    finally:
        if out_handle is not None:
            out_handle.close()

    summarize(records)


if __name__ == "__main__":
    main()
