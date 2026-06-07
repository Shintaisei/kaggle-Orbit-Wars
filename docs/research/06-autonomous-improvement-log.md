# Autonomous Improvement Log

This log records rule-based improvement loops, reviewer feedback, benchmark results, and champion changes.

## 2026-06-06 Loop 001: Same-Turn Combat Projection

Base champion: `candidates/candidate_02_less_defense_absorption.py`.

Hypothesis:
- Public-notebook playbook says arrival ledger should resolve same-turn multi-owner combat with official top-two cancellation.
- `effective_garrison_at_arrival()` in the 908-lineage agent handled same-ETA fleets sequentially, so capture cost could be wrong.

Reviewer notes:
- Review A approved fixing `effective_garrison_at_arrival()` only as the minimal Action 3 change.
- Review A warned not to mix `compute_planet_reserve()` in the first attempt.
- Review B found the mixed `loop_001_same_turn_combat.py` reserve rewrite unsafe: rescue deadline can become `None`, and 4P rescue deficit conflates surface reserve with fleet reinforcement.

Candidates:
- `candidates/loop_001_same_turn_combat.py`: rejected. It changed both attack projection and reserve calculation, mixing hypotheses and introducing defense risks.
- `candidates/loop_001a_effective_garrison_only.py`: kept. It changes only `effective_garrison_at_arrival()` to group arrivals by ETA and call `_resolve_combat()`.

Benchmarks versus previous champion:
- Gate seed 20-24, both seats: 7/10 wins, avg raw diff positive overall but seat0 weak.
- Holdout seed 100-104, both seats: 9/10 wins, avg raw diff strongly positive.
- Combined: 16/20 wins if counting seed 22 raw tie as reward win; invalid/timeout 0.

Decision:
- Promote `loop_001a_effective_garrison_only.py` to `candidates/champion_current.py`.
- Keep `candidate_02_less_defense_absorption.py` as previous champion for regression testing.

Next loop ideas:
- Do not alter reserve math until defense rescue semantics are explicitly tested.
- Candidate should target either existing-fleet first-collision inference or C02 pure defense-budget cleanup.
## 2026-06-06 Loop 002: Existing Fleet Sun Filter

Base champion: `candidates/champion_current.py`.

Hypothesis:
- `fleet_target_planet()` should not add an existing fleet to the arrival ledger if the fleet would hit the sun before the inferred planet collision.

Reviewer notes:
- Direction matches Action 3 first-collision inference.
- Reviewer required strict `SUN_R` detection for existing fleet reconstruction, not `SUN_R + SUN_SAFETY` used for conservative launch planning.

Candidate:
- `candidates/loop_002_fleet_sun_filter.py`.
- Static and orbital inferred hits both skip if the segment from current fleet position to inferred hit point crosses strict sun radius.

Benchmarks versus current champion:
- Gate seed 20-24, both seats: 6/10 wins, avg raw diff modestly positive.
- Holdout seed 100-104, both seats: 6/10 wins, avg raw diff positive but not decisive.
- invalid/timeout 0.

Decision:
- Reject for champion promotion. Direction is physically cleaner, but benchmark edge is below the 65%+ decisive threshold and may be seed-noise.
- Keep as a possible future merge only if combined with better fleet first-collision/sweep inference.
## 2026-06-06 Loop 003: Defense Pure Ablation

Base champion: `candidates/champion_current.py`.

Hypothesis:
- Separate C02's defense absorption changes from mixed hammer/evac tuning.
- Keep `ABSORB_MIN_THREAT=5`, `DEFENSE_OVERSEND_2P=0`, `DEFENSE_COALITION_MAX=1`, and same-turn effective garrison projection.
- Revert `HAMMER_STOCKPILE_MIN` from 45 to 50 and `PREEMPTIVE_EVAC_DOOM_RATIO` from 1.10 to 1.20.

Candidate:
- `candidates/loop_003_defense_pure.py`.

Benchmarks versus current champion:
- Gate seed 20-24, both seats: 4/10 wins.
- avg raw diff negative on both seats.
- invalid/timeout 0.

Decision:
- Reject. Pure defense absorption is not enough against current champion.
- The mixed hammer/evac tuning in C02 likely contributes materially to the champion's strength.

Next loop ideas:
- Isolate hammer stockpile threshold and preemptive evac ratio one at a time against current champion.
## 2026-06-06 Loop 004: Evac/Hammer Ablation

Base champion: `candidates/champion_current.py`.

Hypothesis:
- Loop003 showed reverting both mixed C02 constants hurt performance. Isolate whether the effect comes from hammer fallback or preemptive doom-evac threshold.

Reviewer notes:
- `HAMMER_STOCKPILE_MIN` is mostly inert because `MODE_PARAMS` and `MODE_PARAMS_2P` provide `hammer_stockpile_min` in normal play.
- `PREEMPTIVE_EVAC_DOOM_RATIO` is likely the real differentiator.

Candidates:
- `candidates/loop_004a_hammer_fallback_ablation.py`: global fallback `HAMMER_STOCKPILE_MIN=50`; expected mostly inert.
- `candidates/loop_004b_evac_ablation.py`: `PREEMPTIVE_EVAC_DOOM_RATIO=1.20`; main.py value.

Benchmarks versus current champion:
- 004b gate seed 20-24, both seats: 3/10 wins, avg raw diff negative. Reject.
- 004a spot seed 20-22, both seats: 5/6 wins but likely near mirror/noise; not considered a real improvement because global fallback is normally overridden.

Decision:
- Keep current champion unchanged.
- Treat `PREEMPTIVE_EVAC_DOOM_RATIO=1.10` as a material contributor to current champion strength.

Next loop ideas:
- Tune `PREEMPTIVE_EVAC_DOOM_RATIO` lower than 1.10, e.g. 1.05 and 1.00, against current champion.
## 2026-06-06 Loop 005: More Aggressive Doom Evac

Base champion: `candidates/champion_current.py` with `PREEMPTIVE_EVAC_DOOM_RATIO=1.10`.

Hypothesis:
- Loop004 showed 1.20 is too conservative. Try earlier evacuation to reduce wasted defense/absorption.

Candidates:
- `candidates/loop_005a_evac_105.py`: ratio 1.05.
- `candidates/loop_005b_evac_100.py`: ratio 1.00.

Benchmarks versus current champion:
- 1.05 gate seed 20-24, both seats: 3/10 wins, avg raw diff negative. Reject.
- 1.00 gate seed 20-24, both seats: 6/10 wins, avg raw diff positive but below promotion threshold. Reject for champion promotion.

Decision:
- Keep current champion at ratio 1.10.
- 1.10 appears near a useful local optimum; test tighter neighbors next if continuing.

## 2026-06-06 Loop 006: Tight Doom Evac Neighbor Search

Base champion: `candidates/champion_current.py` with `PREEMPTIVE_EVAC_DOOM_RATIO=1.10`.

Hypothesis:
- Test whether the 1.10 local optimum can be improved with tighter neighbors.

Candidates:
- `candidates/loop_006a_evac_108.py`: ratio 1.08.
- `candidates/loop_006b_evac_112.py`: ratio 1.12.

Benchmarks versus current champion:
- 1.08 gate seed 20-24, both seats: 4/10 wins, avg raw diff weak/negative. Reject.
- 1.12 gate seed 20-24, both seats: 3/10 wins, avg raw diff negative. Reject.
- invalid/timeout 0.

Decision:
- Keep current champion unchanged.
- Do not continue ratio-only doom-evac tuning unless new diagnostic logs show a specific failure.
- Next useful line is actual `MODE_PARAMS` hammer threshold tuning, because global `HAMMER_STOCKPILE_MIN` was mostly inert.
## 2026-06-06 Loop 007: 2P Hammer Stockpile Minimum

Base champion: `candidates/champion_current.py`.

Hypothesis:
- Tune the actual 2P hammer stockpile threshold in `MODE_PARAMS_2P`, not the mostly inert global fallback.

Candidates:
- `candidates/loop_007a_hammer_2p_min20.py`: all 2P modes `hammer_stockpile_min=20`.
- `candidates/loop_007b_hammer_2p_min30.py`: all 2P modes `hammer_stockpile_min=30`.

Reviewer notes:
- 20/30 is a reasonable ±5 scan.
- In 2P, `_detect_mode()` effectively uses `patient` only in opening and `pressure` afterwards, so all-mode tuning mostly tests pressure tuning.
- 20 risks adding small/far stockpiles that delay synchronized hammer arrival or drain frontier defense.

Benchmarks versus current champion:
- 20 gate seed 20-24, both seats: 7/10 wins, positive raw. Promising.
- 20 holdout seed 100-104, both seats: 2/10 wins, strongly negative raw. Reject.
- 30 gate seed 20-24, both seats: 3/10 wins, negative raw. Reject.

Decision:
- Keep current champion unchanged.
- All-mode 2P stockpile min=20 overfits gate seeds and fails holdout.
- Next test should isolate `pressure` mode only rather than all modes.
## 2026-06-06 Loop 008: Pressure-Only Hammer Min 20

Base champion: `candidates/champion_current.py`.

Hypothesis:
- Since 2P effectively uses `pressure` after opening, test only `MODE_PARAMS_2P["pressure"]["hammer_stockpile_min"] = 20` while keeping patient/opportunistic at 25.

Candidate:
- `candidates/loop_008_pressure_hammer_min20.py`.

Benchmarks versus current champion:
- Gate seed 20-24, both seats: 2/10 wins, strongly negative raw.
- invalid/timeout 0.

Decision:
- Reject. Lowering effective 2P hammer stockpile threshold is harmful on this gate.
- Do not continue lower-threshold hammer tuning without replay evidence.
## 2026-06-06 Loop 009/010: Reset To Main Ablations

Reason for reset:
- `candidate_02` and `champion_current` beat `main.py` on earlier seed bands, but both lost to `main.py` on seed 200-209.
- Adopt `main.py` as the primary 908K gate again; candidates must beat both `main.py` and the current internal champion to be promoted.

Candidates:
- `candidates/loop_009_main_evac110.py`: main.py + `PREEMPTIVE_EVAC_DOOM_RATIO=1.10` only.
- `candidates/loop_010_main_defense_absorb.py`: main.py + `ABSORB_MIN_THREAT=5`, `DEFENSE_OVERSEND_2P=0`, `DEFENSE_COALITION_MAX=1` only.

Benchmarks versus `main.py`, seed 200-204 both seats:
- Loop009: 3/10 wins, strongly negative raw. Reject.
- Loop010: 5/10 wins. seat0 1/5 negative, seat1 4/5 positive. Not promotable; suggests defense changes help some starts but create seat/asymmetry failures.

Decision:
- Reject Loop009.
- Keep Loop010 as diagnostic only.
- Next test: add the `_commit_fleet` source-budget clamp safety net to Loop010 and see whether seat0 raw=0 collapses reduce.
## 2026-06-06 Loop 011/012/013: Clamp And Remaining C02 Ablations

Context:
- Reviewer recommended evaluating `_commit_fleet` clamp and `HAMMER_STOCKPILE_MIN=45` as standalone main.py ablations.
- Gate seed band is now 200-204 because it exposed failures missed by earlier seed 20/100 bands.

Candidates:
- `candidates/loop_011_main_defense_clamp.py`: loop010 defense knobs + commit clamp.
- `candidates/loop_012_main_clamp_only.py`: main.py + commit clamp only.
- `candidates/loop_013_main_hammer45.py`: main.py + global `HAMMER_STOCKPILE_MIN=45` only.

Benchmarks versus `main.py`, seed 200-204 both seats:
- Loop011: 2/10 wins, worse than loop010. Reject.
- Loop012: 5/10 wins; seat0 4/5 strongly positive, seat1 1/5 strongly negative. Not promotable but diagnostic.
- Loop013: 2/10 wins, strongly negative. Reject.

Decision:
- No champion promotion.
- Global `HAMMER_STOCKPILE_MIN=45` is not useful by itself.
- Commit clamp changes behavior materially and introduces/uncovers strong seat asymmetry; do not adopt globally until seat1 failure is understood.

Next loop ideas:
- Investigate seat1 collapse for clamp-only and defense-knob candidates.
- Compare early turns for seed 200-204 seat1 between main.py and loop012 to identify whether clamp prevents an intended multi-commit or changes persistent commitments.
## 2026-06-06 Champion Reset

Reason:
- Internal champion `loop_001a_effective_garrison_only.py` beat C02 on seed 20/100 bands, but lost to `main.py` on fresh seed 200-209.
- `candidate_02_less_defense_absorption.py` also lost to `main.py` on seed 200-209.
- Therefore the earlier internal champion was overfit to selected seed bands and should not remain the working champion.

Decision:
- Reset `candidates/champion_current.py` to `main.py`.
- Promotion now requires beating `main.py` directly, not only beating prior candidates.
- Gate A: seed 200-209 both seats.
- Fresh holdout for promotion: seed 300-319 both seats.
- Minimum promotion criteria: win rate > 55% on Gate A, win rate >= 60% and avg raw diff > 0 on fresh holdout, no invalid/timeout, no one-seat collapse.

