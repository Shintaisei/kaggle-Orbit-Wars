from __future__ import annotations

import argparse
import json
import os
import tempfile
from pathlib import Path
from typing import Any

from analyze_turn_metrics import run_game, split_csv


def parse_cases(value: str) -> list[tuple[int, int]]:
    cases: list[tuple[int, int]] = []
    for part in split_csv(value):
        try:
            seed_text, seat_text = part.split(":", 1)
            cases.append((int(seed_text), int(seat_text)))
        except ValueError as exc:
            raise argparse.ArgumentTypeError(
                f"case must be seed:seat, got {part!r}"
            ) from exc
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


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run selected Orbit Wars games with ORBIT_MODE_TRACE and annotate trace rows by seed/seat."
    )
    parser.add_argument("--agent", required=True)
    parser.add_argument("--opponents", default="main.py")
    parser.add_argument("--seats", type=int, choices=[2, 4], default=2)
    parser.add_argument("--cases", type=parse_cases, required=True, help="Comma-separated seed:seat list.")
    parser.add_argument("--trace-out", required=True)
    parser.add_argument("--summary-out", required=True)
    parser.add_argument("--turns-out", default=None)
    parser.add_argument("--trace-all", action="store_true", help="Set ORBIT_MODE_TRACE_ALL=1.")
    args = parser.parse_args()

    opponents = split_csv(args.opponents)
    trace_out = Path(args.trace_out)
    summary_out = Path(args.summary_out)
    turns_out = Path(args.turns_out) if args.turns_out else None
    trace_out.parent.mkdir(parents=True, exist_ok=True)
    summary_out.parent.mkdir(parents=True, exist_ok=True)
    if turns_out is not None:
        turns_out.parent.mkdir(parents=True, exist_ok=True)

    previous_trace = os.environ.get("ORBIT_MODE_TRACE")
    previous_trace_all = os.environ.get("ORBIT_MODE_TRACE_ALL")

    try:
        with (
            trace_out.open("w", encoding="utf-8") as trace_fh,
            summary_out.open("w", encoding="utf-8") as summary_fh,
        ):
            turns_fh = turns_out.open("w", encoding="utf-8") if turns_out is not None else None
            try:
                for seed, tested_seat in args.cases:
                    if tested_seat < 0 or tested_seat >= args.seats:
                        raise ValueError(f"tested_seat={tested_seat} is outside seats={args.seats}")
                    with tempfile.TemporaryDirectory() as tmpdir:
                        tmp_trace = Path(tmpdir) / "mode_trace.jsonl"
                        os.environ["ORBIT_MODE_TRACE"] = str(tmp_trace)
                        if args.trace_all:
                            os.environ["ORBIT_MODE_TRACE_ALL"] = "1"
                        elif "ORBIT_MODE_TRACE_ALL" in os.environ:
                            del os.environ["ORBIT_MODE_TRACE_ALL"]

                        summary, turns = run_game(seed, args.agent, opponents, args.seats, tested_seat)
                        trace_rows = load_jsonl(tmp_trace)

                    summary_fh.write(json.dumps(summary, ensure_ascii=False) + "\n")
                    summary_fh.flush()
                    if turns_fh is not None:
                        for row in turns:
                            turns_fh.write(json.dumps(row, ensure_ascii=False) + "\n")
                        turns_fh.flush()

                    for row in trace_rows:
                        row.setdefault("seed", seed)
                        row.setdefault("seats", args.seats)
                        row.setdefault("tested_seat", tested_seat)
                        row.setdefault("tested_agent", args.agent)
                        row.setdefault("opponents", opponents)
                        row.setdefault("tested_reward", summary.get("tested_reward"))
                        row.setdefault("final_raw_diff", summary.get("final_raw_diff"))
                        row.setdefault("failure_bucket", summary.get("failure_bucket"))
                        row.setdefault("first_prod_share_lt_40", summary.get("first_prod_share_lt_40"))
                        trace_fh.write(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n")
                    trace_fh.flush()

                    print(
                        f"seed={seed} seat={tested_seat} reward={summary['tested_reward']} "
                        f"raw_diff={summary['final_raw_diff']} bucket={summary['failure_bucket']} "
                        f"trace_rows={len(trace_rows)} elapsed={summary['elapsed_s']:.3f}s"
                    )
            finally:
                if turns_fh is not None:
                    turns_fh.close()
    finally:
        if previous_trace is None:
            os.environ.pop("ORBIT_MODE_TRACE", None)
        else:
            os.environ["ORBIT_MODE_TRACE"] = previous_trace
        if previous_trace_all is None:
            os.environ.pop("ORBIT_MODE_TRACE_ALL", None)
        else:
            os.environ["ORBIT_MODE_TRACE_ALL"] = previous_trace_all


if __name__ == "__main__":
    main()
