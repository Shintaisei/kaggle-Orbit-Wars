# Orbit Wars Submission Postmortem And Next Plan

Date: 2026-06-07

This document is the handoff summary after the first serious local-improvement loop and three Kaggle submissions. It supersedes earlier score snapshots; Kaggle public scores changed over time after submission and should be treated as latest-observed values, not immutable one-time results.

## Executive Decision

Current latest-observed public-LB best is:

- `candidates/production_candidate.py` / Loop046
- locked snapshot: `locked_submissions/53439162_loop046_production_candidate_PENDING.py`
- latest observed public score: 915.2 at `2026-06-07T13:48:44+09:00`
- SHA256: `B69C084A3DCD18F24D19E51EAB68B93B5D9781B7A6FEC9CDA31ACD18C8220DB4`

Do not overwrite `main.py` yet until the score is stable across another check, but treat Loop046 as the current challenger to preserve and build from cautiously:

- `candidates/research_best_2p.py` / Loop021
- `candidates/research_best_4p.py` / Loop033
- `candidates/loop_047_opening4p14.py`
- `candidates/loop_048_prod_reserve_4p.py`

Loop046 is now the latest-observed leader. Loop033 is no longer a near-miss in the latest snapshot, and Loop021 remains unresolved because its 600.0 may be an evaluation-not-started artifact.

## Submission Results

Latest observed at `2026-06-07T13:48:44+09:00`:

| Ref | File | Family | Public score | Decision |
| --- | --- | --- | ---: | --- |
| 53439162 | `production_candidate.py` | Loop046, mode split ratio 2P 1.20 / 4P 1.35, commit guard family | 915.2 | Latest-observed leader |
| 53418690 | `main.py` / locked 908 | public vickimar fixed baseline | 908.0 | Previous best |
| 53439169 | `research_best_4p.py` | Loop033, Loop021 plus ratio 1.35 | 885.7 | Useful signal, below 908 in latest snapshot |
| 53439165 | `research_best_2p.py` | Loop021, return-aware commit-drop | 600.0 | Pending interpretation; likely not fully evaluated yet |

Local locked snapshots:

- `locked_submissions/53439162_loop046_production_candidate_PENDING.py`
- `locked_submissions/53439165_loop021_research_best_2p_PENDING.py`
- `locked_submissions/53439169_loop033_research_best_4p_PENDING.py`

The filenames still contain `PENDING` because they were locked immediately after upload. The current observed public scores are listed above and in `locked_submissions/README.md`.

## Pre-submit Validation

All three submitted candidates passed basic local submission checks:

- `py_compile`: passed.
- Random smoke, 2P and 4P all seats: `DONE`, bad 0.
- 2P vs `main.py` smoke: `DONE`, bad 0.
- 4P pool smoke vs `main.py`, `variants/roman_lb1224.py`, `variants/suneet_lb1200.py`: `DONE`, bad 0.
- Review Agent: GO for submission as separate portfolio candidates.

The local checks verified that the files run. They did not prove public-LB strength.

## Local Evaluation That Misled Us

Loop046 looked strong under fixed local evaluation:

| Evaluation | Rows | Wins | Avg raw diff | Bad |
| --- | ---: | ---: | ---: | ---: |
| Loop046 vs `main.py`, 2P, seeds 500-509 h012 | 60 | 42/60 | +1637.2 | 0 |
| Loop046 vs `main.py`, 2P, seeds 600-609 h012 | 60 | 39/60 | +798.0 | 0 |
| Loop046 vs 4P pool, seeds 500-504 h012 | 60 | 39/60 | +923.0 | 0 |
| Loop046 vs 4P pool, seeds 600-604 h012 | 60 | 36/60 | +693.6 | 0 |

Public LB now promotes it in the latest observed snapshot:

- Loop046 latest observed public score: 915.2.
- Previous best public score: 908.0.

Interpretation:

- Fixed-map local head-to-head vs `main.py` is useful for debugging and candidate search.
- It is not sufficient promotion evidence.
- The local pool is too narrow and can reward strategies that exploit `main.py` or a few known public agents but lose broad LB robustness.

## Seat0 And Later Loops

Loop046 had a known 4P seat0 weakness:

| Candidate | Eval | Wins | Avg raw diff | Raw-zero | Bad | Decision |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| Loop046 | 4P seat0 pool, seeds 700-719 h0 | 8/20 | -1258.9 | 12 | 0 | Best local candidate but not promotable |
| Loop047 | Same, `PSM_OPENING_TURN_4P = 14` | 6/20 | -1940.0 | 14 | 0 | Reject |
| Loop048 | Partial same band, 11 rows, 4P production reserve | 1/11 | -3318.0 | 10 | 0 | Reject or do not continue without strong reason |

Loop047 showed that extending 4P opening did not solve early-expansion-lag and flipped good seeds into raw-zero losses.

Loop048 showed that a passive production reserve likely worsens tempo. It passed smoke but failed the partial primary signal badly.

## Revised Diagnosis