Diagnostic note:
- Do not trust ad hoc same-process replay scripts for final win/loss; use `test_local.py` JSONL as source of truth.
## 2026-06-06 Loop 014: Seat-Adaptive Defense

Base: `main.py`.

Hypothesis:
- Gate200 diagnostics showed loop012 clamp-only was strong on seat0 and weak on seat1, while loop010 defense knobs were weak on seat0 and strong on seat1.
- Combine them: use main defense for player 0, C02 defense knobs for player 1, and add commit clamp.

Candidate:
- `candidates/loop_014_seat_adaptive_defense.py`.

Benchmarks versus `main.py`, seed 200-204 both seats:
- 4/10 wins, avg raw diff negative on both seats.
- invalid/timeout 0.

Decision:
- Reject. The seat-specific combination does not preserve the isolated strengths and likely creates interaction effects.
- Do not use player-id adaptive defense without more direct replay evidence.
## 2026-06-06 Loop 015: Main Effective Garrison Grouping

Base: `main.py`.

Hypothesis:
- `effective_garrison_at_arrival()` should group same-ETA arrivals and call `_resolve_combat()`, matching the already-grouped `predict_defender_at_arrival()` helper.

Candidate:
- `candidates/loop_015_main_effective_garrison_grouped.py`.

Reviewer notes:
- This is a valid minimum rule-consistency test.
- Keep existing 2P/4P own-fleet inclusion policy to avoid mixing hypotheses.
- Watch raw 0 collapses and redundant follow-up into targets already won by friendly fleets.

Benchmarks versus `main.py`, Gate A seed 200-209 both seats:
- 10/20 wins, avg raw slightly positive.
- seat0 6/10, seat1 4/10.
- invalid/timeout 0.

Decision:
- Reject for champion promotion. Rule-consistent but not a win-rate improvement.
- Keep as a possible future merge only if combined with ownership-aware `effective_needed_to_capture()`.
## 2026-06-06 Loop 016: Owner-Aware Effective Needed

Base: `candidates/loop_015_main_effective_garrison_grouped.py`.

Hypothesis:
- If existing projected arrivals already make a target ours, `effective_needed_to_capture()` should return 0 to avoid redundant follow-up.

Candidate:
- `candidates/loop_016_main_owner_aware_needed.py`.

Benchmarks versus `main.py`, Gate A seed 200-204 both seats:
- 3/10 wins, strongly negative raw.
- invalid/timeout 0.

Decision:
- Reject early. Returning 0 likely suppresses useful reinforcement/follow-up or target locking in cases where ownership at projection is not enough to hold.
## 2026-06-06 Loop 017: Grouped Projection + Evac 1.10

Base: `candidates/loop_015_main_effective_garrison_grouped.py`.

Hypothesis:
- `PREEMPTIVE_EVAC_DOOM_RATIO=1.10` was useful in C02-derived candidates, but bad alone on main.py. Test whether it becomes useful when target projection is more consistent.

Candidate:
- `candidates/loop_017_grouped_evac110.py`.

Benchmarks versus `main.py`, Gate A seed 200-204 both seats:
- 3/10 wins, strongly negative raw.
- invalid/timeout 0.

Decision:
- Reject. Evac 1.10 is not useful against main.py in this gate, even with grouped target projection.
- Current working champion remains reset `candidates/champion_current.py` = `main.py`.
## 2026-06-06 Loop 018/019: Defense Knob Single Ablations

Base: `main.py`.

Hypothesis:
- Loop010's effective defense changes are mostly `DEFENSE_OVERSEND_2P=0` and `ABSORB_MIN_THREAT=5` because `DEFENSE_COALITION_MAX` is currently inert.

Candidates:
- `candidates/loop_018_main_defense_oversend0.py`: `DEFENSE_OVERSEND_2P=0` only.
- `candidates/loop_019_main_absorb5.py`: `ABSORB_MIN_THREAT=5` only.

Reviewer notes:
- `ABSORB_MIN_THREAT` is the cleaner knob.
- `DEFENSE_OVERSEND_2P=0` can admit `avail == deficit` sources and then send `deficit + 1`, increasing internal overcommit risk.

Benchmarks versus `main.py`:
- Loop018 Gate A seed 200-209 both seats: 9/20 wins, avg raw negative. Reject.
- Loop019 Gate A seed 200-209 both seats: 12/20 wins, avg raw negative. Borderline but not promotable.
- Loop019 fresh holdout seed 300-304 both seats: 4/10 wins, seat0 collapse. Reject.

Decision:
- No champion promotion.
- `ABSORB_MIN_THREAT=5` is the cleanest useful idea but does not generalize enough by itself.
## 2026-06-06 Loop 020: Drop Over-Budget Commits

Base: `main.py`.

Hypothesis:
- Previous clamp-only changed ship count without re-aiming, causing speed/ETA mismatch. Instead, drop an over-budget `_commit_fleet()` attempt and leave valid commits unchanged.

Reviewer notes:
- Drop-only is cleaner than clamp because it avoids angle/ETA mismatch.
- Callers ignore the return value, so some higher-level code may mark a mission as fired even if the over-budget commit was dropped.
- Watch raw=0 collapse and partial hammer/coalition/multiprong attacks.

Candidate:
- `candidates/loop_020_main_commit_drop_overbudget.py`.

Benchmarks versus `main.py`:
- Gate A seed 200-209 both seats: 14/20 wins, avg raw strongly positive, invalid/timeout 0. Passed gate.
- Fresh holdout seed 300-309 both seats: 7/20 wins, avg raw strongly negative, seat1 collapse. Failed promotion.

Decision:
- Reject for champion promotion despite strong Gate A result.
- This is another seed-band overfit; do not adopt until caller return-value semantics are fixed or diagnostics show which drops are beneficial.
- Current champion remains `main.py`.

## 2026-06-06 Loop 021: Return-Aware Drop Over-Budget Commits

Base: `main.py`.

Hypothesis:
- Loop020's drop-overbudget idea was physically cleaner than clamp because it never changes ship count after aim.
- The failure mode was caller state: callers marked defense/evac/hammer/multiprong as successful even when `_commit_fleet()` dropped the move.
- Fix `_commit_fleet()` to return `False` on over-budget and update success state only after `True`. Multi-fleet missions preflight source budgets with all-or-nothing checks.

Reviewer notes:
- Direction is aligned with prior physics findings.
- Must update solo defense, defense coalition, doom evac, coalition expand, hammer, multiprong, and lower-risk single-fleet call sites.
- Post-implementation review found two hammer-specific issues: partial persistent hammer if a scheduled launch later lacks ships, and hammer trim changing speed/ETA without rebuilding the plan. Both were patched inside the candidate.

Candidate:
- `candidates/loop_021_commit_drop_return_aware.py`.

Benchmarks versus `main.py`:
- Smoke random/starter: passed both seats, invalid/timeout 0.
- Gate A seed 200-209 both seats: 17/20 wins, avg raw +2558.1, invalid/timeout 0.
- Fresh holdout seed 300-319 both seats: 25/40 wins, avg raw +738.4, invalid/timeout 0.
- Seat split on holdout: seat0 15/20 avg raw +1765.8, seat1 10/20 avg raw -289.1.

Action audit, 2P games=3 turns=60:
- `main.py`: underpowered 33, likely_miss 13, hits_nothing 13, wrong_planet 8, sun 0.
- Loop021: underpowered 14, likely_miss 9, hits_nothing 10, wrong_planet 23, sun 2.

Decision:
- Reject for champion promotion.
- Winrate and raw improved versus Loop020 and it is the best non-promoted 2P diagnostic so far, but it violates the audit guardrail by increasing `static_path_hits_sun` and `static_path_hits_wrong_planet`.
- Current champion remains `main.py` / `candidates/champion_current.py`.
- Next isolate the hammer physical fix from the over-budget drop mechanism, because the audit regression may come from changing which late/hammer moves fire rather than from the hammer ETA correction itself.

## 2026-06-06 Loop 022: Hammer Physics Only

Base: `main.py`.

Hypothesis:
- Isolate Loop021's hammer-specific physical corrections without generic over-budget drop.
- Fix two known hammer issues: post-trim ship count must be re-aimed and re-scored; scheduled hammer launches should not partially proceed if a due contributor cannot fire.

Candidate:
- `candidates/loop_022_hammer_physics_only.py`.

Reviewer notes:
- Clean diagnostic ablation because `_commit_fleet()` remains unchanged and only `handle_hammer()` / `_build_hammer_plan()` are touched.
- Main risk is future staggered hammer contributors: due launches are preflighted, but earlier fleets can already be in flight if a later contributor fails.
- Reviewer quick audit warned that wrong-planet/sun findings may worsen, so kill-gate before full holdout.

Benchmarks versus `main.py`:
- Smoke random/starter: passed both seats, invalid/timeout 0.
- Kill gate seed 200-204 both seats: 5/10 wins, avg raw roughly negative overall; seat0 3/5 avg raw +905.0, seat1 2/5 avg raw -1149.6.

Decision:
- Reject early. The hammer physics correction is intuitively cleaner but does not improve direct play against `main.py` and shows seat instability.
- Do not merge hammer re-aim by itself. If revisited, first instrument hammer frequency/capture success instead of changing aggregate policy blind.

## 2026-06-06 Loop 023: Commit Guard Trace

Base: `main.py`.

Hypothesis:
- The action audit reports sun/wrong-planet shots, but the audit uses static current-position inference while the agent aims at moving future positions.
- Before adding any drop guard, instrument committed `target_id` versus physics-aware first hit to identify safe guard conditions.

Candidate:
- `candidates/loop_023_commit_guard_trace.py`.
- Behavior-preserving when `ORBIT_GUARD_TRACE` is unset.
- With `ORBIT_GUARD_TRACE`, `_commit_fleet()` logs predicted sun hits and `fleet_target_planet()` first-target mismatches, including target owner/static and first-hit owner/static.

Reviewer notes:
- Broad final guard is too risky because static wrong-planet checks can kill valid moving-target lead shots.
- Safe first implementation should avoid silent `_commit_fleet()` drops.
- Prefer mode-local rejection before commit, using committed `target_id`; never infer target from angle.

Trace findings:
- One seed pair produced 156 first-target mismatches, no predicted sun hits.
- Five seed pairs produced 916 first-target mismatches, no predicted sun hits.
- Many mismatches involve friendly targets or friendly first hits. A broad drop would damage defense/evac/accumulator and is not safe.
- A plausible narrow condition exists: non-friendly solo capture aimed at enemy/neutral, but physics-aware first hit is our own planet before the target.

Decision:
- Keep Loop023 as instrumentation only, not a submission candidate.
- Next test Loop024: add an own-planet blocker rejection inside `plan_solo_capture()` only, so no `_commit_fleet()` return semantics are needed and friendly-target moves are untouched.

## 2026-06-06 Loop 024: Solo Own-Planet Blocker Filter

Base: `main.py`.

Hypothesis:
- Broad commit-time path guards are unsafe, but `plan_solo_capture()` can safely reject a non-friendly solo capture if the physics-aware first hit is one of our own planets before the intended target.
- This avoids silent `_commit_fleet()` drops and leaves defense, evac, hammer, accumulator, and multiprong untouched.

Candidate:
- `candidates/loop_024_solo_own_blocker_filter.py`.

Reviewer notes:
- Clean and low-risk as a scoped experiment.
- Watch comets because `aim_at_target()` is comet-aware but `fleet_target_planet()` is static/orbital.
- Watch early neutral tempo and counter-snipe regressions.

Action audit:
- 2P games=3 turns=60: improved versus `main.py` on likely miss, hits-nothing, wrong-planet, and underpowered counts in the sampled run.
- 4P games=3 turns=60: improved versus `main.py` on underpowered, wrong-planet, and sun counts in the sampled run.

Benchmarks versus `main.py`:
- Smoke random/starter: passed both seats, invalid/timeout 0.
- Gate A seed 200-209 both seats: 9/20 wins, avg raw -244.1, invalid/timeout 0. Seat0 5/10 avg raw -214.9; seat1 4/10 avg raw -273.3.

Decision:
- Reject for champion promotion despite cleaner action audit.
- Important finding: reducing apparent wrong-planet/underpowered audit findings can reduce attack tempo enough to lose to `main.py`.
- If revisited, use a less aggressive version: only reject when target is neutral and first hit is our own planet with very low strategic value, or convert the shot to the first-hit target intentionally instead of dropping it.

## 2026-06-06 Loop 025: Neutral-Only Own-Planet Blocker Filter

Base: `candidates/loop_024_solo_own_blocker_filter.py`.

Hypothesis:
- Loop024 likely over-filtered enemy pressure. Keep enemy attacks untouched and reject own-planet blockers only for neutral solo captures.

Candidate:
- `candidates/loop_025_neutral_own_blocker_filter.py`.

Reviewer notes:
- Sensible narrower ablation.
- Watch neutral tempo, map/seat sensitivity, and false positives around moving targets/comets.

