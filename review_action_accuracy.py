from __future__ import annotations

import argparse
import json
import math
import random
import time
from collections import Counter, defaultdict
from pathlib import Path
from statistics import mean
from typing import Any

from kaggle_environments import make


BOARD = 100.0
CENTER_X = 50.0
CENTER_Y = 50.0
SUN_R = 10.0
AUDIT_VERSION = "static-current-v2"

ID = 0
OWNER = 1
X = 2
Y = 3
RADIUS = 4
SHIPS = 5
PRODUCTION = 6
FLEET_OWNER = 1
FLEET_SHIPS = 6

HARD_INVALID = {
    "bad_shape",
    "missing_source",
    "not_owned_source",
    "invalid_ship_count",
}


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


def raw_score_from_observation(obs: Any, seats: int) -> list[int]:
    scores = [0 for _ in range(seats)]
    for planet in get_value(obs, "planets", []) or []:
        owner = int(planet[OWNER])
        if 0 <= owner < seats:
            scores[owner] += int(planet[SHIPS])
    for fleet in get_value(obs, "fleets", []) or []:
        owner = int(fleet[FLEET_OWNER])
        if 0 <= owner < seats:
            scores[owner] += int(fleet[FLEET_SHIPS])
    return scores


def final_board_observation(env: Any) -> Any:
    for step in reversed(env.steps):
        for state in step:
            obs = get_value(state, "observation")
            if obs is not None and get_value(obs, "planets") is not None:
                return obs
    raise RuntimeError("Could not find final observation with planets")


def angle_diff(a: float, b: float) -> float:
    return abs(math.atan2(math.sin(a - b), math.cos(a - b)))


def point_segment_distance(px, py, ax, ay, bx, by):
    dx = bx - ax
    dy = by - ay
    if dx == 0.0 and dy == 0.0:
        return math.hypot(px - ax, py - ay)
    t = ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy)
    t = max(0.0, min(1.0, t))
    return math.hypot(px - (ax + t * dx), py - (ay + t * dy))


def ray_segment_for_action(src, angle):
    sx = src[X] + math.cos(angle) * (src[RADIUS] + 0.1)
    sy = src[Y] + math.sin(angle) * (src[RADIUS] + 0.1)
    candidates = []
    c = math.cos(angle)
    s = math.sin(angle)
    if c > 1e-9:
        candidates.append((BOARD - sx) / c)
    elif c < -1e-9:
        candidates.append((0.0 - sx) / c)
    if s > 1e-9:
        candidates.append((BOARD - sy) / s)
    elif s < -1e-9:
        candidates.append((0.0 - sy) / s)
    travel = min(t for t in candidates if t > 0)
    return sx, sy, sx + c * travel, sy + s * travel


def first_static_collision(src, angle, planets):
    ax, ay, bx, by = ray_segment_for_action(src, angle)
    hits = []
    for p in planets:
        if p[ID] == src[ID]:
            continue
        d = point_segment_distance(p[X], p[Y], ax, ay, bx, by)
        if d < p[RADIUS]:
            along = (p[X] - ax) * math.cos(angle) + (p[Y] - ay) * math.sin(angle)
            if along > 0:
                hits.append((along, p))
    if not hits:
        return ("none", None, None)
    hits.sort(key=lambda item: item[0])
    return ("planet", hits[0][1], hits[0][0])


def path_to_target_hits_sun(src, angle, target):
    sx = src[X] + math.cos(angle) * (src[RADIUS] + 0.1)
    sy = src[Y] + math.sin(angle) * (src[RADIUS] + 0.1)
    along = (target[X] - sx) * math.cos(angle) + (target[Y] - sy) * math.sin(angle)
    travel = max(0.0, along - target[RADIUS])
    ex = sx + math.cos(angle) * travel
    ey = sy + math.sin(angle) * travel
    return point_segment_distance(CENTER_X, CENTER_Y, sx, sy, ex, ey) < SUN_R


def intended_by_angle(src, angle, planets):
    candidates = []
    for p in planets:
        if p[ID] == src[ID]:
            continue
        target_angle = math.atan2(p[Y] - src[Y], p[X] - src[X])
        diff = angle_diff(angle, target_angle)
        angular_radius = math.asin(
            min(0.95, p[RADIUS] / max(1.0, math.hypot(p[X] - src[X], p[Y] - src[Y])))
        )
        candidates.append((diff, angular_radius, p))
    if not candidates:
        return None
    candidates.sort(key=lambda item: item[0])
    return candidates[0]


