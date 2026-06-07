# Scored Candidate Analysis And Improvement Backlog

Date: 2026-06-07

Latest score observation: `2026-06-07T13:58:29+09:00`

This document summarizes the candidates that already have meaningful Kaggle public-LB feedback and turns the result into the next reviewable improvement actions. It should be read together with `06-autonomous-improvement-log.md` and `07-submission-postmortem-and-next-plan.md`.

## Current Score Snapshot

| Ref | File | Family | Latest observed public score | Status | Interpretation |
| --- | --- | --- | ---: | --- | --- |
| 53439162 | `candidates/production_candidate.py` | Loop046, 2P/4P preemptive-evac ratio split plus commit/hammer consistency bundle | 933.1 | COMPLETE | Current latest-observed leader |
| 53418690 | `main.py` | locked vickimar heuristic fixed | 908.0 | COMPLETE | Previous best and fallback baseline |
| 53439169 | `candidates/research_best_4p.py` | Loop033, global preemptive-evac ratio 1.35 | 907.8 | COMPLETE | Near-baseline useful signal, but not leader |
| 53439165 | `candidates/research_best_2p.py` | Loop021, return-aware commit-drop / commit guard family | 600.0 | COMPLETE | Dangerous or unresolved; do not promote |

Notes:

- Public score values have moved after submission, so every score claim needs an observation time.
- Loop046 is strong enough to become the current working champion, but `main.py` should not be overwritten until another review explicitly approves it.
- Loop021's latest display remains `600.0`; whether this reflects final strength or a leaderboard artifact is unresolved, but it is unusable as a promotion signal.

Score history observed locally:

| Ref | File | Earlier observed score | Latest observed score | Read |
| --- | --- | ---: | ---: | --- |
| 53439162 | `production_candidate.py` | 915.2 | 933.1 | Strengthening; current working champion |
| 53439169 | `research_best_4p.py` | 885.7 | 907.8 | Recovered to near-tie with 908 baseline |
| 53439165 | `research_best_2p.py` | 600.0 | 600.0 | Still unresolved / not promotable |

## Diff Taxonomy

The useful information is the path between files, not only the final scores.

| Transition | Main change | Evidence | Read |
| --- | --- | --- | --- |
| `main.py` -> Loop021 | Adds `_can_commit_fleet`, `_can_commit_many`, and return-aware `_commit_fleet` behavior across many call sites | Strong local H2H, public `600.0` | Broad commit-drop alone is risky and not promotable |
| Loop021 -> Loop033 | Changes preemptive evacuation to global doom ratio `1.35` | Public `907.8`, local 4P below Loop046 | Useful but not enough; global ratio hurts somewhere |
| Loop033 -> Loop046 | Splits ratio by mode: 2P `1.20`, 4P `1.35` | Public `933.1` | Best current signal; mode split likely matters |
| `main.py` -> Loop049 | Adds only 4P ratio `1.35`, no commit guard bundle | Local 4P seat0 screen failed, not submitted | Ratio alone does not explain Loop046's strength |

Working conclusion:

- Loop046's advantage is probably a bundle: mode split plus commit/hammer consistency.
- The same bundle still has local collapse modes, especially in 4P seat0.
- Future edits should branch from Loop046 and change one lever at a time.

## Local Evaluation Summary

Existing local logs say Loop046 is a real improvement candidate, but they also show why the local proxy is not enough.

| Eval | Rows | Wins | Avg raw diff | Raw zero | Bad | Important seat signal |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| Loop046 vs `main.py`, 2P, seeds 500-509 h012 | 60 | 42/60 | +1637.2 | 18 | 0 | balanced seat0/seat1 |
| Loop046 vs `main.py`, 2P, seeds 600-609 h012 | 60 | 39/60 | +798.0 | 21 | 0 | seat0 weaker than seat1 |
| Loop046 vs 4P pool, seeds 500-504 h012 | 60 | 39/60 | +923.0 | 21 | 0 | seat0 strong, seat1/3 weaker |
| Loop046 vs 4P pool, seeds 600-604 h012 | 60 | 36/60 | +693.6 | 24 | 0 | seat0 negative, seat3 strong |
| Loop046 vs 4P pool, seeds 700-719 h012 file only | 160 | 90/160 | +371.6 | 70 | 0 | seat0: 16/40, avg -1258.9 |
| Loop046 vs 4P pool, seeds 700-719 h012 + h2 combined | 240 | 135/240 | +371.6 | 105 | 0 | seat0: 24/60, avg -1258.9 |

Local proxy reading:

- It correctly found Loop046 as promising.
- It also overestimated Loop021 and cannot be used as a leaderboard predictor by itself.
- From now on, local eval is a filter for bad changes, not proof of final strength.

## Loop046 Remaining Weaknesses