Action audit:
- 2P sample retained some improvement on wrong-planet/underpowered versus `main.py`, but likely-miss and hits-nothing increased in the sampled run.

Benchmarks versus `main.py`:
- Smoke random/starter: passed both seats, invalid/timeout 0.
- Gate A seed 200-209 both seats: 6/20 wins, avg raw strongly negative.
- Seat split: seat0 6/10 avg raw +807.7; seat1 0/10 avg raw -3845.9.

Decision:
- Reject hard. The neutral-only guard causes complete seat1 collapse on Gate A.
- Close the own-blocker drop family for now. The audit metric is useful as a smell, but directly dropping these shots removes too much tempo/staging value.

## 2026-06-06 Loop 026: Seat1 Main Commit Behavior Diagnostic

Base: `candidates/loop_021_commit_drop_return_aware.py`.

Hypothesis:
- Loop021 is the strongest non-promoted candidate so far but has holdout seat1 weakness and action-audit regression.
- As a diagnostic only, disable the over-budget drop on 2P player/seat 1 to see whether seat1 weakness is caused by the drop mechanism.

Candidate:
- `candidates/loop_026_seat1_main_commit_behavior.py`.

Reviewer notes:
- Test only as a diagnostic; reject as promotion candidate unless it yields a non-seat-specific explanation.
- Seat-specific logic can mask rather than explain the mechanism, and player0 audit regression likely remains.

Benchmarks versus `main.py`:
- Smoke random/starter: passed both seats, invalid/timeout 0.
- Gate A seed 200-209 both seats: 13/20 wins, avg raw positive but below Loop021.
- Seat split: seat0 7/10 avg raw +1611.8; seat1 6/10 avg raw +1104.1.

Decision:
- Reject. Seat1 improves versus Loop021 holdout symptoms, but Gate A overall drops from Loop021's 17/20 to 13/20 and does not clear the diagnostic threshold.
- Do not use seat-specific bypass as a path to submission.
- Current champion remains `main.py` / `candidates/champion_current.py`.

## 2026-06-06 Current Champion Checkpoint

Champion:
- `main.py` and `candidates/champion_current.py` are byte-identical.
- No loop candidate from 021-026 is promoted.

Best rejected diagnostic:
- `candidates/loop_021_commit_drop_return_aware.py`.
- It has the strongest direct 2P numbers so far: Gate A 17/20, holdout 25/40, avg raw positive.
- It is still not acceptable because holdout seat1 is only 10/20 with negative avg raw and action audit worsens `static_path_hits_sun` / `static_path_hits_wrong_planet`.

Lessons from 021-026:
- Generic over-budget drop is promising but must not be adopted until the audit regression is explained or bounded.
- Cleaner physics is not automatically stronger: hammer re-aim and own-blocker filters reduced obvious smells but lost games.
- Action audit is a guardrail, not the score function. Dropping every suspicious shot can remove useful tempo/staging.
- Seat-specific bypasses are diagnostic only; they are not a robust submission path.

Next high-value directions:
- Instrument mode-level outcomes instead of dropping moves: count expansions, enemy attacks, hammer launches, successful captures, and raw=0 collapses by seed/seat.
- For Loop021, identify which modes create the new sun/wrong-planet audit findings. If concentrated in hammer/multiprong/late flush, gate only that mode rather than `_commit_fleet()` globally.
- Explore non-dropping repair: if a solo shot would first hit another planet, evaluate intentionally targeting the first-hit planet only when it is neutral/enemy and capture math is favorable.
- Revisit defense over-absorption with a budget floor rather than path filters, because the original weakness was "対応に吸収される" and path filtering mostly hurt tempo.

## 2026-06-06 Loop 027: Mode-Level Trace Attribution

Base:
- `candidates/loop_027a_main_mode_trace.py` from `main.py`.
- `candidates/loop_027b_loop021_mode_trace.py` from `candidates/loop_021_commit_drop_return_aware.py`.

Hypothesis:
- Before changing behavior again, attribute suspicious geometry to action modes.
- Use committed `target_id`, not static angle-inferred target, to distinguish real target mismatch/sun issues from review script false positives.

Implementation:
- `_commit_fleet()` accepts keyword-only `mode_label`.
- Trace helper writes JSONL only when `ORBIT_MODE_TRACE` is set.
- Default is suspicious-only logging: `first_target_mismatch`, predicted sun, overbudget, dropped commit, or unknown mode. `ORBIT_MODE_TRACE_ALL=1` enables all commits.
- `tools/summarize_mode_trace.py` aggregates reason x mode, relation, player/seat, and top repeated patterns.

Reviewer notes:
- Compare main-trace and Loop021-trace with the same schema.
- Use JSONL and fail if any `mode_label="unknown"` remains.
- Suspicious-only default is preferable because full trace I/O perturbs `plan_moves()` wall-clock deadline behavior.

Verification:
- `python -m py_compile` passed for both trace candidates and summarizer.
- Smoke versus random passed for both trace candidates with trace disabled.
- Trace enabled on seed 200 and seed 200-204 produced valid JSONL and `unknown_mode=0`.

Trace findings, seed 200-204 both seats versus `main.py`:
- Main trace suspicious rows: 857, all `first_target_mismatch`, no target-id predicted sun.
- Loop021 trace suspicious rows: 544, all `first_target_mismatch`, no target-id predicted sun.
- Main top modes: `doom-evac-friendly` 507, `search-expand` 204, `hammer` 109.
- Loop021 top modes: `doom-evac-friendly` 260, `search-expand` 139, `hammer` 121.
- Doom evac mismatches are mostly friendly evacuation (`own->own`, `own->enemy`, `own->neutral`) and likely not the audit problem to fix first.
- The actionable suspicious modes are `search-expand` and `hammer`, especially `enemy->own` first hits.

Decision:
- Keep Loop027 as diagnostic tooling.
- Treat `static_path_hits_sun` from `review_action_accuracy.py` as a weak signal unless confirmed by target-id trace; this run found no target-id predicted sun hits.
- Next ablation should avoid broad path dropping. Ask review whether to test Loop021 with hammer disabled/gated, or a narrower search-expand repair.

## 2026-06-06 Loop 028: Loop021 Without Routine Hammer

Base: `candidates/loop_021_commit_drop_return_aware.py`.

Hypothesis:
- Loop027 showed Loop021 suspicious mismatches in `hammer` and `search-expand`.
- Prior own-blocker filters on expansion/search destroyed tempo, so test the cleaner one-toggle ablation first: disable routine hammer only.

Candidate:
- `candidates/loop_028_loop021_no_routine_hammer.py`.
- Only change from Loop021: `HAMMER_ENABLED = False`.
- `MEGA_HAMMER_ENABLED`, `SEARCH_EXPAND_*`, and `MULTIPRONG_ENABLED` remain unchanged.

Reviewer notes:
- Prefer hammer-off before touching search-expand.
- Do not enable multiprong; it is already disabled and enabling it would confound the ablation.
- Continue only if the short kill gate is not an obvious collapse.

Benchmarks versus `main.py`:
- Smoke random: passed both seats, invalid/timeout 0.
- Kill gate seed 200-204 both seats: 5/10 wins. Seat0 3/5 avg raw +678.8; seat1 2/5 avg raw +35.2.

Decision:
- Reject early. Routine hammer contributes suspicious first-hit mismatches, but disabling it removes too much strength and does not approach Loop021's same-band 9/10.
- Hammer should not be globally disabled. If revisited, gate only specific hammer risk cases while preserving normal hammer pressure.

## 2026-06-06 Loop 029: Loop021 Hammer Own-Blocker Cancel

Base: `candidates/loop_021_commit_drop_return_aware.py`.

Hypothesis:
- Loop028 proved hammer is needed, but Loop027 showed hammer `enemy->own` first-target mismatches.
- Keep hammer enabled, but when a due hammer launch would first hit our own planet before the intended hammer target, cancel the whole hammer plan instead of partially skipping a contributor.

Candidate:
- `candidates/loop_029_loop021_hammer_own_blocker_cancel.py`.
- Scope limited to `handle_hammer()` due-launch path. No generic `_commit_fleet()` or `search-expand` changes.

Reviewer notes:
- Cancel the whole plan, not one launch, because hammer assumes synchronized committed strength.
- This is the safer hammer-specific ablation after Loop028.

Benchmarks versus `main.py`:
- Smoke random/starter: passed both seats, invalid/timeout 0.
- Kill gate seed 200-204 both seats: 4/10 wins. Seat0 1/5 avg raw -1347.6; seat1 3/5 avg raw +522.6.

Decision:
- Reject early. The guard cancels too many useful hammer plans and is worse than Loop028.
- Do not use own-first blocker cancellation for hammer. The first-hit mismatch may be a noisy proxy for useful hammer pressure rather than a clean bug.

## 2026-06-06 Loop 030: Loop021 + Absorb Min Threat 5

Base: `candidates/loop_021_commit_drop_return_aware.py`.

Hypothesis:
- Return to the original weakness: "対応に吸収されて終わる".
- Combine Loop021's strong commit accounting with `ABSORB_MIN_THREAT=5` to ignore more small hostile arrivals and free ships for pressure.

Candidate:
- `candidates/loop_030_loop021_absorb5.py`.
- Only change from Loop021: `ABSORB_MIN_THREAT = 5`.

Reviewer notes:
- Sensible diagnostic because the knobs are mechanically independent.
- Risk: combines Loop019's holdout seat0 collapse with Loop021's holdout seat1 weakness and may overfeed search/hammer pressure.

Benchmarks versus `main.py`:
- Smoke random: passed both seats, invalid/timeout 0.
- Kill gate seed 200-204 both seats: 5/10 wins. Seat0 3/5 avg raw +405.2; seat1 2/5 avg raw -397.2.

Decision:
- Reject early. `ABSORB_MIN_THREAT=5` breaks Loop021's short-gate strength and does not solve the defense-overabsorption problem in this combination.
- Do not combine higher absorb threshold with Loop021 without a more targeted under-defense diagnostic.

## 2026-06-07 Turn Metrics Diagnostic

Tools:
- `tools/analyze_turn_metrics.py`: runs games and emits per-game summary JSONL plus per-turn metrics JSONL.
- `tools/summarize_turn_metrics.py`: summarizes failure buckets, seat split, turn snapshots, and largest launch turns.

Metrics captured:
- Owned planets, production, planet ships, fleet ships, raw total, raw diff, production diff.
- Fleet/raw ratio, active fleets, action-derived launches and launched ships.
- First marker turns for raw diff below -500/-1000, production share below 0.40, zero owned planets/production, and first large launch.

Loop021 holdout seed 300-319 both seats versus `main.py`:
- 26/40 wins in this run, 14 raw-zero losses.
- All losses classified as `overcommit-collapse`.
- Seat0: 15/20 wins, 5 raw-zero losses, avg raw diff +1952.8.
- Seat1: 11/20 wins, 9 raw-zero losses, avg raw diff +141.2.
- Losses are not early expansion failures: by turn 80 many are raw/prod even or ahead.
- Loss trajectory: fleet/raw ratio is often 0.65-0.80 around turn 80-100, then production collapses by turn 140.

Comparison with `main.py` same seed band:
- `main.py` self-comparison has mixed `overcommit-collapse` and `midgame-defense-drain` buckets.
- Loop021 losses cross production-share danger much earlier: average first prod share <0.40 around turn 105, versus `main.py` losses around turn 194-221 in this diagnostic run.

Interpretation:
- Loop021's failing seeds are mostly midgame overcommit followed by production-planet loss.
- The failure is not solved by path filtering, hammer removal, or absorb-threshold changes.
- A useful fix likely needs to prevent the overcommit before the production-share cliff, not after collapse is already underway.

## 2026-06-07 Loop 031: Loop021 Midgame Overcommit Brake

Base: `candidates/loop_021_commit_drop_return_aware.py`.

Hypothesis:
- Turn metrics show Loop021 losses often have high fleet/raw ratio around turn 80-100 while raw/prod is still close.
- Add a narrow 2P midgame pressure brake: when fleet/raw >= 0.75, production is not clearly ahead, and raw is not clearly ahead, skip new expand, new hammer creation, and multiprong for that turn. Keep defense/evac and existing hammer-plan launches.

Candidate:
- `candidates/loop_031_loop021_overcommit_brake.py`.

Reviewer notes:
- Use a narrow conditional brake, not broad hammer removal.
- Start with threshold 0.75 and raw margin <=150.
- Do not clear existing hammer plan.

Benchmarks versus `main.py`:
- Smoke random/starter: passed both seats, invalid/timeout 0.
- Kill gate seed 200-204 both seats: 5/10 wins. Seat0 2/5 avg raw +318.2; seat1 3/5 avg raw +1033.8.

Brake trace:
- `ORBIT_BRAKE_TRACE` on seed 200-204 produced many brake events.
- Many events fired after raw/prod was already strongly negative, e.g. raw_diff below -500 and prod_diff below -30.