The broad commit guard / return-aware commit-drop mechanism is a risk factor, not a sufficient explanation for all results.

Evidence that makes commit-drop risky:

- Loop021 differs from locked 908 mainly by adding `_can_commit_fleet`, `_can_commit_many`, and return-aware `_commit_fleet` drop checks across many call sites.
- Loop021 scored 600.0 publicly.
- Past action audit already flagged Loop021 as risky:
  - more `static_path_hits_wrong_planet`,
  - more `static_path_hits_sun`,
  - seat instability.
- Earlier docs explicitly rejected Loop021 for champion promotion despite strong local head-to-head results.

Evidence that weakens a single-cause diagnosis:

- Loop033 and Loop046 also contain commit guard, but latest observed scores are 902.5 and 899.1, not 600.0.
- This suggests some bundled behavior has serious public-LB value despite the Loop021 collapse.
- Therefore, the correct wording is:
  - Loop021 strongly implicates commit-drop-only direction as unsafe,
  - Loop033/046 show that some bundled ideas are near-leader strength and deserve careful isolation.

## What Not To Do

Do not:

- overwrite `main.py` with Loop021, Loop033, or Loop046;
- use Loop021-family files as the new base;
- reintroduce broad `_can_commit_fleet` / `_can_commit_many` commit-drop as a default;
- trust fixed-map head-to-head wins against `main.py` as sufficient promotion evidence;
- submit Loop047 or Loop048;
- optimize only for raw score against the current local pool.

## Current Candidate Status

| File | Status | Reason |
| --- | --- | --- |
| `main.py` | Previous best | Public 908.0 |
| `locked_submissions/53418690_vickimar_heuristic_fixed_SCORE_908_0.py` | Canonical 908 baseline | Exact snapshot of current best |
| `candidates/production_candidate.py` | Latest-observed leader | Latest public 915.2 |
| `candidates/research_best_2p.py` | Unresolved | Public still 600.0, may not have fully evaluated |
| `candidates/research_best_4p.py` | Useful signal | Latest public 885.7 |
| `candidates/loop_047_opening4p14.py` | Rejected | Worse local 4P seat0 |
| `candidates/loop_048_prod_reserve_4p.py` | Rejected / stop | Bad partial local signal, 11 rows only |
| `candidates/loop_049_locked908_ratio4p135.py` | Rejected / stop | Starts from locked 908, no commit guard; 4P seat0 screen failed |

## Next Minimal Experiment

The next clean experiment is already started:

- `candidates/loop_049_locked908_ratio4p135.py`

Purpose:

- Test whether the useful part of Loop033/046 is the 4P preemptive-evac ratio, not the commit guard.

Design:

- Base: locked 908 snapshot.
- No `_can_commit_fleet`.
- No `_can_commit_many`.
- No return-aware `_commit_fleet` drop.
- 2P remains the locked 908 behavior:
  - `PREEMPTIVE_EVAC_DOOM_RATIO = 1.20`.
- 4P uses:
  - `PREEMPTIVE_EVAC_DOOM_RATIO_4P = 1.35`.

Current Loop049 evidence:

- Diff from locked 908 is limited to the 4P ratio branch and constant.
- SHA256: `9EAF602B468A40587521984E187756DDBB789355A2C0AF73B7F60FE5588DF1C2`.
- `py_compile`: passed.
- Random 2P/4P all-seat smoke: 6/6, bad 0.
- 2P vs `main.py` smoke: 3/6, avg raw 0.0, bad 0. This is expected to be parity-like because both are effectively 908 in 2P.
- 4P pool rerun was stopped early after the seat0 screen failed:
  - `eval_results/loop049_vs_pool_4p_930_934_h0_rerun.jsonl`.
  - Partial rows: 6.
  - Seat0 complete slice: 1/5 wins, avg raw -2168.6, raw-zero 4, bad 0.
  - Review gate said a seat-level collapse should reject the candidate.

## Required Gates For Future Candidates

Local gates:

- Smoke random/starter: invalid/timeout 0.
- 2P parity vs locked 908:
  - no clear regression,
  - if the candidate claims 2P unchanged, verify practical parity.
- 4P pool:
  - no seat collapse,
  - compare all seats, not just total wins.
- Action audit:
  - do not increase `static_path_hits_sun`,
  - do not increase `static_path_hits_wrong_planet`,
  - do not introduce invalid ship counts.

Promotion gates:

- Public LB is the final gate.
- `> 908`: promote to new leader.
- `902.5-908`: near miss; do not promote, isolate one more improvement.
- `899-902.5`: useful signal, weaker than current Loop033 near-miss.
- `< 899`: reject as leader.
- Around `600`: stop that candidate family unless there is a narrow diagnostic reason.

## Practical Next Steps

1. Do not submit Loop049.
2. Stop ratio-only 4P evac as a standalone fix from locked 908.
3. Continue from locked 908, but look for a different isolated lever than broad commit-drop or scalar preemptive-evac ratio.
4. Any next candidate must pass all-seat 4P screening before action audit or LB submission.

