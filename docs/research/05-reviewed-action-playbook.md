# Reviewed Action Playbook

This document turns the public-notebook analysis into reviewable actions. It is intentionally more concrete than the roadmap.

Each action has:

- purpose,
- implementation scope,
- reviewer prompt,
- pass/fail criteria,
- expected failure mode.

The order matters. Do not skip to learning/search before the physics and evaluation harness are trustworthy.

## Action 1: Build The Benchmark Harness

Purpose:

- Make every later change measurable.

Implementation scope:

- Extend `test_local.py`.
- Add support for:
  - `--agent`
  - `--opponents`
  - `--games`
  - `--seats`
  - `--seed-start`
  - JSONL/CSV output under `runs/`
  - per-player final raw ship scores: owned planet ships plus owned fleet ships
  - player seat and opponent ordering
  - final status for all agents
  - elapsed time
  - invalid/timeout tracking
  - optional seat-symmetry runs, especially for 4P

Reviewer prompt:

```text
Review the benchmark harness only. Check that it runs reproducibly, supports 2P and 4P, reports reward and per-player raw score, records seat/opponent ordering, and does not hardcode main.py or one opponent. Do not review strategy quality.
```

Pass criteria:

- Same command produces same seed list.
- Opponent pool can include file paths and built-in agents.
- 2P and 4P both run.
- Output is easy to compare before/after.
- Seat symmetry can be checked on fixed seeds.

Expected failure mode:

- Harness takes too long with heavy agents.

Mitigation:

- Add `--max-steps` only for debug if environment supports it, otherwise use small seed sets and staged opponent pools.

## Action 2: Physics Contract Audit

Purpose:

- Ensure every scored shot can physically work.

Implementation scope:

- Add `tools/physics_check.py` or a non-submission debug script.
- Check:
  - official logarithmic fleet speed,
  - sun collision,
  - sun radius 10.0,
  - launch point at `planet.radius + 0.1`,
  - source/target boundary distance,
  - target-radius collision distance,
  - out-of-bounds removal,
  - unintended-planet collision before intended target,
  - static target ETA,
  - moving target lead aim,
  - comet path lookup,
  - moving planet/comet sweep after fleet movement,
  - re-aim after exact send count,
  - official turn order around launch, production, movement, sweep, and combat.

Reviewer prompt:

```text
Review only the physics contract. Compare formulas against the installed orbit_wars environment. Flag any mismatch in logarithmic speed, sun radius 10, launch clearance, collision, out-of-bounds removal, ETA, moving-target projection, comet path handling, or moving-body sweep. Do not suggest strategy changes.
```

Pass criteria:

- Physics matches local environment implementation.
- Rahul-style simplified speed/sun assumptions are not used in production.
- Changing send count triggers re-aim or explicit confirmation.
- A shot is not considered legal if it hits an unintended planet first.

Expected failure mode:

- Tests pass for static planets but miss orbiting/comet targets.

Mitigation:

- Include generated examples for static, orbiting, and comet planets.

## Action 3: Arrival Ledger And Planet Timeline

Purpose:

- Stop reasoning from current garrison only.

Implementation scope:

- Create or verify:
  - `build_arrival_ledger`,
  - confidence-tagged in-flight fleet collision inference,
  - `simulate_planet_timeline`,
  - `projected_state`,
  - `ships_needed_to_capture`,
  - `reinforcement_needed_to_hold_until`.

Reviewer prompt:

```text
Review the world model. Check that visible fleets are assigned by predicted first collision, not nearest intended target; uncertain fleet destinations are confidence-tagged or marked unknown. Check that same-turn arrivals use official owner grouping/top-two combat, production is applied in the correct order, and planned commitments can be injected into projections.
```

Pass criteria:

- Existing fleets affect target ownership estimates.
- Planned launches in the same turn affect later candidates.
- Same-turn multi-owner combat uses the official top-two cancellation plus survivor-vs-garrison rule.

Expected failure mode:

- Fleet target inference misses moving planets.

Mitigation:

- Use Vicki/Roman-style future-position checks, not only current ray intersection.
- Mark low-confidence fleet destinations as unknown rather than confidently wrong.

## Action 4: Mission Contract Split

Purpose:

- Stop mixing every idea into one target score.

Implementation scope:

- Define mission generators:
  - `capture_neutral`
  - `capture_enemy`
  - `rescue`
  - `reinforce`
  - `recapture`
  - `snipe`
  - `swarm`
  - `crash_exploit`
  - `comet_evac`
  - `doomed_evac`