Decision:
- Reject early. The brake activates, but mostly after the collapse is already in progress and it reduces Loop021's short-gate strength.
- Future fixes should target the pre-collapse trigger, not a late offensive pause after fleet/raw is already extreme.

## 2026-06-07 Pre-Cliff Mode Trace Diagnostic

Tools:
- Added `tools/run_mode_trace_games.py`.
- Existing mode traces did not include `seed` or `tested_seat`; the new runner executes selected games one at a time, writes a fresh `ORBIT_MODE_TRACE` file per game, annotates every trace row with game keys, and emits same-run summary/turn JSONL.
- Added/used `tools/summarize_precliff_modes.py` to compare committed mode volume before `first_prod_share_lt_40`.

Reviewer notes:
- Use `ORBIT_MODE_TRACE_ALL=1`; suspicious-only trace is not valid for launch-volume attribution.
- Use same-run summary because full trace I/O can perturb time-sensitive action choices.
- Compare fixed early windows and per-game averages; no-cliff wins otherwise contribute full-game volume.

Findings:
- Representative Loop021 trace sample first showed no clean hammer-only overuse. In fixed 0-100/120T windows, losses had more `doom-evac-friendly`, while prior broad hammer/search removals already collapsed strength.
- ETA distribution did not support a simple `DOOM_EVAC_MAX_TRAVEL` reduction: loss and win doom-evac ETA distributions were similar.
- Updated diagnostic-only `candidates/loop_027b_loop021_mode_trace.py` to split labels:
  - `doom-evac-preemptive-friendly`
  - `doom-evac-fallback-friendly`
  - corresponding attack labels.
- Split trace showed the loss-side excess is mostly preemptive friendly evacuation, not fallback. In the representative same-run sample:
  - 0-100T: `doom-evac-preemptive-friendly` loss avg about 682 ships vs win avg about 359.
  - 0-120T: loss avg about 1120 vs win avg about 617.
  - `doom-evac-fallback-friendly` was much smaller.

Decision:
- Do not touch search/hammer again from this evidence.
- Do not reduce `DOOM_EVAC_MAX_TRAVEL` yet; long-distance evac was not loss-specific.
- Test only the preemptive doom ratio as a narrow behavior probe, then stop scalar ratio tuning if it cannot preserve Loop021's short-gate strength.

## 2026-06-07 Loop 032: Preemptive Evac Ratio 1.50

Base: `candidates/loop_021_commit_drop_return_aware.py`.

Hypothesis:
- Preemptive doom evac fires before solo/coalition rescue and sends the full garrison.
- `PREEMPTIVE_EVAC_DOOM_RATIO = 1.20` is too low for a decision that skips rescue and empties a planet.

Candidate:
- `candidates/loop_032_preemptive_evac_ratio150.py`.
- Only behavior change: `PREEMPTIVE_EVAC_DOOM_RATIO = 1.50`.

Reviewer notes:
- Direction is right as a narrow probe.
- `1.50` is preferred over `1.35` for the first causal test because false negatives are less dangerous than false positives while fallback doom evac remains available.

Benchmarks versus `main.py`:
- Smoke random/starter: passed both seats, invalid/timeout 0.
- Kill gate seed 200-204 both seats: 6/10 wins, avg raw diff about +488, invalid/timeout 0.

Decision:
- Reject early. It is better than the recent 4-5/10 broad probes, but far below Loop021's same-band strength.
- `1.50` likely suppresses too much useful preemptive evacuation.

## 2026-06-07 Loop 033: Preemptive Evac Ratio 1.35

Base: `candidates/loop_021_commit_drop_return_aware.py`.

Hypothesis:
- `1.35` may reduce premature preemptive evacuation while restoring enough of Loop021's useful saves.
- Treat as the last cheap ratio-only probe.

Candidate:
- `candidates/loop_033_preemptive_evac_ratio135.py`.
- Only behavior change: `PREEMPTIVE_EVAC_DOOM_RATIO = 1.35`.

Reviewer notes:
- Proceed, but promotion bar is close to Loop021's short-gate result. If it lands below about 8/10 or has weak raw, abandon ratio-only tuning.

Benchmarks versus `main.py`:
- Smoke random/starter: passed both seats, invalid/timeout 0.
- Short gate seed 200-204 both seats: 8/10 wins, avg raw positive, invalid/timeout 0.
- Full Gate A seed 200-209 both seats: 13/20 wins.
  - Seat0: 7/10, avg raw diff +1128.9.
  - Seat1: 6/10, avg raw diff +577.9.

Decision:
- Reject. `1.35` recovers part of the short gate but does not approach Loop021's 17/20 Gate A shape and does not solve seat stability.
- Stop scalar `PREEMPTIVE_EVAC_DOOM_RATIO` tuning. The evidence says aggressive preemptive evacuation is coupled to Loop021's strength; a future fix needs a narrower trigger, likely limiting `threat_metric` to arrivals inside the actual deadline/window or adding a value-aware preemptive evac condition.
- Current champion remains `main.py` / `candidates/champion_current.py`.

## 2026-06-07 Loop 034: Windowed Preemptive Threat

Base: `candidates/loop_021_commit_drop_return_aware.py`.

Hypothesis:
- The preemptive doom trigger sums all enemy arrivals but compares against `garrison_at_deadline` for a finite `deadline`/default window.
- This can mark a planet doomed too early and fire full-garrison friendly evacuation before solo/coalition rescue.
- Keep `PREEMPTIVE_EVAC_DOOM_RATIO = 1.20`, but in 2P sum only enemy arrivals with `eta <= window` for the preemptive threat metric.

Candidate:
- `candidates/loop_034_preemptive_windowed_threat.py`.
- Scope: 2P preemptive threat calculation only.
- Fallback doom evac, defense, search, hammer, commit accounting, and 4P semantics unchanged.

Reviewer notes:
- This is a cleaner fix than scalar ratio tuning because it addresses an apples-to-window comparison.
- Main risk: late stacked arrivals beyond the first defense deadline are excluded, so the agent may attempt rescue when long-tail pressure still dooms the planet.

Benchmarks versus `main.py`:
- Smoke random/starter: passed both seats, invalid/timeout 0.
- Short gate seed 200-204 both seats: 5/10 wins.
  - Seat0: 3/5, avg raw diff +969.8.
  - Seat1: 2/5, avg raw diff +81.2.

Decision:
- Reject early. The implementation is mechanically safe, but it removes too much useful preemptive evacuation and repeats the 5/10 failure pattern.
- Do not continue with coarse preemptive suppression. If revisiting this family, use a value-aware condition rather than arrival-window or scalar suppression: only preemptively evacuate when the victim is low production/low strategic value, or when rescue cannot preserve a production lead.
- Current champion remains `main.py` / `candidates/champion_current.py`.

## 2026-06-07 Loop 035: Core-Value Preemptive Evac

Base: `candidates/loop_021_commit_drop_return_aware.py`.

Hypothesis:
- Broad preemptive suppression fails because preemptive evac is globally useful.
- Limit only high-value/core planet preemptive evacuation:
  - Non-core planets keep `PREEMPTIVE_EVAC_DOOM_RATIO = 1.20`.
  - Core victims use ratio `1.75`.
  - Core definition: production >= 3, or production >= 2 and in the top two currently owned production values.
- If normal defense later fails, fallback doom evac remains unchanged.

Candidate:
- `candidates/loop_035_core_value_preemptive_evac.py`.
- Scope: preemptive block in `handle_defense()` only.
- No `_try_doom_evac`, hammer, search, path, or commit accounting changes.

Reviewer notes:
- This is more promising than pressure-budget changes because prior broad search/hammer changes underperformed.
- Promotion bar should be close to Loop021: short gate at least 8/10, full Gate A near 17/20, then holdout.

Benchmarks versus `main.py`:
- Smoke random/starter: passed both seats, invalid/timeout 0.
- Short gate seed 200-204 both seats: 6/10 wins.
  - Seat0: 3/5, avg raw diff +89.4.
  - Seat1: 3/5, avg raw diff +910.6.

Decision:
- Reject early. Value-aware core suppression is still too disruptive and does not clear the short-gate bar.
- Stop preemptive-evac suppression family for now. The evidence suggests Loop021 depends heavily on aggressive preemptive evacuation; fixing collapse likely needs either richer tactical simulation around the evac decision or a different lever.
- Next recommended family: trace-only budget/pressure attribution for hammer/multiprong after turn 80, preserving search-expand first.
- Current champion remains `main.py` / `candidates/champion_current.py`.

## 2026-06-07 Post-80 Pressure Mode Diagnostic

Tools:
- Added `tools/summarize_pressure_modes.py`.
- Joins mode trace rows to same-run turn metrics by `(seed, tested_seat, turn)`.
- Reports fixed windows `80-100` and `80-120`, stopping at `first_prod_share_lt_40`.
- Buckets by fleet/raw ratio, production diff, raw diff, mode, and outcome.

Reviewer notes:
- `MULTIPRONG_ENABLED = False` in Loop021, so multiprong should remain a zero-count invariant, not a candidate to enable.
- `MEGA_HAMMER_4P_ONLY = True`, so 2P Loop021-vs-main should expect `hammer`, not `mega-hammer`.
- Use `ORBIT_MODE_TRACE_ALL=1` and same-run summaries; suspicious-only or separate-run summaries are not valid for volume attribution.

Diagnostic runs:
- Existing representative split trace sample: `eval_results/precliff_loop021_split_*`.
- Larger same-run split trace sample: seed 300-309 both seats:
  - `eval_results/pressure_loop021_split_trace_300_309.jsonl`
  - `eval_results/pressure_loop021_split_summary_300_309.jsonl`
  - `eval_results/pressure_loop021_split_turns_300_309.jsonl`

Findings:
- Hammer is not clearly loss-biased in 2P. Winning cases often have larger `hammer` and `search-expand` volume when `production_diff >= 5`, which looks like useful conversion of a production lead.
- Losing cases show more `search-expand` volume in flat/bad pressure states, especially fleet-heavy with `production_diff <= 0`.
- This supports testing a narrow search-expand pressure gate, not a hammer gate.

## 2026-06-07 Loop 036: Search-Expand Pressure Gate

Base: `candidates/loop_021_commit_drop_return_aware.py`.

Hypothesis:
- Prior search path/own-blocker filters were destructive, but they targeted geometry.
- This candidate preserves normal expansion and all hammer/defense/evac behavior, and only skips the search-based expansion pre-pass in a bad 2P pressure state:
  - `world.step >= 80`
  - fleet/raw ratio >= 0.65
  - production diff <= 0
  - raw diff <= 0

Candidate:
- `candidates/loop_036_search_pressure_gate.py`.
- Scope: `handle_expand()` search pre-pass only.
- `handle_expand()` normal solo/coalition expansion still runs.
- Hammer, mega-hammer, defense, evac, search scoring, and commit accounting unchanged.

Reviewer notes:
- Use `raw_diff <= 0`, not `<500`, to avoid clipping more winning search volume.
- Pass target split only if seed300-309 improves raw-zero collapses and raw diff.
- Pass Gate A only if near Loop021: at least 16/20 and avg raw >= +2000.

Benchmarks versus `main.py`:
- Smoke random/starter: passed both seats after fixing the local helper to derive enemy owners from `owner_production`.
- Target split seed 300-309 both seats:
  - 13/20 wins, avg raw diff +626.1, raw-zero losses 7.
  - Seat0: 6/10, avg raw +382.2.
  - Seat1: 7/10, avg raw +870.1.
- Gate A seed 200-209 both seats:
  - 11/20 wins, avg raw diff +569.4, raw-zero losses 9.
  - Seat0: 4/10, avg raw -496.4.
  - Seat1: 7/10, avg raw +1635.2.

Decision:
- Reject for champion promotion.
- The pressure gate improves the target diagnostic band, but it breaks Gate A, especially seat0.
- Do not use this exact search-expand gate. If revisiting search pressure, it needs a less disruptive condition, likely requiring a stronger bad-state signal than `prod<=0/raw<=0` or applying only after a confirmed production-share decline.
- Current champion remains `main.py` / `candidates/champion_current.py`.

## 2026-06-07 Loop 037: Search-Skip Attribution Diagnostic

Base:
- `candidates/loop_037_search_skip_trace.py` from Loop036.

Purpose:
- Diagnostic only. Keep Loop036 behavior, but log every skipped search-expand pre-pass to `ORBIT_SEARCH_SKIP_TRACE`.
- Added `tools/run_search_skip_trace_games.py` to execute one game at a time and annotate skip rows with `seed` and `tested_seat`.

Reviewer notes:
- Do not create another scalar pressure gate yet.
- Attribute what Loop036 skipped, especially on Gate A seeds where Loop021 won but Loop036 lost.
- Next behavior, if any, should be source/target-specific rather than mode-wide.

