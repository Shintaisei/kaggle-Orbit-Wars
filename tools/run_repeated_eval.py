from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from collections import Counter, defaultdict
from pathlib import Path
from statistics import mean, pstdev
from typing import Any


ROOT = Path(__file__).resolve().parents[1]


def split_csv(value: str) -> list[str]:
    return [part.strip() for part in value.split(",") if part.strip()]


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def sha256_path(path_text: str) -> str | None:
    path = (ROOT / path_text).resolve()
    if not path.exists() or not path.is_file():
        return None
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def apply_hash_seed(env: dict[str, str], hash_seed: str) -> str:
    if hash_seed.lower() == "unset":
        env.pop("PYTHONHASHSEED", None)
        return "unset"
    env["PYTHONHASHSEED"] = hash_seed
    return hash_seed


def run_test_local(args: argparse.Namespace, repeat: int, hash_seed: str, games: int, seed_start: int, agent_slot: int | None) -> list[dict[str, Any]]:
    with tempfile.TemporaryDirectory() as tmpdir:
        out_path = Path(tmpdir) / "eval.jsonl"
        cmd = [
            sys.executable,
            str(ROOT / "test_local.py"),
            "--agent",
            args.agent,
            "--opponents",
            args.opponents,
            "--games",
            str(games),
            "--seats",
            args.seats,
            "--seed-start",
            str(seed_start),
            "--out",
            str(out_path),
        ]
        if agent_slot is None:
            cmd.append("--rotate-seats")
        else:
            cmd.extend(["--agent-slot", str(agent_slot)])

        env = os.environ.copy()
        effective_hash_seed = apply_hash_seed(env, hash_seed)
        started_at = datetime.now(timezone.utc).isoformat()
        result = subprocess.run(
            cmd,
            cwd=str(ROOT),
            env=env,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            check=False,
        )
        ended_at = datetime.now(timezone.utc).isoformat()
        if result.returncode != 0:
            raise RuntimeError(
                f"repeat={repeat} hash_seed={hash_seed} failed with code {result.returncode}\n"
                f"{result.stdout[-4000:]}"
            )
        rows = read_jsonl(out_path)
        for row in rows:
            row["repeat"] = repeat
            row["process_mode"] = args.process_mode
            row["python_hash_seed"] = effective_hash_seed
            row["exit_code"] = result.returncode
            row["command"] = cmd
            row["cwd"] = str(ROOT)
            row["python_executable"] = sys.executable
            row["started_at"] = started_at
            row["ended_at"] = ended_at
            row["agent_sha256"] = sha256_path(args.agent)
            row["test_local_sha256"] = sha256_path("test_local.py")
            row["opponent_sha256"] = {
                opponent: sha256_path(opponent) for opponent in split_csv(args.opponents)
            }
        return rows


def run_once(args: argparse.Namespace, repeat: int, hash_seed: str) -> list[dict[str, Any]]:
    if args.process_mode == "batch":
        return run_test_local(
            args,
            repeat,
            hash_seed,
            games=args.games,
            seed_start=args.seed_start,
            agent_slot=None if args.rotate_seats else args.agent_slot,
        )

    rows: list[dict[str, Any]] = []
    seats = [int(part) for part in split_csv(args.seats)]
    for seats_value in seats:
        tested_seats = range(seats_value) if args.rotate_seats else [args.agent_slot]
        for tested_seat in tested_seats:
            for offset in range(args.games):
                single_args = argparse.Namespace(**vars(args))
                single_args.seats = str(seats_value)
                rows.extend(
                    run_test_local(
                        single_args,
                        repeat,
                        hash_seed,
                        games=1,
                        seed_start=args.seed_start + offset,
                        agent_slot=tested_seat,
                    )
                )
    return rows


