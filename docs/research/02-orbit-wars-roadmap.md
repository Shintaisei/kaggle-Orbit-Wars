# Orbit Wars Implementation Roadmap

## Current Repository Context

Observed local files:

- `main.py`
  - Current submission file.
  - It appears to be adapted from a public Orbit Wars heuristic notebook and is much larger than the small baseline.
  - It already contains advanced concepts such as future position prediction, fleet intent, target scoring, forward simulation, mission handling, and many tuned constants.
- `baselines/path_safe_v1.py`
  - Small baseline: direct-path safety, simple target score, static preference, and no serious future model.
- `notebooks/vicki-lb-1110/`
  - Public heuristic notebook lineage.
- `notebooks/roman-lb-1224/`
  - Structured baseline derivative with mission families and tuned strategic constants.
- `notebooks/suneet-lb-1200/`
  - PPO-named strategy file, but structurally it still contains a large amount of handcrafted world modeling and mission logic.
- `notebooks/rahul-target-2000/`
  - Ambitious notebook with modules listed for predictor, simulator, MCTS, opponent model, comet logic, beam search, genetic tuner, and neural MLP.

Interpretation:

- The repo is no longer at "toy heuristic" stage.
- The next risk is uncontrolled complexity, not missing ambition.
- Improvements should be made through isolated audits and measurable changes.

## Target Architecture

Use five layers.

### 1. Physics Layer

Owns:

- Fleet speed.
- Source boundary to target boundary ETA.
- Sun collision.
- Planet collision.
- Moving-target lead aim.
- Comet path lookup.

Does not own:

- Target value.
- Whether a mission is strategically good.
- Whether to attack or defend.

Required API shape:

```python
plan_shot(source_id, target_id, ships) -> ShotPlan | None
```

Where `ShotPlan` contains:

- `angle`
- `eta`
- `target_future_position`
- `risk_flags`

### 2. World Model Layer

Owns:

- Parsed planets/fleets.
- Ownership groups.
- Existing fleet arrivals by planet.
- Projected owner/garrison at ETA.
- Remaining turns.
- 2-player vs 4-player state.
- Comet remaining lifetime.

Required API shape:

```python
project_planet(target_id, eta, extra_arrivals=None) -> PlanetProjection
```

Where `PlanetProjection` contains:

- `owner`
- `ships`
- `incoming_by_owner`
- `will_flip`
- `confidence`

### 3. Mission Layer

Owns candidate contracts:

- `capture_neutral`
- `attack_enemy`
- `rescue`
- `reinforce`
- `recapture`
- `snipe_after_enemy_collision`
- `swarm_joint_attack`
- `evacuate_doomed_planet`
- `late_total_war`

Each mission must state:

- Preconditions.
- Needed ships.
- Max acceptable ETA.
- Hold requirement.
- Value formula.
- Risk penalties.

### 4. Commitment Layer

Owns:

- Remaining ships per source.
- Target locks.
- Planned arrivals this turn.
- Persistent commitments across turns when safe.
- Prevention of duplicate launches.

Key rule:

After a mission is accepted, later candidates must see its future arrival as a fact.

### 5. Evaluation Layer

Owns:

- Local tournament.
- Seed list.
- Opponent pool.
- 2-player and 4-player split.
- Win rate, average score, elimination timing, invalid actions, timeout checks.
- Change log per experiment.

## Implementation Phases

### Phase 0: Benchmark Harness

Goal:

- Know whether a change helped.

Build:

- Run `main.py` against `random`, `starter`, `baselines/path_safe_v1.py`, and selected notebook-derived agents if executable.
- Support 2-player and 4-player games.
- Record final rewards and raw ship scores.
- Save seed-level results to `runs/`.

Review output:

- A small table: opponent, seats, seeds, win rate, average score diff, invalid/timeouts.

### Phase 1: Physics Audit

Goal:

- Prevent bad shots from being scored.

Build:

- Unit-like checks for fleet speed formula, sun collision, static target ETA, orbiting target lead aim, comet path lookup.
- A debug mode that logs rejected shots by reason.

Review output:

- Examples of accepted/rejected shots.
- No obvious legal static shots rejected.
- No obvious sun-crossing shots accepted.

### Phase 2: Arrival Ledger and Defense

Goal:

- Stop losing owned planets because incoming fleets are ignored or under-modeled.

Build:

- `arrivals_by_planet`.
- `project_planet`.
- `rescue_needs`.
- Defense priority before expansion.

Review output:

- For a seed where we lose a planet, show whether the incoming fleet was detected.
- Win/loss delta against current baseline.

### Phase 3: Opening Expansion ROI

Goal:

- Capture planets that pay back before they are retaken.

Build:

- Static neutral ROI first.
- Rotating neutral only if ETA is short and lead aim is stable.
- Production value based on remaining turns after ETA.
- Reaction-time penalty if enemy can reinforce faster than us.

Review output:

- First 40 turns replay notes for 5 seeds.
- Number of bad early captures reduced.

### Phase 4: Mission Families

Goal:

- Replace one blended target score with mission-specific decisions.

Build:

- Capture, rescue, reinforce, recapture, snipe, swarm, and evacuation as separate generators.
- Normalize candidate scoring so each mission can compete after validity checks.

Review output:

- Per-turn chosen mission log for sample seeds.
- No mission family starves all others unless intentionally gated.

### Phase 5: Forward Simulation Filter

Goal:

- Avoid captures that immediately flip back or weaken us into a loss.

Build:

- Short horizon forward sim for candidate launches.
- Compare no-action vs candidate-action score.
- Keep it bounded for Kaggle timeout.

Review output:

- Runtime per turn.
- Examples where a high raw score candidate is correctly rejected.

### Phase 6: 2P / 4P Strategy Split

Goal:

- Stop using the same aggression profile for duels and free-for-all.

Build:

- 2P: direct pressure, front-line attack, elimination.
- 4P: avoid overextension, target leader or weak exposed player depending on board, avoid donating captured planets to third parties.

Review output:

- Separate benchmark tables for 2P and 4P.
- Manual replay check for 4P overextension.

### Phase 7: Parameter Search

Goal:

- Improve weights without hand guessing.

Build:

- Small JSON/config block for tunable constants.
- Random search or evolutionary search over stable logic.
- Use fixed seed sets and opponent pool.

Review output:

- Top parameter sets.
- Overfit check on holdout seeds.

### Phase 8: Learning Layer

Goal:

- Use learning only where it has leverage.

Options:

- Imitation learning over mission selection from strong self-play/replay data.
- Value model to rank candidate missions.
- PPO only over pruned discrete candidate actions, not raw continuous angles.
- MCTS/beam search only over a small mission set.

Review output:

- Learning model must beat the heuristic selector on held-out local seeds before replacing it.
- If not, keep it as a scoring feature only.

## Key Design Constraints

- Keep the submission single-file compatible.
- Avoid heavy dependencies.
- Keep per-turn runtime under Kaggle timeout with margin.
- Preserve deterministic behavior unless deliberately testing stochastic tie-breaks.
- Every change should be reversible and benchmarked.

## Main Failure Modes To Watch

- Scoring a target before verifying the shot can actually hit.
- Using current target position instead of ETA position.
- Treating two small fleets as equivalent to one large fleet even though speed differs.
- Capturing a planet that the enemy can immediately retake.
- Sending long cross-map fleets that remove ships from the useful front.
- Overdefending the first visible threat and losing elsewhere.
- Winning 2P changes that worsen 4P.
- Optimizing public/local seeds too tightly.