Diagnostics:
- Selected Gate A flips: `eval_results/loop_037_search_skip_gate200_selected.jsonl`.
- 358 skipped rows across 7 games.
- One winning selected game had 27 skip rows; losing selected games had 40-70 skip rows each.
- Top skipped actions often came from production 2-5 sources and targeted enemy/high-production planets.
- Source production distribution among top skipped actions:
  - Wins: prod1 8, prod2 7, prod3 3, prod4 5, prod5 4.
  - Losses: prod1 35, prod2 60, prod3 66, prod4 64, prod5 52.

Interpretation:
- Loop036 is too blunt because it removes many high-score conversion attacks, including useful high-production-source attacks.
- The row count is still much higher in losses, so the pressure signal is real, but not enough to justify a whole-mode skip.

## 2026-06-07 Loop 038: Source-Risk Search Gate

Base: `candidates/loop_021_commit_drop_return_aware.py`.

Hypothesis:
- Preserve search-expand globally.
- Under the same bad 2P pressure state as Loop036, skip only individual search actions where:
  - source production >= 3,
  - target is enemy, not neutral,
  - and the source is locally risky: hostile arrival within 25 turns or post-launch residual below `max(8, source.production * 5)`.

Candidate:
- `candidates/loop_038_source_risk_search_gate.py`.
- Scope: per-action skip inside `_handle_search_expand_4p()` only.
- Normal expansion, neutral search, hammer, defense, evac, and commit accounting unchanged.

Reviewer notes:
- Do not skip merely because the source is high production; high-prod sources often produce useful attacks.
- Do not skip enemy/high-prod targets by default; those are often the conversion attacks Loop036 clipped.

Benchmarks versus `main.py`:
- Smoke random/starter: passed both seats, invalid/timeout 0.
- Short gate seed 200-204 both seats: 5/10 wins.
  - Seat0: 2/5, avg raw diff -254.4.
  - Seat1: 3/5, avg raw diff +899.0.

Decision:
- Reject early. Even source-risk search gating damages short-gate strength.
- Stop search-pressure suppression family for now. The signal is diagnostic-useful but current behavior edits remove too much tempo/conversion.
- Current best non-promoted candidate remains Loop021; current champion remains `main.py` / `candidates/champion_current.py`.

## 2026-06-07 Search Source Outcome Diagnostic

Tool:
- Added `tools/analyze_search_source_outcomes.py`.
- Runs one game at a time with `ORBIT_MODE_TRACE_ALL=1`.
- Correlates committed `search-expand` rows with environment planet history.
- For each committed search action, records source/target, residual ships, production/raw pressure state, source ownership loss within 10/20/30 turns, target owner at arrival and arrival+10, and whether the target was captured/held.

Diagnostics:
- Selected Gate A flips:
  - `eval_results/search_source_outcomes_gate200_selected.jsonl`
  - `eval_results/search_source_outcomes_gate200_selected_summary.jsonl`
  - rows=1157.
  - Winning rows: source_lost20=0.387, target_capture10=0.723, avg_residual=24.4.
  - Losing rows: source_lost20=0.667, target_capture10=0.478, avg_residual=19.0.
- Target split seed 300-309 both seats:
  - `eval_results/search_source_outcomes_300_309.jsonl`
  - `eval_results/search_source_outcomes_300_309_summary.jsonl`
  - rows=3468.
  - Winning rows: source_lost20=0.355, target_capture10=0.727, avg_residual=22.7.
  - Losing rows: source_lost20=0.575, target_capture10=0.528, avg_residual=20.2.

Interpretation:
- Losing games do have more search actions where the source is lost soon and the target is not held.
- The bad rows cluster more by global collapse state than by source production/residual alone.
- However, many low-residual or high-production-source search actions still lead to useful captures in wins.
- This explains why Loop036/038 damaged strength: search-expand is both a collapse accelerant and a comeback/conversion mechanism.

## 2026-06-07 Loop 039: Tight Global Search Pressure Gate

Base: `candidates/loop_021_commit_drop_return_aware.py`.

Hypothesis:
- Test the narrowest mode-wide version of the search-pressure idea as a diagnostic ablation.
- Skip the 2P search-expand pre-pass only when:
  - `world.step >= 80`
  - fleet/raw ratio >= 0.65
  - production diff <= -5
  - raw diff <= -500

Candidate:
- `candidates/loop_039_tight_search_pressure_gate.py`.
- Scope: `handle_expand()` search pre-pass only.
- Normal expansion, hammer, defense, evac, search scoring, and commit accounting unchanged.

Reviewer notes:
- The code diff is limited to `_skip_search_expand_tight_pressure_2p()` and the `handle_expand()` condition.
- Fleet tuple access `f[1]` owner / `f[6]` ships is correct.
- 4P search behavior remains unchanged.
- Treat as a diagnostic candidate only. If short gate is below 6/10, reject and stop global search skipping.

Benchmarks versus `main.py`:
- Smoke random/starter: passed both seats, invalid/timeout 0.
- Short gate seed 200-204 both seats:
  - 3/10 wins, avg raw diff -2090.8.
  - Seat0: 3/5, avg raw diff +467.4.
  - Seat1: 0/5, avg raw diff -4183.6.

Decision:
- Reject immediately.
- Even the tight global pressure gate deletes too many useful search conversions, especially from seat1.
- Do not continue mode-wide search suppression. Future work should either:
  - improve source retention/defense budget around committed attacks, or
  - use per-action outcome proxies that preserve high-value conversions.
- Current champion remains `main.py` / `candidates/champion_current.py`.

## 2026-06-07 Loop 040: Search-Only First-Target Guard

Base: `candidates/loop_021_commit_drop_return_aware.py`.

Hypothesis:
- Stop suppressing search-expand by global pressure.
- Instead, drop only search-expand actions that clearly do not hit the intended target.
- Use existing `fleet_target_planet()` before commit, and skip when:
  - target is enemy or neutral,
  - first predicted collision is a different planet,
  - first collision occurs before planned arrival,
  - and the first collision is at least 2 turns earlier than planned arrival.

Candidate:
- `candidates/loop_040_search_first_target_guard.py`.
- Scope: `_handle_search_expand_4p()` only.
- `_commit_fleet`, doom evac, defense, accumulator, hammer, mega-hammer, and normal expand are unchanged.

Reviewer notes:
- Direction is valid after Loop036-039 because it is per-action physics, not mode-wide search suppression.
- First version should be search-expand only; hammer/expand/mega-hammer should wait.
- Blocking bug: none.
- Warning: `fleet_target_planet()` receives `world.planets`, so the source planet itself can be predicted as first target for orbital sources. If short/full evaluation worsens, first fix should allow `first.id == src_id`.

Benchmarks versus `main.py`:
- Smoke random/starter: passed both seats, invalid/timeout 0.
- Short gate seed 200-204 both seats:
  - Loop040: 6/10 wins, avg raw diff +754.4, raw-zero losses 4.
  - Same short comparison for Loop021: 5/10 wins, avg raw diff +186.8, raw-zero losses 5.
- Full Gate A seed 200-209 both seats:
  - Loop040: 10/20 wins, avg raw diff +257.3, raw-zero losses 10.
  - Seat0: 6/10, avg raw diff +993.7.
  - Seat1: 4/10, avg raw diff -479.1.
  - Loop021 reference on same full Gate A: 17/20 wins, avg raw diff +2558.1, raw-zero losses 3.

Decision:
- Reject.
- The short gate was a false positive; full Gate A shows the guard removes too many useful search conversions.
- The most likely implementation-specific false positive is source-self first collision on orbital planets.
- Next test, if continuing this family, should be Loop041: same search-only guard but explicitly allow `first.id == src_id`.
- Current champion remains `main.py` / `candidates/champion_current.py`.

## 2026-06-07 Loop 041: Search Guard Allow Source-Self

Base: `candidates/loop_040_search_first_target_guard.py`.

Hypothesis:
- Loop040 may have rejected useful search shots because `fleet_target_planet()` can identify the source planet itself as the first collision for orbital sources.
- Keep the same search-only first-target guard, but allow `first.id == src_id`.

Candidate:
- `candidates/loop_041_search_guard_allow_source.py`.
- Diff from Loop040 is one line:
  - `first.id in (src_id, target_id)` is allowed.

Reviewer notes:
- Valid diagnostic ablation after Loop040.
- Do not additionally allow all friendly first hits; another own planet can still be a real unintended blocker.
- Proceed to full Gate A only if short gate is at least 6/10 and seat1 raw does not worsen versus Loop040.

Benchmarks versus `main.py`:
- Smoke random/starter: passed both seats, invalid/timeout 0.
- Short gate seed 200-204 both seats:
  - Loop041: 6/10 wins, avg raw diff +219.8, raw-zero losses 4.
  - Seat0: 4/5, avg raw diff +1718.2.
  - Seat1: 2/5, avg raw diff -1278.6.
  - Loop040 short reference: 6/10 wins, avg raw diff +754.4, seat1 avg raw diff -264.6.
  - Loop021 short reference: 5/10 wins, avg raw diff +186.8, seat1 avg raw diff -781.6.

Decision:
- Reject early.
- Allowing source-self did not fix the seat1 regression and reduced average raw score versus Loop040.
- Stop hard first-target skip for now. If revisiting this signal, use it as a scoring penalty or trace feature, not a binary commit veto.
- Current champion remains `main.py` / `candidates/champion_current.py`.

## 2026-06-07 Loop 042: Search Mismatch Score Penalty

Base: `candidates/loop_021_commit_drop_return_aware.py`.

Hypothesis:
- Loop040/041 failed because binary search veto removed useful conversion attacks.
- Keep all search actions available, but reduce positive Melis gain when the action appears physically suspicious:
  - target is enemy or neutral,
  - first predicted collision is neither source nor intended target,
  - first collision is at least 2 turns earlier than planned arrival,
  - first owner is our own planet or neutral.
- Do not penalize a different enemy first hit, because that can still be useful pressure.

Candidate:
- `candidates/loop_042_search_mismatch_score_penalty.py`.
- Scope: `search_step_action()` positive gain only.
- Penalty: own-first factor 0.55, neutral-first factor 0.75.
- Commit, defense, evac, hammer, and normal expand unchanged.

Reviewer notes:
- Correct follow-up after hard skip failure because it changes ranking rather than availability.
- `search_step_action()` is the right insertion point.
- Multipliers may be strong; if weak, test a softer `0.65/0.80`.

Benchmarks versus `main.py`:
- Smoke random/starter: passed both seats, invalid/timeout 0.
- Short gate seed 200-204 both seats:
  - 4/10 wins, avg raw diff -1079.3.
  - Seat0: 2/5, avg raw diff -1146.4.
  - Seat1: 2/5, avg raw diff -1012.2.

Decision:
- Reject early.
- Even score-only penalty is too disruptive at `0.55/0.75`.
- Test only the reviewer-suggested softer ablation before stopping this family.

## 2026-06-07 Loop 043: Search Mismatch Soft Penalty

Base: `candidates/loop_042_search_mismatch_score_penalty.py`.

Hypothesis:
- Same as Loop042, but soften the score penalty so useful search conversions survive more often.

Candidate:
- `candidates/loop_043_search_mismatch_soft_penalty.py`.
- Diff from Loop042:
  - own-first factor 0.65.
  - neutral-first factor 0.80.

Benchmarks versus `main.py`:
- Smoke random/starter: passed both seats, invalid/timeout 0.
- Short gate seed 200-204 both seats:
  - 6/10 wins, avg raw diff +1069.3.
  - Seat0: 4/5, avg raw diff +2732.6.
  - Seat1: 2/5, avg raw diff -594.0.
- Full Gate A seed 200-209 both seats:
  - 11/20 wins, avg raw diff +334.8, raw-zero losses 9.
  - Seat0: 4/10, avg raw diff -935.3.
  - Seat1: 7/10, avg raw diff +1604.8.
  - Loop021 reference: 17/20 wins, avg raw diff +2558.1, raw-zero losses 3.

Decision:
- Reject for promotion.
- The softer penalty improves seat1 relative to several failed probes but collapses seat0 and remains far below Loop021.
- Diagnostic insight: first-target mismatch penalty has a seat-bias effect. If revisiting, make it seat/adaptive or use it only in the holdout seat1 failure profile. Do not apply it globally.
- Current champion remains `main.py` / `candidates/champion_current.py`.

## 2026-06-07 Loop 044: Seat1-Only Search Mismatch Soft Penalty

Base: `candidates/loop_043_search_mismatch_soft_penalty.py`.

Hypothesis:
- Loop043 globally hurts seat0 but leaves seat1 close to useful.
- Loop021's holdout weakness is also seat1.
- Apply the Loop043 soft mismatch penalty only in 2P seat1 (`world.player == 1`) and leave seat0/4P as Loop021.

Candidate:
- `candidates/loop_044_seat1_search_mismatch_soft_penalty.py`.
- Diff from Loop043:
  - `_search_first_target_score_factor()` returns `1.0` unless `world.is_2p and world.player == 1`.

Reviewer notes:
- Seat-specific behavior is overfit-risky but valid as a diagnostic because repeated evaluations show seat asymmetry.
- Gate A is worth running, but promotion requires near-Loop021 Gate A plus holdout seat1 improvement.
- Do not add more conditions before measuring the pure seat1-gate effect.