The cleanest diagnosed weakness is 4P seat0 collapse.

`eval_results/turn_metrics_loop046_4p_seat0_700_719_summary.jsonl`:

| Bucket | Count | Read |
| --- | ---: | --- |
| win | 8/20 | Still wins many seat0 maps, so do not overfit away the core strategy |
| early-expansion-lag | 5/20 | Raw gap appears early, average first `< -500` around turn 70 |
| overcommit-collapse | 7/20 | Collapse appears later, average first `< -500` around turn 152 |

This suggests two separate failure modes:

- Early-lag: the opening does not claim enough productive territory before other agents snowball.
- Overcommit-collapse: the agent eventually empties or commits from key planets in a way that loses production and dies to recapture.

Rejected attempts:

- Loop047 extended 4P opening turn to 14. It worsened seat0: 6/20, avg -1940.0.
- Loop048 production reserve worsened seat0 badly in partial run: 1/11, avg -3318.0.
- Loop049 ratio-only from locked 908 failed seat0: 1/5, avg -2168.6.

## Action Audit Read

Static action audit for Loop046 produced suspicious findings but no invalid/timeout hard errors.

| Audit | Rows | Wins | Avg raw | Sun | Wrong planet | Nothing | Miss angle | Underpowered |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 2P vs `main.py`, seeds 500-509 | 20 | 14/20 | +1637.2 | 16 | 75 | 80 | 82 | 151 |
| 2P vs `main.py`, seeds 600-609 | 20 | 13/20 | +798.0 | 41 | 133 | 169 | 175 | 270 |
| 4P pool, seeds 500-504 | 20 | 13/20 | +923.0 | 10 | 25 | 58 | 58 | 80 |
| 4P pool, seeds 600-604 | 20 | 12/20 | +693.6 | 33 | 44 | 53 | 70 | 127 |

Important limitation:

- The audit guesses target from current angle and static geometry. It is useful for comparing candidates, not as a direct proof that every flagged launch is bad.

Current read:

- Do not start with a broad physics rewrite.
- Any candidate that increases `static_path_hits_sun`, `static_path_hits_wrong_planet`, or invalid ship counts should be rejected unless it produces overwhelming local and public evidence.

## Improvement Backlog

### A1: Preserve Loop046 As Working Champion

Status: approved direction by review agent.

Actions:

- Treat `candidates/production_candidate.py` as current latest-observed leader.
- Keep `main.py` as previous-best fallback.
- Submit future candidates only if they pass against Loop046, not merely against `main.py`.

Stop rule:

- Do not overwrite `main.py` in this action.

### A2: Seat0 Diagnostic First

Status: next recommended action.

Actions:

- Re-run turn metrics for Loop046 on 4P all seats for a small holdout band.
- Compare seat0 loss buckets against seat1/2/3 instead of only optimizing seat0.
- Record whether seat0 losses are mostly early-lag or overcommit-collapse in the new band.

Why:

- Loop046 is strong publicly despite seat0 weakness, so the next change must reduce collapses without damaging other seats.

### A3: Early-Lag Micro Candidate

Status: candidate idea, not yet approved for edit.

Allowed edit shape:

- One narrow 4P-only opening selector adjustment.
- Must not extend the whole opening phase like Loop047.
- Prefer a targeted safe neutral / high-production pickup gate over a global tempo change.

Gate:

- Compare to Loop046, not `main.py`.
- Require no 2P regression and no 4P all-seat collapse.

### A4: Overcommit-Collapse Micro Candidate

Status: candidate idea, not yet approved for edit.

Allowed edit shape:

- One narrow 4P-only launch brake that triggers only when production share or owned planet count is already fragile.
- Avoid passive reserve rules like Loop048.
- Avoid broad commit-guard rewrites, because Loop021 is unresolved/dangerous.

Gate:

- Must improve overcommit-collapse seeds without converting early-lag wins into losses.

### A5: Action Audit Gate

Status: mandatory after every candidate.

Actions:

- Run `review_action_accuracy.py` on the candidate and Loop046 baseline over the same seeds.
- Reject if hard errors or suspicious path findings rise materially without clear performance gain.

## Review Record

Review Agent result for this analysis direction:

- Approved using Loop046 as latest-observed leader with `observed_at`.
- Approved analyzing before editing.
- Warned not to treat commit guard as universally safe or universally bad.
- Warned not to overfit only to local fixed maps or 4P seat0.
- Recommended exact diff taxonomy, score history, local proxy caveats, and Loop046 diagnostics before new code changes.

## Next Concrete Step

Run action A2:

1. Re-check Kaggle scores.
2. Run Loop046 turn metrics on a small 4P all-seat holdout band.
3. Ask review agent to validate the resulting failure-bucket interpretation.
4. Only then create one micro candidate from either A3 or A4.