Reviewer prompt:

```text
Review mission contracts. For each mission type, check that preconditions, ETA constraints, needed ships, hold condition, value, and risk penalty are explicit. Flag any mission that bypasses physics or timeline projection.
```

Pass criteria:

- Mission type is visible in logs or candidate object.
- Each mission has distinct validity checks.
- Capture and rescue are not scored as the same thing.

Expected failure mode:

- Mission generators produce too many candidates.

Mitigation:

- Prune by source top-K, target top-K, and max ETA before expensive scoring.

## Action 5: Commitment-Aware Planner

Purpose:

- Prevent duplicate sends and stale decisions.

Implementation scope:

- Maintain per-turn:
  - remaining ships by source,
  - target locks,
  - planned arrivals,
  - mission log.
- Optionally maintain persistent commitments across turns with explicit expiry.
- Same-source multi-launches must subtract from observed garrison in order.
- Launch-before-production budgeting must be explicit: do not spend ships that will be produced later this turn.

Reviewer prompt:

```text
Review commitment handling. Check that once a fleet is accepted, later candidates see reduced source inventory and target future arrivals. Check that same-source multi-launches spend only observed garrison, not future production. Check that persistent commitments expire or are revalidated.
```

Pass criteria:

- No repeated wasteful launches to already-won neutrals.
- Multi-source attacks intentionally synchronize ETA.
- Persistent plans are reset when target owner/state invalidates them.
- Accepted mission logs include `kind`, source, target, ships, angle, ETA, projected owner/ships before and after arrival, hold horizon, and rejection reasons for near-misses when debug is enabled.

Expected failure mode:

- Over-locking prevents useful follow-up attacks.

Mitigation:

- Allow follow-up only when projected existing commitment undershoots needed ships.

## Action 6: Opening Policy

Purpose:

- Establish stable early economy.

Implementation scope:

- Opening mode should prefer:
  - static neutrals,
  - low-garrison high-production targets,
  - short ETA orbiting targets only when aim is stable,
  - defense reserve around likely first contact.

Reviewer prompt:

```text
Review opening policy on 5 fixed seeds. For each first 40 turns, identify whether each launched fleet had clear ROI, whether any high-risk rotating target was chased too early, and whether source planets were left unsafe.
```

Pass criteria:

- Most early captures are held long enough to repay.
- Low-production/high-garrison neutrals are skipped.
- Early moving-target misses are rare.

Expected failure mode:

- Too much caution loses expansion race.

Mitigation:

- Add safe-neutral and contested-neutral categories rather than one global threshold.

## Action 7: Defense And Evacuation

Purpose:

- Preserve high-value owned planets and recover value from doomed planets.

Implementation scope:

- Build:
  - incoming hostile detection,
  - rescue mission,
  - coalition rescue if one source cannot cover,
  - doomed evacuation,
  - comet expiration evacuation.

Reviewer prompt:

```text
Review defense behavior on seeds where planets are lost. For each loss, determine whether the incoming threat was detected, whether rescue was possible, whether rescue would have been worth it, and whether owned-planet doomed evacuation should have fired. Separately review comet evacuation: verify path-index/life checks and that the launch occurs before expiration removal.
```

Pass criteria:

- High-production planets are defended when economically rational.
- Impossible rescues do not waste ships.
- Expiring comet ships are moved out when feasible.
- Owned-planet doom evacuation and comet expiration evacuation are separate decisions.

Expected failure mode:

- Defense hoards ships and stalls offense.

Mitigation:

- Rescue value must account for production saved and remaining turns.

## Action 8: Midgame Exploitation

Purpose:

- Win contested planets and punish enemy commitments.

Implementation scope:

- Add or verify:
  - recapture,
  - snipe after enemy fleet arrival,
  - crash exploit,
  - swarm with ETA tolerance,
  - counter-snipe.

Reviewer prompt:

```text
Review midgame exploitation. Check whether the planner uses visible enemy fleets as opportunities, not only threats. Verify that snipes arrive after the enemy weakens the target and before another owner can profit.
```

Pass criteria:

- Some missions explicitly exploit enemy in-flight commitments.
- Snipe/counter-snipe timing is logged.
- Swarm attacks are synchronized within acceptable ETA tolerance.

Expected failure mode:

- Fancy snipes are lower ROI than normal captures.

Mitigation:

- Keep exploitation missions competing with normal mission score, not hard-prioritized.

## Action 9: 2P Strategy Mode

Purpose:

- Close duels decisively.

Implementation scope:

- 2P-specific:
  - stop-expansion only after a benchmarked production/share or projected-score trigger is met,
  - pressure enemy high-production planets,
  - hammer/mega-hammer only after revalidation,
  - use attack as defense when enemy weakens a planet.

Reviewer prompt:

```text
Review 2P mode. Check whether the agent transitions from expansion to pressure at the right time. Identify long neutral grabs after a sufficient production lead and missed chances to attack exposed enemy production.
```

Pass criteria:

- No endless neutral greed after winning production position.
- Enemy production is attacked when feasible.
- Hammers have abort conditions.

Expected failure mode:

- Premature aggression loses economy.

Mitigation:

- Require production/share or projected-score threshold before pressure mode.

## Action 10: 4P Strategy Mode

Purpose:

- Avoid donating value in free-for-all.

Implementation scope:

- 4P-specific:
  - leader pressure,
  - weakest-enemy finishing only when it benefits us,
  - avoid overextended captures,
  - exploit enemy-vs-enemy battles,
  - avoid becoming the obvious leader too early if that triggers pressure.

Reviewer prompt:

```text
Review 4P mode. Check whether the agent distinguishes leader pressure from weakest-player farming, whether captures are holdable against third parties, and whether attacks accidentally donate planets to another enemy.
```

Pass criteria:

- 4P does not use 2P all-in behavior by default.
- Target owner strength and third-party reaction time affect score.
- Captures near enemy clusters have higher hold threshold.
- Target choice reports our projected rank delta, not only target owner weakness.

Expected failure mode:

- Attacking the weakest player helps the leader.

Mitigation:

- Score target by our projected rank delta, not just target owner's weakness.

## Action 11: Forward Simulation Filter

Purpose:

- Catch high-scoring moves that fail dynamically.

Implementation scope:

- Short simulation for top candidate missions only.
- Compare no-action and with-action states.
- Track runtime.
- Veto logic should be environment-correct for movement and combat, or explicitly log approximation boundaries.

Reviewer prompt:

```text
Review forward simulation filter. Check that it runs only on a bounded top-K, respects timeout budget, and rejects candidates for clear dynamic reasons rather than noisy score differences. Verify the simulator matches official movement/combat closely enough for a veto; if approximate, check that approximation boundaries are logged.
```

Pass criteria:

- Runtime safe under Kaggle timeout.
- Filtered candidates have explainable failure reason.
- Does not reject all aggressive play.
- Approximate simulation is not used to bless impossible shots.

Expected failure mode:

- Expensive and noisy.

Mitigation:

- Use it as veto for obvious failures, not as the whole evaluator.

## Action 12: Parameter Search

Purpose:

- Tune stable logic without hand guessing.

Implementation scope:

- Extract tunable constants.
- Run train/holdout seed split.
- Compare against opponent pool.

Reviewer prompt:

```text
Review parameter search. Check that train and holdout seeds are separated, opponent pool includes prior versions, and selected constants are not too numerous for the trial budget.
```

Pass criteria:

- Holdout improves or stays neutral.
- Tuned constants are documented.
- No one-seed overfit.

Expected failure mode:

- Chasing local noise.

Mitigation:

- Require improvement across multiple opponent types and held-out seeds.

## Action 13: Search Or Learning-Assisted Selector

Purpose:

- Improve candidate choice after rules are reliable.

Implementation scope:

- Candidate generator remains rule-based.
- Search/NN ranks or filters already-valid candidates.
- No raw continuous angle policy at first.

Reviewer prompt:

```text
Review learning/search integration. Check that the model/search only sees valid mission candidates, that fallback heuristic remains available, and that local held-out performance beats the heuristic selector before enabling it by default.
```

Pass criteria:

- Candidate validity does not depend on the model.
- Search/NN improves held-out local arena.
- Runtime and dependencies are submission-safe.

Expected failure mode:

- Model learns leaderboard/local artifacts or search amplifies physics bugs.

Mitigation:

- Keep it advisory until it beats the deterministic mission compiler consistently.

## Review-Agent Operating Rule

For every action above, the review should focus only on that action's contract. Do not allow the review to become a broad refactor request. The useful review question is:

```text
Did this action make the agent more truthful about the game state and more measurable, without hiding a new failure mode?
```
