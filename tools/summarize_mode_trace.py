from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path


def load_rows(path: Path) -> list[dict]:
    rows = []
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


def reason_keys(row: dict) -> list[str]:
    keys = []
    for key in ("first_target_mismatch", "predicted_path_hits_sun", "overbudget"):
        if row.get(key):
            keys.append(key)
    if row.get("commit_allowed") is False:
        keys.append("dropped")
    return keys or ["clean"]


def relation_tuple(row: dict) -> str:
    return f"{row.get('target_relation')}->{row.get('first_relation')}"


def show_counter(title: str, counter: Counter, limit: int) -> None:
    print(f"\n== {title}")
    for key, count in counter.most_common(limit):
        print(f"{count:6d} {key}")


def summarize(path: Path, limit: int) -> None:
    rows = load_rows(path)
    print(f"# {path}")
    print(f"rows={len(rows)}")
    if not rows:
        return

    errors = Counter(row.get("trace_error") for row in rows if row.get("trace_error"))
    unknown = sum(1 for row in rows if row.get("mode_label") == "unknown")
    print(f"errors={dict(errors)} unknown_mode={unknown}")

    by_mode = Counter(row.get("mode_label", "missing") for row in rows)
    by_reason = Counter()
    by_reason_mode = Counter()
    by_reason_relation = Counter()
    by_reason_mode_relation = Counter()
    by_player_reason_mode = Counter()
    top_patterns = Counter()

    for row in rows:
        mode = row.get("mode_label", "missing")
        player = row.get("player", "na")
        rel = relation_tuple(row)
        pattern = (mode, row.get("src"), row.get("target"), row.get("first_id"))
        for reason in reason_keys(row):
            by_reason[reason] += 1
            by_reason_mode[(reason, mode)] += 1
            by_reason_relation[(reason, rel)] += 1
            by_reason_mode_relation[(reason, mode, rel)] += 1
            by_player_reason_mode[(player, reason, mode)] += 1
        if row.get("first_target_mismatch"):
            top_patterns[pattern] += 1

    show_counter("mode", by_mode, limit)
    show_counter("reason", by_reason, limit)
    show_counter("reason x mode", by_reason_mode, limit)
    show_counter("reason x relation", by_reason_relation, limit)
    show_counter("reason x mode x relation", by_reason_mode_relation, limit)
    show_counter("player x reason x mode", by_player_reason_mode, limit)
    show_counter("top mismatch patterns (mode, src, target, first)", top_patterns, limit)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("traces", nargs="+")
    parser.add_argument("--limit", type=int, default=30)
    args = parser.parse_args()

    for trace in args.traces:
        summarize(Path(trace), args.limit)


if __name__ == "__main__":
    main()