def severity_for(kind: str) -> str:
    return "hard_invalid" if kind in HARD_INVALID else "static_suspicious"


def make_finding(
    *,
    seed: int,
    seats: int,
    tested_seat: int,
    step: int,
    move_index: int,
    kind: str,
    move: Any,
    src: Any = None,
    target: Any = None,
    first_hit: Any = None,
    detail: str = "",
) -> dict[str, Any]:
    angle = None
    ships = None
    src_id = None
    if isinstance(move, list) and len(move) == 3:
        src_id, angle, ships = move
    return {
        "audit_version": AUDIT_VERSION,
        "audit_model": "static_current_position_angle_guess",
        "seed": seed,
        "seats": seats,
        "tested_seat": tested_seat,
        "step": step,
        "move_index": move_index,
        "kind": kind,
        "severity": severity_for(kind),
        "src_id": None if src_id is None else int(src_id),
        "target_id_guess": None if target is None else int(target[ID]),
        "first_static_hit_id": None if first_hit is None else int(first_hit[ID]),
        "src_owner": None if src is None else int(src[OWNER]),
        "target_owner_guess": None if target is None else int(target[OWNER]),
        "first_hit_owner": None if first_hit is None else int(first_hit[OWNER]),
        "angle": None if angle is None else float(angle),
        "ships": None if ships is None else int(ships),
        "src_ships": None if src is None else int(src[SHIPS]),
        "target_ships_guess": None if target is None else int(target[SHIPS]),
        "target_prod_guess": None if target is None else int(target[PRODUCTION]),
        "detail": detail,
    }


def inspect_move(seed, seats, tested_seat, step_index, move_index, move, planets, player, used_by_src):
    findings = []
    by_id = {p[ID]: p for p in planets}
    if not isinstance(move, list) or len(move) != 3:
        return [
            make_finding(
                seed=seed, seats=seats, tested_seat=tested_seat, step=step_index,
                move_index=move_index, kind="bad_shape", move=move, detail=str(move)
            )
        ]

    src_id, angle, ships = move
    src = by_id.get(src_id)
    if src is None:
        return [
            make_finding(
                seed=seed, seats=seats, tested_seat=tested_seat, step=step_index,
                move_index=move_index, kind="missing_source", move=move, detail=str(move)
            )
        ]
    if src[OWNER] != player:
        return [
            make_finding(
                seed=seed, seats=seats, tested_seat=tested_seat, step=step_index,
                move_index=move_index, kind="not_owned_source", move=move, src=src, detail=str(move)
            )
        ]

    used_by_src[src_id] += int(ships)
    if ships <= 0 or used_by_src[src_id] > src[SHIPS]:
        return [
            make_finding(
                seed=seed, seats=seats, tested_seat=tested_seat, step=step_index,
                move_index=move_index, kind="invalid_ship_count", move=move, src=src,
                detail=f"used={used_by_src[src_id]} src_ships={src[SHIPS]}",
            )
        ]

    intended = intended_by_angle(src, float(angle), planets)
    hit_kind, hit_planet, _ = first_static_collision(src, float(angle), planets)
    if intended is None:
        return [
            make_finding(
                seed=seed, seats=seats, tested_seat=tested_seat, step=step_index,
                move_index=move_index, kind="no_target_candidate", move=move, src=src, detail=str(move)
            )
        ]

    diff, angular_radius, target = intended
    if diff > angular_radius * 1.35:
        findings.append(make_finding(
            seed=seed, seats=seats, tested_seat=tested_seat, step=step_index,
            move_index=move_index, kind="likely_miss_by_angle", move=move, src=src,
            target=target,
            detail=f"diff_deg={math.degrees(diff):.2f} radius_deg={math.degrees(angular_radius):.2f}",
        ))

    if path_to_target_hits_sun(src, float(angle), target):
        findings.append(make_finding(
            seed=seed, seats=seats, tested_seat=tested_seat, step=step_index,
            move_index=move_index, kind="static_path_hits_sun", move=move, src=src,
            target=target, detail=f"intended={target[ID]}",
        ))
    elif hit_kind == "none":
        findings.append(make_finding(
            seed=seed, seats=seats, tested_seat=tested_seat, step=step_index,
            move_index=move_index, kind="static_path_hits_nothing", move=move, src=src,
            target=target, detail=f"intended={target[ID]}",
        ))
    elif hit_planet and hit_planet[ID] != target[ID]:
        findings.append(make_finding(
            seed=seed, seats=seats, tested_seat=tested_seat, step=step_index,
            move_index=move_index, kind="static_path_hits_wrong_planet", move=move, src=src,
            target=target, first_hit=hit_planet,
            detail=f"intended={target[ID]} first_hit={hit_planet[ID]}",
        ))

    if target[OWNER] != player:
        required = int(target[SHIPS]) + 1
        if target[OWNER] != -1:
            required += max(2, int(target[PRODUCTION] * 2))
        if ships < required:
            findings.append(make_finding(
                seed=seed, seats=seats, tested_seat=tested_seat, step=step_index,
                move_index=move_index, kind="underpowered_launch", move=move, src=src,
                target=target,
                detail=f"target_ships={target[SHIPS]} prod={target[PRODUCTION]} required~={required}",
            ))
    return findings