## Local Proxy Calibration

After the public score refresh, a quick calibration run tested known-score agents against the same 4P public-agent pool:

- opponents: `variants/roman_lb1224.py`, `variants/suneet_lb1200.py`, `variants/rahul_target2000.py`
- seed: 961
- seats: 4, rotate seats
- hash seed: 0

| Agent | Latest public | Local wins | Avg raw diff | Raw-zero | Bad |
| --- | ---: | ---: | ---: | ---: | ---: |
| `main.py` / locked 908 | 908.0 | 4/4 | +2188.5 | 0 | 0 |
| Loop033 / `research_best_4p.py` | 902.5 | 3/4 | +399.2 | 1 | 0 |
| Loop046 / `production_candidate.py` | 899.1 | 4/4 | +2413.5 | 0 | 0 |
| Loop021 / `research_best_2p.py` | 600.0 | 4/4 | +2296.8 | 0 | 0 |

Interpretation:

- This one-seed public-agent pool proxy is not reliable as a public-LB ranking proxy.
- It correctly shows these agents run without invalid/timeout, but it fails to demote Loop021 despite its public 600.0 score.
- Future local evaluation should not rely on a single map or a tiny public-agent pool for promotion decisions.
- The local proxy can still be used as a smoke or crash screen, but public LB remains the promotion gate.

## Score Refresh And Action Analysis

Latest observed at `2026-06-07T13:50:56+09:00`:

| Ref | File | Public score | Interpretation |
| --- | --- | ---: | --- |
| 53439162 | `production_candidate.py` / Loop046 | 915.2 | Current latest-observed leader |
| 53418690 | `main.py` / locked 908 | 908.0 | Previous best |
| 53439169 | `research_best_4p.py` / Loop033 | 885.7 | Useful but below 908 in latest snapshot |
| 53439165 | `research_best_2p.py` / Loop021 | 600.0 display | Do not conclude; may be early/placeholder evaluation |

Code comparison:

- Loop046 vs Loop033:
  - only meaningful difference is the preemptive-evac ratio split,
  - Loop033 uses `PREEMPTIVE_EVAC_DOOM_RATIO = 1.35` globally,
  - Loop046 uses `1.20` in 2P and `1.35` in 4P.
- Loop046 vs locked 908:
  - adds return-aware `_commit_fleet()` and source-budget checks,
  - adds `_can_commit_many()` all-or-nothing checks for multi-source missions,
  - updates call sites so failed commits do not mark a mission as successful,
  - changes hammer due-launch handling to abort all-or-nothing instead of silently dropping contributors,
  - re-aims hammer contributors after trimming and recomputes target arrival/required strength,
  - uses the 2P/4P preemptive-evac ratio split.

Current inference:

- Loop046 should be treated as the current leader to preserve.
- Loop033 being below Loop046 supports the ratio split over global 1.35.
- Loop049 showed that adding 4P ratio 1.35 alone to locked 908 is not enough, and locally collapsed on 4P seat0.
- Therefore, the useful signal is probably the combination of commit/hammer consistency plus ratio split, not scalar ratio alone.

Action candidates sent to review:

- Action A: preserve Loop046 as current leader, lock it as the new working best, and branch future candidates from it while delaying `main.py` overwrite until score stability is rechecked.
- Action B: choose next improvement path from Loop046:
  - B1: tiny 4P ratio sweep around 1.35, such as 1.30 or 1.40;
  - B2: targeted 4P seat0 stabilization, noting opening extension and production reserve already failed;
  - B3: no behavior edit yet; run action audit / turn metrics on Loop046 to identify remaining failure buckets.

Review result:

- Action A approved:
  - Treat Loop046 as current observed leader.
  - Do not overwrite `main.py` until the score is rechecked and the snapshot is locked.
  - Branch future experiments from Loop046.
  - Keep locked 908 as fallback/reference.
- Action B recommendation:
  - Do B3 first.
  - Loop046 is now a high-scoring bundle, so changing it blindly is riskier than diagnosing its remaining losses.
  - Ratio sweeps should wait until diagnostics show that ratio is still the likely lever.

Next diagnostic order:

1. Compare Loop046 vs main on known local bands.
2. Run action audit against main.
3. Run turn metrics on Loop046 losses, especially 4P seat0 and raw-zero losses.
4. Only then try one micro-change at a time, likely 4P ratio `1.30` or `1.40` from Loop046.

Strict gates for any next candidate:

- Must beat or match Loop046 locally, not merely beat `main.py`.
- bad/invalid/timeout must be 0.
- 2P parity vs Loop046 must not regress.
- 4P all-seat pool must not show seat collapse.
- action audit must not increase hard sun / wrong-planet / invalid ship findings.
- LB submissions should be one micro-change at a time.

## One-line Handoff

The local loop found interesting ideas, but the only proven leader is still the locked 908 `main.py`; restart from 908, avoid broad commit-drop, do not use scalar 4P evac ratio alone, isolate one small hypothesis at a time, and treat public LB as the promotion gate.