Benchmarks versus `main.py`:
- Smoke random/starter: passed both seats, invalid/timeout 0.
- Full Gate A seed 200-209 both seats:
  - 10/20 wins, avg raw diff -1.4, raw-zero losses 10.
  - Seat0: 5/10, avg raw diff +63.2.
  - Seat1: 5/10, avg raw diff -65.9.
  - Loop021 reference: 17/20 wins, avg raw diff +2558.1, raw-zero losses 3.

Decision:
- Reject.
- Seat1-only gating did not preserve Loop021's seat0 strength and did not improve seat1 enough.
- Stop the first-target mismatch penalty family for now:
  - hard veto failed,
  - score penalty failed,
  - soft penalty failed,
  - seat1-only soft penalty failed.
- Current best non-promoted candidate remains `candidates/loop_021_commit_drop_return_aware.py`.
- Current submission champion remains `main.py` / `candidates/champion_current.py`.

## 2026-06-07 Action Audit CLI Expansion

Reason:
- Loop039-044 all failed, and the old `review_action_accuracy.py` could not audit the same opponent/seed/seat conditions used by `test_local.py`.
- Before creating more candidates, align the audit runner with the evaluation runner.

Tool changes:
- Rebuilt `review_action_accuracy.py` with:
  - `--agent`
  - `--opponents` / `--opponent`
  - `--games`
  - `--seed-start`
  - `--seats`
  - `--agent-slot` / `--tested-seat`
  - `--rotate-seats`
  - `--turns`
  - `--out`
  - `--findings-out`
- Preserved positional variant mode for backwards compatibility.
- Added game-level JSONL with raw score, reward, status, finding counts, hard-error counts, and suspicious counts.
- Added finding-level JSONL with source/guessed-target/first-static-hit fields.

Audit limitation:
- This audit is still `static_current_position_angle_guess`.
- It guesses target intent from current angle and current planet positions.
- It does not simulate moving orbital targets, same-turn combat, incoming fleets, retake risk, or the agent's internal target ID.
- Therefore, `static_path_hits_wrong_planet`, `static_path_hits_sun`, and `underpowered_launch` are weak relative signals, not official invalid-move proof.

Initial same-condition audits:
- `main.py` vs `main.py`, seed 200-209, 2P both seats, turns=60:
  - `eval_results/audit_main_vs_main_gate200_summary.jsonl`
  - `eval_results/audit_main_vs_main_gate200_findings.jsonl`
  - Seat0 suspicious counts: likely_miss 67, sun 17, underpowered 124, nothing 66, wrong_planet 90.
  - Seat1 suspicious counts: likely_miss 57, sun 4, underpowered 98, nothing 66, wrong_planet 56.
- Loop021 vs `main.py`, seed 200-209, 2P both seats, turns=60:
  - `eval_results/audit_loop021_vs_main_gate200_summary.jsonl`
  - `eval_results/audit_loop021_vs_main_gate200_findings.jsonl`
  - Seat0 suspicious counts: likely_miss 62, sun 21, underpowered 135, nothing 69, wrong_planet 89.
  - Seat1 suspicious counts: likely_miss 59, sun 8, underpowered 92, nothing 63, wrong_planet 54.
- Loop021 vs `main.py`, seed 300-309, 2P both seats, turns=60:
  - `eval_results/audit_loop021_vs_main_holdout300_309_summary.jsonl`
  - `eval_results/audit_loop021_vs_main_holdout300_309_findings.jsonl`
  - Seat0 suspicious counts: likely_miss 61, sun 10, underpowered 112, nothing 61, wrong_planet 80.
  - Seat1 suspicious counts: likely_miss 55, sun 8, underpowered 96, nothing 52, wrong_planet 56.

Interpretation:
- Baseline `main.py` already has many static-audit suspicious rows, so static audit is noisy.
- Loop021 does not clearly increase wrong-planet counts versus `main.py` on the aligned Gate A audit; it slightly increases sun counts and seat0 underpowered count.
- Holdout seat1 weakness is not explained by static wrong-planet count alone.
- A short `test_local.py` recheck on seed 200-202 did not reproduce the historical Loop021 17/20 Gate A shape, so future promotion decisions should use repeated runs or larger holdout rather than one historical Gate A file.
- Current champion remains `main.py` / `candidates/champion_current.py`.

## 2026-06-07 Evaluation Reproducibility Diagnostic

Reason:
- Historical `eval_results/loop_021_vs_main_gate200.jsonl` showed Loop021 at 17/20 versus `main.py`.
- A later `test_local.py` recheck on seed 200-202 did not reproduce that shape.
- Before trusting more candidate loops, measure whether results depend on Python process mode or `PYTHONHASHSEED`.

Tool:
- Added `tools/run_repeated_eval.py`.
- Runs `test_local.py` in fresh subprocesses.
- Supports:
  - `--process-mode batch`
  - `--process-mode per-game`
  - `--hash-seeds 0,1,unset`
  - combined JSONL output
  - per-repeat/per-seat aggregate
  - seed/seat reward flip counts
  - command/provenance fields and sha256 hashes.

Diagnostics:
- Loop021 vs `main.py`, seed 200-202, 2P both seats:
  - Batch mode: `eval_results/repeated_batch_loop021_200_202.jsonl`.
  - Reward flips across hash seeds: 4/6 seed-seat cases.
  - Combined batch: seat0 6/9 wins, avg raw +634.9; seat1 6/9 wins, avg raw +1043.1.
  - Per-game mode: `eval_results/repeated_pergame_loop021_200_202.jsonl`.
  - Reward flips across hash seeds: 5/6 seed-seat cases.
  - Combined per-game: seat0 6/9 wins, avg raw +1619.3; seat1 5/9 wins, avg raw +580.6.
- `main.py` vs `main.py`, seed 200-202, 2P both seats:
  - Per-game mode: `eval_results/repeated_pergame_main_mirror_200_202.jsonl`.
  - Reward flips across hash seeds: 2/6 seed-seat cases.
  - Combined per-game: seat0 7/9 wins, avg raw +738.9; seat1 9/9 wins, avg raw +2911.9.
- `candidates/champion_current.py` vs `main.py`, seed 200-202, 2P both seats:
  - `cmd /c fc /b main.py candidates\champion_current.py`: no differences.
  - Per-game mode: `eval_results/repeated_pergame_champion_current_vs_main_200_202.jsonl`.
  - Reward flips across hash seeds: 4/6 seed-seat cases.
  - Combined per-game: seat0 3/9 wins, avg raw -1693.6; seat1 7/9 wins, avg raw +2429.1.

Interpretation:
- Local evaluation is strongly hash-seed sensitive, even when comparing byte-identical `main.py`/`champion_current.py` against `main.py`.
- Single JSONL Gate A files are not stable enough for promotion decisions.
- Future candidate evaluation must use repeated subprocess evaluation across multiple `PYTHONHASHSEED` values.
- A candidate should only be trusted if it improves combined repeated results and does not simply win one hash seed.
- Next direction: inspect unordered set/dict iteration in the agent code and consider deterministic ordering only if it can be done narrowly without damaging strategy.

## 2026-06-07 Repeated Hash-Seed Evaluation: Current Best Check

Protocol:
- Use `tools/run_repeated_eval.py`.
- Batch process mode.
- `PYTHONHASHSEED=0,1,2`.
- 2P both seats.
- Compare against `main.py`.
- Treat each hash seed as a distinct deterministic map set because initial Orbit Wars planets differ by `PYTHONHASHSEED`.

Train band seed 200-209:
- `candidates/champion_current.py` vs `main.py`:
  - `eval_results/repeated_batch_champion_current_vs_main_200_209_h012.jsonl`
  - 27/60 wins, avg raw diff -487.0, raw-zero losses 32.
  - Seat0: 12/30, avg raw -435.0.
  - Seat1: 15/30, avg raw -538.9.
- Loop021:
  - `eval_results/repeated_batch_loop021_200_209_h012.jsonl`
  - 34/60 wins, avg raw diff +339.0, raw-zero losses 26.
  - Seat0: 15/30, avg raw -200.5.
  - Seat1: 19/30, avg raw +878.4.
- Loop043:
  - `eval_results/repeated_batch_loop043_200_209_h012.jsonl`
  - 31/60 wins, avg raw diff -70.2, raw-zero losses 29.
  - Seat0: 12/30, avg raw -898.5.
  - Seat1: 19/30, avg raw +758.1.
- Loop044:
  - `eval_results/repeated_batch_loop044_200_209_h012.jsonl`
  - 36/60 wins, avg raw diff +671.8, raw-zero losses 24.
  - Seat0: 19/30, avg raw +959.2.
  - Seat1: 17/30, avg raw +384.3.

Holdout band seed 300-309:
- Loop021:
  - `eval_results/repeated_batch_loop021_300_309_h012.jsonl`
  - 35/60 wins, avg raw diff +584.0, raw-zero losses 25.
  - Seat0: 19/30, avg raw +1141.3.
  - Seat1: 16/30, avg raw +26.6.
- Loop044:
  - `eval_results/repeated_batch_loop044_300_309_h012.jsonl`
  - 27/60 wins, avg raw diff -308.2, raw-zero losses 33.
  - Seat0: 13/30, avg raw -468.4.
  - Seat1: 14/30, avg raw -148.0.

Decision:
- Loop044 is train-band overfit. It beats Loop021 on seed 200-209 hash average but fails holdout badly.
- Loop043 is not competitive.
- Under the repeated hash-seed protocol, Loop021 is the current strongest non-promoted candidate:
  - improves over byte-identical champion/current main on train band,
  - remains positive on holdout,
  - does not show the Loop044 holdout collapse.
- Current submission champion remains `main.py` / `candidates/champion_current.py` because Loop021 still needs broader repeated validation and action-risk review before replacing `main.py`.

## 2026-06-07 Current Best Candidate Snapshot

Created:
- `candidates/current_best_repeated_hash.py`.
- Byte-identical to `candidates/loop_021_commit_drop_return_aware.py`.
- This is a working "current best" pointer for continued experiments, not a `main.py` overwrite.

Additional repeated holdout:
- `candidates/champion_current.py` vs `main.py`, seed 300-309:
  - `eval_results/repeated_batch_champion_current_vs_main_300_309_h012.jsonl`
  - 33/60 wins, avg raw diff +339.5, raw-zero losses 24.
- Loop021 vs `main.py`, seed 300-309:
  - `eval_results/repeated_batch_loop021_300_309_h012.jsonl`
  - 35/60 wins, avg raw diff +584.0, raw-zero losses 25.
- `candidates/champion_current.py` vs `main.py`, seed 400-409:
  - `eval_results/repeated_batch_champion_current_vs_main_400_409_h012.jsonl`
  - 27/60 wins, avg raw diff -384.2, raw-zero losses 32.
- Loop021 vs `main.py`, seed 400-409:
  - `eval_results/repeated_batch_loop021_400_409_h012.jsonl`
  - 29/60 wins, avg raw diff +115.3, raw-zero losses 31.

Combined repeated-hash view across seed bands 200/300/400:
- Champion/current main proxy:
  - 87/180 wins.
  - Weighted avg raw diff about -177.2.
- Loop021/current best:
  - 98/180 wins.
  - Weighted avg raw diff about +346.1.

Decision:
- `current_best_repeated_hash.py` / Loop021 is the strongest local candidate under the new repeated hash-seed protocol.
- It is still not automatically promoted to `main.py` because the evaluation environment's hash behavior is now known to be map-generating, and broad validation is needed before replacing the submission file.
- Next recommended work:
  - use `current_best_repeated_hash.py` as the base for new loops,
  - keep evaluating with `tools/run_repeated_eval.py`,
  - require improvements on both seed 200-209 and at least one holdout band.

## 2026-06-07 Loop033 Provisional Current Best

Change:
- `candidates/current_best_repeated_hash.py` was updated from Loop021 to `candidates/loop_033_preemptive_evac_ratio135.py`.
- `main.py` was not changed.
- The previous current-best agent remains available as `candidates/loop_021_commit_drop_return_aware.py`.
- SHA256:
  - Loop033/current_best: `79f41a66cce1038b453d98483e716023edccf4938f9db777137fb192a2c0d428`.
  - Loop021: `059826d5db7527ba28fdb02ff86a5cccb065ca9f84a30c41f48ec4bbcf0f81c4`.

Screen result:
- Loop033 small screen vs previous current_best:
  - seed 200-204: 20/30 wins, avg raw about +1249.9.
  - seed 300-304: 23/30 wins, avg raw about +2472.2.
- Loop035 small screen did not clear the direct current_best threshold:
  - seed 200-204: 17/30 wins, seat0 weak.
  - seed 300-304: 16/30 wins, avg raw only slightly positive and seat0 weak.