def summarize(rows: list[dict[str, Any]]) -> None:
    by_key: dict[tuple[int, str, str, int], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        by_key[(
            int(row["repeat"]),
            str(row["python_hash_seed"]),
            str(row.get("process_mode", "batch")),
            int(row["tested_seat"]),
        )].append(row)

    print("# Per Repeat")
    for (repeat, hash_seed, process_mode, seat), group in sorted(by_key.items()):
        wins = sum(1 for row in group if row.get("tested_reward") == 1)
        raw_values = [float(row.get("raw_score_diff", 0)) for row in group]
        raw = mean(raw_values)
        raw_std = pstdev(raw_values) if len(raw_values) > 1 else 0.0
        raw_zero_losses = sum(1 for row in group if row.get("tested_reward") != 1 and row.get("tested_raw_score") == 0)
        bad = sum(1 for row in group if row.get("has_timeout_or_invalid"))
        print(
            f"repeat={repeat} hash_seed={hash_seed} mode={process_mode} seat={seat} "
            f"wins={wins}/{len(group)} avg_raw={raw:.1f} std_raw={raw_std:.1f} "
            f"raw_zero_losses={raw_zero_losses} bad={bad}"
        )

    print("\n# Combined")
    by_seat: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        by_seat[int(row["tested_seat"])].append(row)
    for seat, group in sorted(by_seat.items()):
        wins = sum(1 for row in group if row.get("tested_reward") == 1)
        raw_values = [float(row.get("raw_score_diff", 0)) for row in group]
        raw = mean(raw_values)
        raw_std = pstdev(raw_values) if len(raw_values) > 1 else 0.0
        raw_zero_losses = sum(1 for row in group if row.get("tested_reward") != 1 and row.get("tested_raw_score") == 0)
        bad = sum(1 for row in group if row.get("has_timeout_or_invalid"))
        status_counts = Counter(row.get("tested_status") for row in group)
        print(
            f"seat={seat} wins={wins}/{len(group)} avg_raw={raw:.1f} std_raw={raw_std:.1f} "
            f"raw_zero_losses={raw_zero_losses} bad={bad} statuses={dict(status_counts)}"
        )

    print("\n# Flip Check")
    by_case: dict[tuple[int, int], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        by_case[(int(row["seed"]), int(row["tested_seat"]))].append(row)
    flip_count = 0
    for (seed, seat), group in sorted(by_case.items()):
        outcomes = Counter(row.get("tested_reward") for row in group)
        raw_signs = Counter(
            1 if float(row.get("raw_score_diff", 0)) > 0 else -1 if float(row.get("raw_score_diff", 0)) < 0 else 0
            for row in group
        )
        if len(outcomes) > 1 or len(raw_signs) > 1:
            flip_count += 1
            print(f"seed={seed} seat={seat} outcomes={dict(outcomes)} raw_signs={dict(raw_signs)}")
    print(f"flip_count_by_seed_seat={flip_count}/{len(by_case)}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run test_local.py repeatedly in fresh Python processes.")
    parser.add_argument("--agent", required=True)
    parser.add_argument("--opponents", default="main.py")
    parser.add_argument("--games", type=int, default=10)
    parser.add_argument("--seats", default="2")
    parser.add_argument("--seed-start", type=int, default=200)
    parser.add_argument("--agent-slot", type=int, default=0)
    parser.add_argument("--rotate-seats", action="store_true")
    parser.add_argument("--hash-seeds", default="0,1,2")
    parser.add_argument("--process-mode", choices=["batch", "per-game"], default="batch")
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    all_rows: list[dict[str, Any]] = []
    hash_seeds = split_csv(args.hash_seeds)
    for repeat, hash_seed in enumerate(hash_seeds):
        rows = run_once(args, repeat, hash_seed)
        all_rows.extend(rows)
        with out_path.open("w", encoding="utf-8") as fh:
            for row in all_rows:
                fh.write(json.dumps(row, ensure_ascii=False) + "\n")
        print(f"completed repeat={repeat} hash_seed={hash_seed} rows={len(rows)}")
    summarize(all_rows)


if __name__ == "__main__":
    main()