def inspect_game(seed: int, agent: str, opponents: list[str], seats: int, tested_seat: int, turns: int):
    agents = build_agents(agent, opponents, seats, tested_seat)
    start = time.perf_counter()
    random.seed(seed)
    env = make("orbit_wars", configuration={"seed": seed}, debug=True)
    env.run(agents)
    elapsed_s = time.perf_counter() - start

    findings: list[dict[str, Any]] = []
    audited_steps = min(turns, len(env.steps))
    for step_index, step in enumerate(env.steps[:audited_steps]):
        agent_state = step[tested_seat]
        action = get_value(agent_state, "action") or []
        obs_state = env.steps[step_index - 1][tested_seat] if step_index > 0 else agent_state
        obs = get_value(obs_state, "observation")
        planets = get_value(obs, "planets", []) or []
        player = get_value(obs, "player", tested_seat)
        used_by_src = defaultdict(int)
        for move_index, move in enumerate(action):
            findings.extend(
                inspect_move(seed, seats, tested_seat, step_index, move_index, move, planets, player, used_by_src)
            )

    final_states = env.steps[-1]
    rewards = [get_value(state, "reward") for state in final_states]
    statuses = [normalize_status(get_value(state, "status")) for state in final_states]
    raw_scores = raw_score_from_observation(final_board_observation(env), seats)
    tested_raw = raw_scores[tested_seat]
    max_opp_raw = max(score for seat, score in enumerate(raw_scores) if seat != tested_seat)
    raw_rank = 1 + sum(score > tested_raw for score in raw_scores)
    finding_counts = Counter(item["kind"] for item in findings)
    hard_counts = Counter(item["kind"] for item in findings if item["severity"] == "hard_invalid")
    suspicious_counts = Counter(item["kind"] for item in findings if item["severity"] == "static_suspicious")

    summary = {
        "audit_version": AUDIT_VERSION,
        "audit_model": "static_current_position_angle_guess",
        "audit_limitations": [
            "target is guessed from current angle, not the agent's internal target_id",
            "first collision is static/current-position geometry, not full moving physics",
            "underpowered estimate ignores ETA production, same-turn combat, and incoming fleets",
        ],
        "seed": seed,
        "map_random_seed": seed,
        "seats": seats,
        "tested_seat": tested_seat,
        "tested_agent": agent,
        "opponents": opponents,
        "agents": agents,
        "turns_audited": audited_steps,
        "rewards": rewards,
        "tested_reward": rewards[tested_seat] if tested_seat < len(rewards) else None,
        "statuses": statuses,
        "tested_status": statuses[tested_seat] if tested_seat < len(statuses) else "UNKNOWN",
        "raw_scores": raw_scores,
        "tested_raw_score": tested_raw,
        "raw_score_diff": tested_raw - max_opp_raw,
        "raw_rank": raw_rank,
        "elapsed_s": round(elapsed_s, 4),
        "finding_counts": dict(finding_counts),
        "hard_error_counts": dict(hard_counts),
        "suspicious_counts": dict(suspicious_counts),
        "has_timeout_or_invalid": any(
            "TIMEOUT" in status.upper() or "INVALID" in status.upper() or "ERROR" in status.upper()
            for status in statuses
        ),
    }
    return summary, findings