Full repeated evaluation, hash seeds 0/1/2, seed bands 200/300/400, 2P both seats:
- Loop033 vs previous current_best/Loop021:
  - `eval_results/repeated_batch_loop033_vs_current_best_200_209_h012.jsonl`: 35/60 wins, avg raw +501.8.
  - `eval_results/repeated_batch_loop033_vs_current_best_300_309_h012.jsonl`: 33/60 wins, avg raw +263.3.
  - `eval_results/repeated_batch_loop033_vs_current_best_400_409_h012.jsonl`: 40/60 wins, avg raw +1321.9.
  - Combined: 108/180 wins, avg raw +695.7, raw-zero losses 72, bad 0.
  - Seat0: 54/90 wins, avg raw +732.3.
  - Seat1: 54/90 wins, avg raw +659.0.
- Loop033 vs `main.py`:
  - `eval_results/repeated_batch_loop033_vs_main_200_209_h012.jsonl`: 31/60 wins, avg raw +292.7.
  - `eval_results/repeated_batch_loop033_vs_main_300_309_h012.jsonl`: 28/60 wins, avg raw -297.9.
  - `eval_results/repeated_batch_loop033_vs_main_400_409_h012.jsonl`: 42/60 wins, avg raw +1353.4.
  - Combined: 101/180 wins, avg raw +449.4, raw-zero losses 79, bad 0.
  - Seat0: 54/90 wins, avg raw +641.9.
  - Seat1: 47/90 wins, avg raw +256.9.
- Loop021 baseline vs `main.py` on the same 200/300/400 bands:
  - Combined: 98/180 wins, avg raw +346.1, raw-zero losses 82, bad 0.
  - Seat0: 49/90 wins, avg raw +408.9.
  - Seat1: 49/90 wins, avg raw +283.3.

Action audit:
- Static audit is not a perfect physics replay; use it as a relative risk signal only.
- Hard invalid findings remained 0.
- Compared with Loop021, Loop033 generally reduced `static_path_hits_wrong_planet`.
- `likely_miss_by_angle` and `static_path_hits_nothing` increased in some bands, consistent with the preemptive-evac style producing more non-direct shots or static-model false positives.
- Audit files:
  - `eval_results/audit_loop033_vs_main_200_209_summary.jsonl`
  - `eval_results/audit_loop033_vs_main_200_209_findings.jsonl`
  - `eval_results/audit_loop033_vs_main_300_309_summary.jsonl`
  - `eval_results/audit_loop033_vs_main_300_309_findings.jsonl`
  - `eval_results/audit_loop033_vs_current_best_200_209_summary.jsonl`
  - `eval_results/audit_loop033_vs_current_best_200_209_findings.jsonl`
  - `eval_results/audit_loop033_vs_current_best_300_309_summary.jsonl`
  - `eval_results/audit_loop033_vs_current_best_300_309_findings.jsonl`

Review decision:
- Subagent review accepted Loop033 as the provisional development champion.
- Do not overwrite `main.py` yet.
- Continue measuring new candidates against both Loop033/current_best and `main.py`.

Known risks:
- Loop033 still loses many games by raw score 0. It wins more often, but losses are often total collapses.
- Loop033 vs `main.py` seat1 is slightly worse than Loop021 by wins and raw, even though total performance improved.
- Loop044 showed that train-band strength can overfit, so Loop033 needs an additional holdout before submission promotion.

Next required holdout before touching `main.py`:
- Run seed 500-519, hash seeds 0/1/2, 2P both seats, batch mode:
  - Loop033/current_best vs Loop021.
  - Loop033/current_best vs `main.py`.
  - Loop021 vs `main.py` as the same-band baseline if not already available.
- Promotion criteria:
  - invalid/timeout 0.
  - Loop033 beats Loop021 directly with positive avg raw.
  - Both seats remain at least approximately even.
  - Loop033 vs `main.py` beats Loop021 baseline by wins or avg raw without a raw-zero-loss blowup.
  - Static audit hard invalid stays 0 and sun/wrong-planet counts do not become materially worse.

## 2026-06-07 Holdout 500 And 4P Check

2P holdout, seed 500-519, hash seeds 0/1/2, both seats:
- Loop033/current_best vs Loop021:
  - `eval_results/holdout500_loop033_current_best_vs_loop021_h012.jsonl`
  - 68/120 wins, avg raw about +525.0, raw-zero losses 52, bad 0.
  - Seat0: 34/60 wins, avg raw +668.1.
  - Seat1: 34/60 wins, avg raw +381.8.
- Loop033/current_best vs `main.py`:
  - `eval_results/holdout500_loop033_current_best_vs_main_h012.jsonl`
  - 69/120 wins, avg raw about +614.3, raw-zero losses 51, bad 0.
  - Seat0: 35/60 wins, avg raw +720.2.
  - Seat1: 34/60 wins, avg raw +508.4.
- Loop021 vs `main.py` baseline:
  - `eval_results/holdout500_loop021_vs_main_h012.jsonl`
  - 65/120 wins, avg raw about +281.2, raw-zero losses 55, bad 0.
  - Seat0: 31/60 wins, avg raw +123.2.
  - Seat1: 34/60 wins, avg raw +439.1.

2P interpretation:
- Loop033/current_best held its advantage on unseen seed 500-519.
- It still should not replace `main.py` until 4P is checked because preemptive evacuation can transfer value to third parties.

Holdout action audit, seed 500-519:
- Loop033/current_best vs `main.py`:
  - `eval_results/audit_holdout500_loop033_current_best_vs_main_summary.jsonl`
  - `eval_results/audit_holdout500_loop033_current_best_vs_main_findings.jsonl`
  - hard invalid 0.
  - Total suspicious: wrong_planet 223, sun 46, underpowered 466, miss 294, nothing 290.
- Loop021 vs `main.py`:
  - `eval_results/audit_holdout500_loop021_vs_main_summary.jsonl`
  - `eval_results/audit_holdout500_loop021_vs_main_findings.jsonl`
  - hard invalid 0.
  - Total suspicious: wrong_planet 263, sun 57, underpowered 467, miss 286, nothing 290.
- Audit interpretation:
  - Loop033 reduced wrong-planet and sun static findings on this holdout.
  - The audit does not block Loop033 as a 2P current-best.

4P small pool screen, seed 500-504, hash seeds 0/1/2, all seats:
- Pool opponents: `main.py`, `variants/roman_lb1224.py`, `variants/suneet_lb1200.py`.
- Loop033/current_best:
  - `eval_results/screen4p_holdout500_loop033_current_best_vs_pool_h012.jsonl`
  - 28/60 wins, avg raw -609.2, avg rank 1.533, raw-zero losses 31, bad 0.
- Loop021:
  - `eval_results/screen4p_holdout500_loop021_vs_pool_h012.jsonl`
  - 35/60 wins, avg raw +284.7, avg rank 1.417, raw-zero losses 25, bad 0.

4P interpretation:
- Loop033 is still the 2P development champion, but it is not safe as a universal `main.py` replacement.
- The 4P result clearly favors Loop021 over Loop033.
- Submission promotion remains blocked by 4P performance.

Loop045 attempt:
- Created `candidates/loop_045_2p_ratio135_4p_ratio120.py`.
- Hypothesis:
  - keep Loop033 ratio 1.35 in 2P,
  - use Loop021 ratio 1.20 in 4P.
- Implementation:
  - `PREEMPTIVE_EVAC_DOOM_RATIO_4P = 1.20`.
  - `doom_ratio = PREEMPTIVE_EVAC_DOOM_RATIO if world.is_2p else PREEMPTIVE_EVAC_DOOM_RATIO_4P`.
- Review accepted the direction as a minimal 2P/4P split candidate.
- Smoke:
  - `eval_results/smoke_loop045_2p_vs_main_h0.jsonl`
  - `eval_results/smoke_loop045_4p_vs_pool_h0.jsonl`
- Screen:
  - `eval_results/screen4p_holdout500_loop045_vs_pool_h012.jsonl`
  - 29/60 wins, avg raw about -351.2, avg rank not promoted; bad 0.
  - It improved slightly over Loop033 in 4P but did not approach Loop021's 35/60 and positive raw.
  - `eval_results/screen2p_holdout500_loop045_vs_loop021_h012.jsonl`: 18/30 wins.
  - `eval_results/screen2p_holdout500_loop045_vs_main_h012.jsonl`: 18/30 wins.
- Decision:
  - Loop045 is rejected.
  - Do not promote it to `current_best_repeated_hash.py`.
  - The 4P weakness is not solved by only restoring the doom ratio in 4P; other interactions in the evaluation/state or broader 4P policy need inspection.

## 2026-06-07 Evaluation Protocol Correction

Critical finding:
- Previous local evaluation did not fully fix the map.
- Orbit Wars map generation uses Python's global `random`.
- `configuration={"seed": seed}` alone did not seed that global random stream in the local Kaggle environment.
- `PYTHONHASHSEED` was not enough and should not be treated as the map seed.
- Agents also use a `time.perf_counter()` soft deadline; production-code evaluation can change actions depending on CPU timing.

Fixes made:
- `test_local.py` now calls `random.seed(seed)` immediately before `make("orbit_wars", ...)`.
- `review_action_accuracy.py` now does the same.
- Both outputs include `map_random_seed`.
- Created `eval_clones/` research-only deterministic clones:
  - `eval_clones/main_det.py`
  - `eval_clones/loop021_det.py`
  - `eval_clones/loop033_det.py`
  - `eval_clones/README.md`
- The deterministic clones disable the soft deadline by using `plan_moves(world, deadline=None)`.
- These clones are not submission files.

Determinism checks:
- `eval_results/determinism_loop033det_vs_maindet_500_501_h000.jsonl`
  - repeated same hash/seed 3 times.
  - identical results; flip count 0/4.
- `eval_results/determinism_loop033det_vs_loop021det_500_501_h000.jsonl`
  - repeated same hash/seed 3 times.
  - identical results; flip count 0/4.

Reinterpretation:
- All pre-correction benchmark files are still useful as noisy production robustness hints.
- They should not be used as the main strategy-selection signal.
- The main strategy-selection lane is now:
  1. deterministic clones for fixed-map strategic comparison,
  2. production files only for final stochastic robustness and timeout checks.

First deterministic fixed-map results, seed 500-509, hash seeds 0/1/2:
- 2P:
  - `eval_results/det2p_loop033det_vs_loop021det_500_509_h012.jsonl`
  - Loop033_det vs Loop021_det: 27/60 wins, avg raw about -120.5.
  - `eval_results/det2p_loop033det_vs_maindet_500_509_h012.jsonl`
  - Loop033_det vs main_det: 39/60 wins, avg raw about +1076.0.
  - `eval_results/det2p_loop021det_vs_maindet_500_509_h012.jsonl`
  - Loop021_det vs main_det: 42/60 wins, avg raw about +1637.2.
- 4P:
  - Pool: `main_det`, Roman LB1224, Suneet LB1200.
  - `eval_results/det4p_loop033det_vs_pool_500_504_h012.jsonl`
  - Loop033_det: 39/60 wins, avg raw about +923.0.
  - `eval_results/det4p_loop021det_vs_pool_500_504_h012.jsonl`
  - Loop021_det: 30/60 wins, avg raw about -204.6.

Working interpretation:
- Fixed-map 2P favors Loop021 over Loop033.
- Fixed-map 4P favors Loop033 over Loop021.
- The obvious next hypothesis is a mode-split agent:
  - 2P: Loop021 behavior.
  - 4P: Loop033 behavior.
- Since Loop021 and Loop033 differ only in `PREEMPTIVE_EVAC_DOOM_RATIO`, the simple version is:
  - ratio 1.20 in 2P,
  - ratio 1.35 in 4P.
- Do not overwrite `main.py` until this split is evaluated in deterministic and production robustness lanes.

## 2026-06-07 Loop046 Mode-Split Candidate

Candidate:
- `candidates/loop_046_mode_split_ratio_2p120_4p135.py`
- `candidates/production_candidate.py` is byte-identical to Loop046.
- `candidates/current_best_repeated_hash.py` was reverted to Loop021 because that file name came from the old noisy repeated-hash protocol.
- Research best pointers:
  - `candidates/research_best_2p.py` = Loop021.
  - `candidates/research_best_4p.py` = Loop033.

Implementation:
- Start from Loop021.
- Use `PREEMPTIVE_EVAC_DOOM_RATIO = 1.20` in 2P.
- Use `PREEMPTIVE_EVAC_DOOM_RATIO_4P = 1.35` in 4P.
- This is the minimal split implied by deterministic fixed-map evaluation:
  - 2P favored Loop021.
  - 4P favored Loop033.

Deterministic clone:
- `eval_clones/loop046_det.py`.
- Research only, soft deadline disabled.

Fixed-map deterministic/prod check, seed 500 band:
- `eval_results/det2p_loop046det_vs_maindet_500_509_h012.jsonl`
- `eval_results/prod_fixed2p_loop046_vs_main_500_509_h012.jsonl`
  - 42/60 wins, avg raw +1637.2, bad 0.
  - Same as Loop021 behavior in 2P.
