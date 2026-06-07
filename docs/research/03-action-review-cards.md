# Action Review Cards

Use these as implementation checkpoints. Each action should be reviewed before moving to the next one.

## A0: Build A Real Benchmark Harness

Hypothesis:

- We cannot judge changes from a few random games or public LB impressions.

Edit scope:

- Add or extend `test_local.py`.
- Do not change `main.py`.

Build:

- Accept `--agent`, `--opponents`, `--games`, `--seats`, `--seed-start`.
- Report both rewards and raw final ship scores.
- Run 2P and 4P.
- Save CSV/JSONL results under `runs/`.

Command:

```powershell
C:\owv\Scripts\python.exe test_local.py --agent main.py --opponents random,starter,baselines/path_safe_v1.py --games 50 --seats 2
```

Success criteria:

- Results include win rate, average score diff, invalid count, timeout count.
- Same seed range is reproducible.

Review decision:

- Keep if it runs in reasonable time and makes regressions obvious.
- Do not tune strategy before this exists.

## A1: Physics Contract Tests

Hypothesis:

- Many strategy errors are actually shot feasibility or ETA errors.

Edit scope:

- Add `tools/physics_check.py` or a test mode.
- Avoid changing policy behavior unless a clear formula bug is found.

Build:

- Check fleet speed against official formula.
- Check sun-crossing rejection.
- Check static planet ETA.
- Check orbiting planet future position.
- Check comet path future position.

Command:

```powershell
C:\owv\Scripts\python.exe tools/physics_check.py
```

Success criteria:

- Prints pass/fail cases.
- Any failure maps to one named function in `main.py`.

Review decision:

- If failures are found, patch physics before strategy.
- If no failures, move to arrival ledger audit.

## A2: Arrival Ledger Audit

Hypothesis:

- Better use of existing `obs.fleets` will improve defense and reduce overcommit.

Edit scope:

- Inspect and, if needed, patch the functions that identify fleet target and ETA.
- Add debug summary for arrivals by planet.

Build:

- For each fleet, estimate target planet and ETA.
- Group by target and owner.
- Project combat in ETA order.
- Expose this to both attack and defense candidate generation.

Command:

```powershell
C:\owv\Scripts\python.exe test_local.py --agent main.py --opponents starter --games 30 --seats 2
```

Success criteria:

- Incoming hostile fleets to owned planets are detected before impact.
- Friendly pending captures prevent redundant launches.

Review decision:

- Keep if score improves or replay inspection shows fewer obvious defense misses.
- Tune if it over-defends and stops expanding.

## A3: Opening Static-Neutral ROI

Hypothesis:

- Early stable expansion beats chasing hard moving targets.

Edit scope:

- Opening target scoring only.
- Do not touch defense or endgame.

Build:

- Score neutral planets by `(production * useful_remaining_turns - ships_sent - travel_cost)`.
- Add static preference.
- Add rotating target gate: only short ETA and stable aim.
- Add reaction-time penalty for planets enemy can reinforce faster.

Command:

```powershell
C:\owv\Scripts\python.exe test_local.py --agent main.py --opponents baselines/path_safe_v1.py --games 50 --seats 2
```

Success criteria:

- First 50 turns show fewer failed/late neutral captures.
- Win rate does not drop against `starter`.

Review decision:

- Keep if opening ship economy improves.
- Rework if agent becomes too passive.

## A4: Defense Before Expansion

Hypothesis:

- A capture is bad if it exposes a high-production owned planet.

Edit scope:

- Defense mission and source reserve logic.

Build:

- Identify owned planets projected to fall within `DEFENSE_LOOKAHEAD`.
- Send rescue only if it can arrive before or near fall time.
- If rescue impossible, evacuate doomed ships toward useful targets.
- Reserve ships based on local threat, not only fixed production multiple.

Command:

```powershell
C:\owv\Scripts\python.exe test_local.py --agent main.py --opponents main.py,starter --games 50 --seats 2
```