def summarize(summaries: list[dict[str, Any]]) -> None:
    by_key: dict[tuple[str, int, int], list[dict[str, Any]]] = defaultdict(list)
    for row in summaries:
        by_key[(row["tested_agent"], row["seats"], row["tested_seat"])].append(row)
    for (agent, seats, tested_seat), rows in sorted(by_key.items()):
        rewards = [0 if row["tested_reward"] is None else row["tested_reward"] for row in rows]
        raw = [row["raw_score_diff"] for row in rows]
        bad = sum(1 for row in rows if row["has_timeout_or_invalid"])
        total_counts = Counter()
        hard_counts = Counter()
        suspicious_counts = Counter()
        for row in rows:
            total_counts.update(row["finding_counts"])
            hard_counts.update(row["hard_error_counts"])
            suspicious_counts.update(row["suspicious_counts"])
        print(
            f"{agent} seats={seats} tested_seat={tested_seat} games={len(rows)} "
            f"avg_reward={mean(rewards):.3f} avg_raw_diff={mean(raw):.1f} bad={bad} "
            f"hard={dict(hard_counts)} suspicious={dict(suspicious_counts)}"
        )


def default_opponents(mode: str) -> list[str]:
    return ["random"] if mode == "2p" else ["random", "starter", "random"]


def main() -> None:
    parser = argparse.ArgumentParser(description="Static action-audit runner for Orbit Wars agents.")
    parser.add_argument("variants", nargs="*", help="Backward-compatible agent paths when --agent is omitted.")
    parser.add_argument("--agent", default=None)
    parser.add_argument("--opponents", default=None)
    parser.add_argument("--opponent", default=None)
    parser.add_argument("--games", type=int, default=3)
    parser.add_argument("--turns", type=int, default=35)
    parser.add_argument("--mode", choices=["2p", "4p"], default="4p")
    parser.add_argument("--seats", type=int, choices=[2, 4], default=None)
    parser.add_argument("--seed-start", type=int, default=0)
    parser.add_argument("--agent-slot", "--tested-seat", dest="agent_slot", type=int, default=0)
    parser.add_argument("--rotate-seats", action="store_true")
    parser.add_argument("--out", default=None, help="Optional game-level JSONL output.")
    parser.add_argument("--findings-out", default=None, help="Optional finding-level JSONL output.")
    parser.add_argument("--print-findings", type=int, default=25)
    args = parser.parse_args()

    agents_to_test = [args.agent] if args.agent else args.variants
    if not agents_to_test:
        raise SystemExit("Provide --agent or at least one positional variant.")

    seats = args.seats if args.seats is not None else (2 if args.mode == "2p" else 4)
    opponent_spec = args.opponent if args.opponent is not None else args.opponents
    opponents = split_csv(opponent_spec) if opponent_spec else default_opponents(args.mode)

    out_handle = None
    findings_handle = None
    if args.out:
        out_path = Path(args.out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_handle = out_path.open("w", encoding="utf-8")
    if args.findings_out:
        findings_path = Path(args.findings_out)
        findings_path.parent.mkdir(parents=True, exist_ok=True)
        findings_handle = findings_path.open("w", encoding="utf-8")

    summaries: list[dict[str, Any]] = []
    printed = 0
    try:
        for agent in agents_to_test:
            tested_seats = range(seats) if args.rotate_seats else [args.agent_slot]
            for tested_seat in tested_seats:
                if tested_seat < 0 or tested_seat >= seats:
                    raise ValueError(f"tested seat {tested_seat} is outside seats={seats}")
                for offset in range(args.games):
                    seed = args.seed_start + offset
                    summary, findings = inspect_game(seed, agent, opponents, seats, tested_seat, args.turns)
                    summaries.append(summary)
                    if out_handle is not None:
                        out_handle.write(json.dumps(summary, ensure_ascii=False) + "\n")
                        out_handle.flush()
                    if findings_handle is not None:
                        for finding in findings:
                            findings_handle.write(json.dumps(finding, ensure_ascii=False) + "\n")
                        findings_handle.flush()
                    print(
                        f"seed={seed} seats={seats} tested_seat={tested_seat} "
                        f"reward={summary['tested_reward']} raw_diff={summary['raw_score_diff']} "
                        f"findings={summary['finding_counts']}"
                    )
                    for finding in findings:
                        if printed >= args.print_findings:
                            break
                        print(
                            f"  seed={seed} step={finding['step']} move={finding['move_index']} "
                            f"{finding['kind']}: {finding['detail']}"
                        )
                        printed += 1
    finally:
        if out_handle is not None:
            out_handle.close()
        if findings_handle is not None:
            findings_handle.close()

    summarize(summaries)


if __name__ == "__main__":
    main()