- `eval_results/det2p_loop046det_vs_loop021det_500_504_h012.jsonl`
- `eval_results/prod_fixed2p_loop046_vs_loop021_500_509_h012.jsonl`
  - Production 500-509: 30/60 wins, avg raw 0.0, bad 0.
  - Interpreted as parity with Loop021 in 2P.
- `eval_results/det4p_loop046det_vs_pool_500_504_h012.jsonl`
- `eval_results/prod_fixed4p_loop046_vs_pool_500_504_h012.jsonl`
  - 39/60 wins, avg raw +923.0, bad 0.
  - Same as Loop033 behavior in 4P.

Fixed-map 600 holdout:
- `eval_results/det2p_loop046det_vs_maindet_600_609_h012.jsonl`
- `eval_results/prod_fixed2p_loop046_vs_main_600_609_h012.jsonl`
  - 39/60 wins, avg raw +798.0, bad 0.
- `eval_results/det2p_loop046det_vs_loop021det_600_609_h012.jsonl`
- `eval_results/prod_fixed2p_loop046_vs_loop021_600_609_h012.jsonl`
  - Production: 33/60 wins, avg raw 0.0, bad 0.
  - Seat0: 15/30, avg raw -586.8.
  - Seat1: 18/30, avg raw +586.8.
- `eval_results/det4p_loop046det_vs_pool_600_604_h012.jsonl`
- `eval_results/prod_fixed4p_loop046_vs_pool_600_604_h012.jsonl`
  - 36/60 wins, avg raw +693.6, bad 0.
  - Seat0 remains weak: 6/15, avg raw -618.8.
  - Other seats: 9/15, 9/15, 12/15.

Action audit:
- `eval_results/audit_fixed_loop046_vs_main_2p_500_509_summary.jsonl`
- `eval_results/audit_fixed_loop046_vs_main_2p_500_509_findings.jsonl`
  - hard invalid 0.
- `eval_results/audit_fixed_loop046_vs_main_2p_600_609_summary.jsonl`
- `eval_results/audit_fixed_loop046_vs_main_2p_600_609_findings.jsonl`
  - hard invalid 0.
- `eval_results/audit_fixed_loop046_vs_pool_4p_500_504_summary.jsonl`
- `eval_results/audit_fixed_loop046_vs_pool_4p_500_504_findings.jsonl`
  - hard invalid 0.
- `eval_results/audit_fixed_loop046_vs_pool_4p_600_604_summary.jsonl`
- `eval_results/audit_fixed_loop046_vs_pool_4p_600_604_findings.jsonl`
  - hard invalid 0.

Current decision:
- Loop046 is the strongest structured production candidate found after fixing the evaluation protocol.
- It combines the fixed-map 2P winner and fixed-map 4P winner with one mode-dependent ratio.
- `main.py` has not yet been overwritten.
- Remaining concern:
  - 4P seat0 is weak on the 600 band.
  - Before final promotion, either accept this as within variance because the total 4P result is positive, or run a larger 4P all-seat holdout.

## 2026-06-07 Loop046 4P 700 Holdout

Reason:
- A strict promotion review blocked `main.py` overwrite until larger 4P seat-symmetry validation.
- Main concern was 4P seat0:
  - seed 600-604: 6/15 wins, avg raw -618.8.

Run:
- `eval_results/prod_fixed4p_loop046_vs_pool_700_719_h012.jsonl`
  - interrupted after hash seeds 0 and 1.
  - 160 valid rows, bad 0.
- `eval_results/prod_fixed4p_loop046_vs_pool_700_719_h2.jsonl`
  - completed hash seed 2.
  - 80 valid rows, bad 0.
- Because fixed-map seeding is now active, hash seeds 0/1/2 produced identical per-seed results.

Combined 4P result, seed 700-719, hash seeds 0/1/2, all seats:
- 135/240 wins.
- avg raw +371.6.
- bad 0.
- Seat0: 24/60 wins, avg raw -1258.9, raw-zero losses 36.
- Seat1: 42/60 wins, avg raw +1550.0, raw-zero losses 18.
- Seat2: 36/60 wins, avg raw +638.7, raw-zero losses 24.
- Seat3: 33/60 wins, avg raw +556.6, raw-zero losses 27.

Decision:
- Loop046 remains the best structured production candidate.
- Do not overwrite `main.py` yet.
- It passes total 4P win/raw and has bad 0, but seat0 failed the review threshold:
  - target was approximately at least 27/60 and not heavily negative,
  - observed 24/60 and avg raw -1258.9.
- Next improvement should target 4P seat0 stability without disturbing:
  - 2P Loop021 parity,
  - 4P total positive raw,
  - action audit hard 0.

Likely next directions:
- Compare Loop046 seat0 losses against Loop033 and Loop021 on the same fixed 700 seeds.
- Identify whether seat0 collapse is caused by opening expansion, preemptive evac, leader-bash, or target selection.
- Candidate should be evaluated first on 4P seat0 seed 700-719, then rechecked on 2P parity.

## 2026-06-07 Loop047/048 Seat0 Follow-up

Loop047:
- `candidates/loop_047_opening4p14.py`.
- Single change from Loop046:
  - `PSM_OPENING_TURN_4P = 10 -> 14`.
- Pre-change review approved it as a narrow experiment because it left 2P untouched and avoided seat hardcoding.
- Primary gate result:
  - `eval_results/loop047_seat0_4p_pool_700_719_h0.jsonl`
  - 6/20 wins, avg raw -1939.95, raw-zero 14, bad 0.
  - Baseline Loop046 on the same band was 8/20 wins, avg raw -1258.9, raw-zero 12.
- Decision:
  - Reject.
  - Opening extension did not fix early-expansion-lag and flipped good seeds 706 and 713 into raw-zero losses.

Loop048:
- `candidates/loop_048_prod_reserve_4p.py`.
- Single candidate family from reviewer recommendation:
  - enable dormant 4P-only production reserve for routine spending,
  - `PROD_RESERVE_ENABLED = True`,
  - `PROD_RESERVE_4P_ONLY = True`,
  - `PROD_RESERVE_TURN_MIN = 25`,
  - `PROD_RESERVE_MIN_PROD = 3`,
  - `PROD_RESERVE_FRAC = 0.20`.
- Smoke:
  - `eval_results/loop048_smoke_random_4p_seed700.jsonl`
  - passed, bad 0.
- Interrupted primary gate partial:
  - `eval_results/loop048_seat0_4p_pool_700_719_h0.jsonl`
  - first 11 seeds only: 1/11 wins, avg raw -3318.0, raw-zero 10, bad 0.
- Decision:
  - Do not submit unless a full rerun later contradicts the partial result.
  - Current partial strongly suggests the production reserve is too passive and worsens seat0 tempo.

Submission candidates as of this checkpoint:
- Strongest overall verified candidate:
  - `candidates/production_candidate.py` = Loop046.
- 2P research best:
  - `candidates/research_best_2p.py` = Loop021.
- 4P research best:
  - `candidates/research_best_4p.py` = Loop033.
- Do not submit Loop047 or Loop048 from current evidence.

## 2026-06-07 Pre-submit Review And Kaggle Upload

Pre-submit review:
- Review Agent result: GO for the three named files as separate Kaggle submissions.
- Reviewed files:
  - `candidates/production_candidate.py` = Loop046, SHA256 `B69C084A3DCD18F24D19E51EAB68B93B5D9781B7A6FEC9CDA31ACD18C8220DB4`.
  - `candidates/research_best_2p.py` = Loop021, SHA256 `059826D5DB7527BA28FDB02FF86A5CCCB065CA9F84A30C41F48EC4BBCF0F81C4`.
  - `candidates/research_best_4p.py` = Loop033, SHA256 `79F41A66CCE1038B453D98483E716023EDCCF4938F9DB777137FB192A2C0D428`.
- Review notes:
  - standalone submissions,
  - stdlib-only imports,
  - callable `agent`,
  - global reset present on new games,
  - exclude Loop047/Loop048.

Local validation immediately before upload:
- `C:\owv\Scripts\python.exe -m py_compile` passed for all three files.
- Random smoke:
  - `eval_results/pre_submit_prod_random_smoke.jsonl`
  - `eval_results/pre_submit_2p_random_smoke.jsonl`
  - `eval_results/pre_submit_4p_random_smoke.jsonl`
  - all seats 2P/4P, bad 0.
- 2P vs current `main.py` smoke:
  - `eval_results/pre_submit_prod_vs_main_2p_smoke.jsonl`
  - `eval_results/pre_submit_2p_vs_main_2p_smoke.jsonl`
  - `eval_results/pre_submit_4p_vs_main_2p_smoke.jsonl`
  - all DONE, bad 0.
- 4P pool smoke:
  - `eval_results/pre_submit_prod_vs_pool_4p_smoke.jsonl`
  - `eval_results/pre_submit_2p_vs_pool_4p_smoke.jsonl`
  - `eval_results/pre_submit_4p_vs_pool_4p_smoke.jsonl`
  - all DONE, bad 0.

Kaggle submissions:
- `53439162`: `production_candidate.py`, description `Loop046 production candidate mode split 2p120 4p135 sha B69C084A pre_submit_smoke_bad0`, status `PENDING` at first check.
- `53439165`: `research_best_2p.py`, description `Loop021 research best 2p sha 059826D5 pre_submit_smoke_bad0`, status `PENDING` at first check.
- `53439169`: `research_best_4p.py`, description `Loop033 research best 4p sha 79F41A66 pre_submit_smoke_bad0`, status `PENDING` at first check.

Locked local snapshots:
- `locked_submissions/53439162_loop046_production_candidate_PENDING.py`
- `locked_submissions/53439165_loop021_research_best_2p_PENDING.py`
- `locked_submissions/53439169_loop033_research_best_4p_PENDING.py`

Public LB result after score refresh, latest observed at `2026-06-07T13:48:44+09:00`:
- `53439162` Loop046: COMPLETE, public score 915.2.
- `53439165` Loop021: COMPLETE, public score 600.0.
- `53439169` Loop033: COMPLETE, public score 885.7.

Decision:
- Treat Loop046 / `candidates/production_candidate.py` as the latest-observed public-LB leader.
- Do not overwrite `main.py` until the score is stable across another check and the candidate is re-reviewed.
- Keep `locked_submissions/53418690_vickimar_heuristic_fixed_SCORE_908_0.py` as the previous-best 908 reference.
- Treat the local fixed-map win rates against `main.py` as insufficient promotion evidence.
- Next loop should preserve Loop046, verify the score stability, and improve carefully from Loop046 or isolate its useful pieces.

Immediate postmortem hypotheses:
- The local opponent pool overfit against known public agents and did not represent leaderboard map/opponent distribution.
- The fixed-map protocol may have measured head-to-head raw score rather than broad survival/Elo robustness.
- Candidate changes may exploit weaknesses in `main.py` while losing to broader LB strategies.
- The commit-guard family is no longer categorically suspicious because Loop046 is latest-observed 915.2.
- Loop021's 600.0 may simply mean its public evaluation has not fully started; do not hard-conclude from that value alone.
- Loop046's mode split / combined changes have real signal and should be preserved.

## 2026-06-07 Loop049 Locked908 + 4P Ratio Isolation

Reason:
- Post-submit review recommended restarting from locked 908 and isolating the 4P preemptive-evac ratio without the Loop021 commit guard / commit-drop family.

Candidate:
- `candidates/loop_049_locked908_ratio4p135.py`
- Base: `locked_submissions/53418690_vickimar_heuristic_fixed_SCORE_908_0.py`
- No `_can_commit_fleet`.
- No `_can_commit_many`.
- No return-aware `_commit_fleet` drop.
- Only behavior change:
  - 2P keeps `PREEMPTIVE_EVAC_DOOM_RATIO = 1.20`.
  - 4P uses `PREEMPTIVE_EVAC_DOOM_RATIO_4P = 1.35`.
- SHA256: `9EAF602B468A40587521984E187756DDBB789355A2C0AF73B7F60FE5588DF1C2`.

Pre-screen:
- `py_compile`: passed.
- `eval_results/loop049_random_smoke_930.jsonl`
  - 6/6 random smoke, bad 0.
- `eval_results/loop049_vs_main_2p_930_932_h0.jsonl`
  - 3/6, avg raw 0.0, bad 0.
  - Interpreted as parity-like because 2P should match locked 908.

Review gate:
- The 4P rerun was approved as a primary screen, not a submission gate.
- Reject if any seat collapses, especially `0/5` or strong negative avg raw.

4P pool screen:
- `eval_results/loop049_vs_pool_4p_930_934_h0_rerun.jsonl`
- Stopped after 6 rows because seat0 completed and failed the review gate.
- Seat0: 1/5 wins, avg raw -2168.6, raw-zero 4, bad 0.
- Partial overall: 2/6 wins, avg raw -1470.8, bad 0.

Decision:
- Reject Loop049.
- Do not submit.
- Scalar 4P preemptive-evac ratio alone is not the useful piece to isolate from Loop033/046.
- Continue from locked 908, but choose a different isolated lever than broad commit-drop or scalar 4P evac ratio.