Success criteria:

- Fewer high-production planets lost without response.
- Agent still launches enough expansion/attack missions.

Review decision:

- Keep if defensive saves are visible and score diff improves.
- Rebalance if it hoards ships.

## A5: Mission Family Logging

Hypothesis:

- We need to know why each move was sent before tuning scores.

Edit scope:

- Add optional lightweight logging controlled by a constant or environment variable.
- Do not print during Kaggle submission unless disabled by default.

Build:

- For each committed fleet, record mission kind, source, target, ships, ETA, score, and rejection reason for top discarded candidates.

Command:

```powershell
$env:OW_DEBUG='1'; C:\owv\Scripts\python.exe test_local.py --agent main.py --opponents starter --games 3 --seats 2
```

Success criteria:

- Debug output identifies the policy path without overwhelming logs.
- No runtime issue when debug is off.

Review decision:

- Keep if it helps explain moves.
- Remove if it risks Kaggle stdout/time behavior.

## A6: Forward Simulation Filter

Hypothesis:

- Short-horizon simulation catches false-positive captures and self-weakening moves.

Edit scope:

- Candidate filtering after mission generation.

Build:

- Clone simplified state.
- Simulate existing fleets plus candidate launch for 5-10 turns.
- Reject candidate if target flips back quickly or score delta is clearly worse.

Command:

```powershell
C:\owv\Scripts\python.exe test_local.py --agent main.py --opponents baselines/path_safe_v1.py,starter --games 30 --seats 2
```

Success criteria:

- Runtime remains safe.
- At least some bad candidates are rejected in debug examples.

Review decision:

- Keep if it improves stability.
- Lower horizon if time cost is high.

## A7: 4-Player Strategy Split

Hypothesis:

- 4P needs less overextension and more opportunistic pressure than 2P.

Edit scope:

- Strategy mode selection and value multipliers.

Build:

- Detect number of active players.
- In 4P, penalize targets that a third player can retake cheaply.
- Add leader/weakest-player pressure logic separately.
- Reduce all-in attacks unless elimination is realistic.

Command:

```powershell
C:\owv\Scripts\python.exe test_local.py --agent main.py --opponents starter,random,baselines/path_safe_v1.py --games 30 --seats 4
```

Success criteria:

- Fewer cases where we donate ships/planets to third parties.
- 2P results do not regress from 4P-specific constants.

Review decision:

- Keep only if 4P improves without damaging 2P.

## A8: Parameter Search

Hypothesis:

- Once logic is stable, many gains come from weight tuning.

Edit scope:

- Add a config/tuning script.
- Keep tuned constants reviewable.

Build:

- Choose 10-30 constants.
- Random search or evolutionary search.
- Train seeds and holdout seeds.
- Opponent pool includes current, prior, and simple baselines.

Command:

```powershell
C:\owv\Scripts\python.exe tools/tune_params.py --trials 100 --games 20
```

Success criteria:

- Produces ranked parameter sets.
- Holdout result is reported.

Review decision:

- Keep parameter changes only if holdout seeds improve.

## A9: Learning-Assisted Selector

Hypothesis:

- Learning should rank candidate missions, not invent raw continuous actions.

Edit scope:

- Offline experiment only at first.
- Do not replace `agent()` until it beats the heuristic selector locally.

Build:

- Generate per-turn candidate missions from the heuristic.
- Label chosen/winning candidates from strong self-play or local tournament winners.
- Train a small model to rank candidates.
- Use as a tie-breaker or value feature.

Command:

```powershell
C:\owv\Scripts\python.exe tools/collect_candidates.py --games 100
C:\owv\Scripts\python.exe tools/train_candidate_ranker.py
```

Success criteria:

- The model improves candidate ranking on held-out games.
- Runtime and dependency footprint are Kaggle-safe.

Review decision:

- Keep as advisory feature first.
- Do not use full PPO/AZ unless action pruning and evaluator are already reliable.

