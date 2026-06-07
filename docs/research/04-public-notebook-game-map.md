# Orbit Wars Game Map From Public Notebook-Derived Agents

This document summarizes what the currently collected public notebook-derived agents imply about the game. It focuses on how to play the game well, not just how each file is structured.

Local sources inspected:

- `main.py`
- `variants/vicki_fixed.py`
- `variants/roman_lb1224.py`
- `variants/suneet_lb1200.py`
- `variants/rahul_target2000.py`
- `notebooks/vicki-lb-1110/orbit-wars-heuristic-lb-1110.py`
- `notebooks/roman-lb-1224/orbit-star-wars-lb-max-1224.py`
- `notebooks/suneet-lb-1200/lb-1200-orbit-wars-ppo-strategy.py`
- `notebooks/rahul-target-2000/orbit-wars-target-score-2000-4.py`

External context:

- [Orbit Wars structured baseline methodology](https://pilkwangkim.github.io/posts/Orbit-Wars-Structured-Baseline/)
- [Planet Wars strategy notes](https://satirist.org/ai/planetwars/strategy.html)
- [Kore 2022 graph/path-planning writeup](https://astralord.github.io/posts/applying-graph-neural-networks-to-kaggle-competition/)
- [Hungry Geese MCTS/BC/RL deck](https://d1eu30co0ohy4w.cloudfront.net/hoxomaxwell/kaggle-hungry-geese)

## Top-Level Conclusion

The public notebook direction is converging on this:

```text
Do not think of Orbit Wars as "pick the best target".
Think of it as "commit delayed effects into a moving combat simulator".
```

Good play requires:

1. Legal shot physics.
2. ETA-based target projection.
3. Existing fleet arrival accounting.
4. Mission-specific contracts.
5. Commitment-aware planning.
6. 2-player and 4-player strategy split.
7. A benchmark loop to prevent overfitting one tactical idea.

The strongest reusable pattern is Roman/Suneet's structured mission compiler plus Vicki's mature edge-case guardrails. Rahul's compact hybrid search ideas are interesting, but its normalized variant has rough physics assumptions and should not be copied as the base.

## Official Mechanics That Drive Strategy

The installed environment's README and interpreter define the strategy surface:

- The board is continuous 2D, not grid-based.
- Actions are launches: `[from_planet_id, direction_angle, num_ships]`.
- A launch does not target a planet by ID; it only picks a ray and ship count.
- The game lasts up to 500 turns.
- Final score is total owned ships on planets plus ships in fleets.
- Production happens before fleet movement each turn.
- Fleet movement uses continuous collision detection against sun and planets.
- Orbiting planets move after fleet movement, then can sweep fleets into combat.
- Combat groups same-turn arrivals by owner and resolves largest force versus second largest before fighting the garrison.
- Comets spawn at fixed windows, move along known paths, produce if owned, and disappear with their garrison when they leave.
- Launches are processed before production, so a source budget must use the observed garrison only; ships produced this turn cannot be spent until a later turn.

Strategic consequences:

- A "target" is a planning abstraction, not an action primitive.
- The same source-target pair can require a different angle when ship count changes.
- ETA errors affect combat, production, and whether a target still exists.
- A valid capture at ETA can still be a bad move if it cannot be held.
- Final-turn ship accounting means late neutral expansion should be filtered by payoff time.
- Existing fleets do not expose target IDs; any arrival ledger must infer the first collision, not merely the nearest intended target.

## Notebook Families

### Vicki Lineage

Files:

- `variants/vicki_fixed.py`
- `notebooks/vicki-lb-1110/orbit-wars-heuristic-lb-1110.py`
- Current `main.py` appears to follow this lineage.

Core idea:

- Large sequential heuristic pipeline with persistent tactical state.

Important components:

- Physics and ETA:
  - `fleet_speed`
  - `segment_hits_sun`
  - `predict_target_position`
  - `aim_at_target`
  - `plan_solo_capture`
- World model:
  - `World`
  - `collect_arrivals`
  - `effective_garrison_at_arrival`
  - `forward_project`
- Mission handlers:
  - `handle_comet_evac`
  - `handle_defense`
  - `handle_expand`
  - `handle_accumulator`
  - `handle_mega_hammer`
  - `handle_hammer`
  - `handle_multiprong`

What it teaches about the game:

- Exact ship count matters because fleet speed depends on ship count; aim must be recomputed after deciding how many ships to send.
- A planet that looks cheap now can become expensive at ETA because production and fleets resolve before arrival.
- Existing enemy fleets are not just threats; they create snipe opportunities and traps.
- Big stockpiled attacks can matter because large fleets are faster and can punch through growing garrisons.
- Global commitment memory is strategically useful, but risky if it becomes stale.

Likely strengths:

- Practical guardrails.
- Strong anti-snipe and tempo filters.
- Explicit 2P/4P mode behavior.
- Mature edge-case handling for comets, doomed planets, stockpiles, and hammers.

Likely risks:

- Too many flags and constants.
- Sequential handlers can starve later missions.
- Global state can leak across games if not reset carefully.
- Hard to attribute a win/loss to one rule.

### Roman Lineage

Files:

- `variants/roman_lb1224.py`
- `notebooks/roman-lb-1224/orbit-star-wars-lb-max-1224.py`

Core idea:

- Clean mission compiler.

Important components:

- Data contracts:
  - `ShotOption`
  - `Mission`
- Physics:
  - `aim_with_prediction`
  - `search_safe_intercept`
- World model:
  - `WorldModel`
  - `build_arrival_ledger`
  - `simulate_planet_timeline`
  - `projected_state`
  - `reinforcement_needed_to_hold_until`
  - `ships_needed_to_capture`
- Mission builders:
  - `build_snipe_mission`
  - `build_rescue_missions`
  - `build_recapture_missions`
  - `build_reinforce_missions`
  - `build_crash_exploit_missions`
  - `build_gang_up_missions`
  - `build_elimination_missions`

What it teaches about the game:

- Mission families should be separate because each has different validity rules.
- A "capture" and a "rescue" are not the same scoring problem.
- 4P needs player-level reasoning: weakest-enemy finishing, gang-up timing, and elimination are explicit Roman themes; Vicki contributes more explicit leader-containment/leader-bash style logic.
- A timeline model per planet is a central primitive.
- A candidate should become a `Mission` only after shot feasibility and projected ownership are checked.

Likely strengths:

- Best architecture for future maintainability.
- Clear responsibilities.
- Better suited for review and incremental testing than Vicki's monolithic pipeline.

Likely risks:

- Many scoring constants still need tuning.
- 4P weakest-enemy pressure can be wrong when leader containment is more urgent.
- Route probing and mission generation can become expensive.

### Suneet Lineage

Files:

- `variants/suneet_lb1200.py`
- `notebooks/suneet-lb-1200/lb-1200-orbit-wars-ppo-strategy.py`

Core idea:

- Structured baseline derivative with aggressive tuning. Despite the PPO title, the local file is mostly handcrafted world modeling and mission logic.

Important components:

- Same general architecture as Roman:
  - `ShotOption`
  - `Mission`
  - `WorldModel`
  - arrival ledger
  - planet timelines
  - mission builders
- Distinct emphasis:
  - quick reinforcement pass
  - domination consolidation
  - more aggressive finishing behavior

What it teaches about the game:

- Reinforcing nearby under-defended owned planets before main mission selection can stabilize the empire.
- When ahead, pure expansion can become too passive; advantage should convert into pressure.
- However, "being ahead" must be measured carefully in 4P because overextension can donate value to third parties.

Likely strengths:

- Good source for "shore up weak allies first".
- Good source for "convert lead into attacks".

Likely risks:

- Quick reinforcement can spend ships that should have gone to high-value attack/rescue missions.
- Domination consolidation can overextend if the lead estimate is wrong.
- The PPO label should not bias us into thinking this is a learned policy.

### Rahul Lineage

Files:

- `variants/rahul_target2000.py`
- `notebooks/rahul-target-2000/orbit-wars-target-score-2000-4.py`

Core idea:

- Compact hybrid search/evaluator stack: predictor, short simulator, MCTS, opponent model, fleet interception, comet opportunism, diplomacy, beam search, counterfactual risk, strategy engine.

Important components:

- `GameState`
- `Predictor`
- `sim_step`
- `EliteEval`
- `MCTSEngine`
- `OpponentModel`
- `FleetInterceptor`
- `CometOpp`
- `DiplomacyEngine`
- `BeamSearch`
- `CounterfactualRisk`
- `StrategyEngine`

What it teaches about the game:

- A bounded search wrapper over candidate actions can be useful.
- Diplomacy/4P pressure and counterfactual risk are real concerns.
- Compactness makes iteration easier.

Major caveat:

- The normalized variant uses rough physics assumptions compared with the official rule implementation and other variants:
  - simple `1 + ships // 20` speed formula,
  - sun radius mismatch,
  - angle-threshold fleet target inference,
  - broad `try/except` hiding disabled subsystems.

Likely strengths:

- Search framing is useful as a later selector.
- Easy to read compared with Vicki.

Likely risks:

- Physics mismatch can invalidate tactical conclusions.
- MCTS/beam over bad candidates amplifies errors.
- Should be mined for ideas, not used as the base.

## The Game's Real Axes

### 1. Physics Is A Gate, Not A Scoring Feature

Bad pattern:

```text
score target -> aim -> hope it lands
```

Good pattern:

```text
candidate target -> legal shot -> ETA state -> mission score -> commit
```

Required facts:

- Fleet speed depends on ships.
- Changing send size changes ETA and sometimes the angle.
- Static planets are much easier to hit than orbiting planets.
- Comets require path-index/lifetime checks.
- Sun and planet collision should reject a shot before strategy scores it.
- A legal shot must verify it does not hit an unintended planet before the intended target.
- A legal shot must also account for moving planet/comet sweep after fleet movement.

Implementation rule:

- `plan_shot(source, target, ships)` must be a first-class primitive.

### 2. Arrival-Time Ownership Is The Center Of The Game

The current snapshot is often misleading.

On the ETA turn, the official order matters:

1. Expired comets are removed before launches.
2. New launches are created.
3. Owned planets produce.
4. Fleets move and collide.
5. Planets/comets move and can sweep fleets.
6. Combat resolves.

At ETA, the target may have:

- produced more ships,
- received friendly reinforcements,
- received enemy attacks,
- flipped owner,
- been removed if it is a comet.

Same-turn combat is not a raw sum. Arriving fleets are grouped by owner; the largest attacking owner group fights the second largest, ties erase both, and only the surviving attacker, if any, then interacts with the planet garrison.

Implementation rule:

- Every mission should ask `projected_state(target_id, eta, planned_commitments)` before deciding send size.

### 3. Holding Is More Important Than Capturing

Public notes and local notebook structure both emphasize that a capture is bad if it flips back before production pays off.

Practical forms:

- Safe neutral capture.
- Contested neutral capture.
- Enemy planet capture.
- Rescue-to-hold.
- Recapture after enemy overcommit.
- Snipe after enemy battle.

Implementation rule:

- A capture mission needs a hold check, not just `garrison + 1`.

### 4. Ships In Flight Have Opportunity Cost

Long flights:

- cannot defend,
- cannot react,
- can arrive after the strategic situation changed,
- may be slower if undersized,
- can create cross-map mistakes.

Implementation rule:

- Target value should subtract travel-time cost and reaction-time risk.

### 5. 2P And 4P Are Different Games

2P:

- Direct pressure works more often.
- Elimination and hammers are valuable.
- A weakening enemy usually benefits us.
- Expansion can stop earlier once production lead is enough.

4P:

- Overextension can benefit a third player.
- Leader pressure and weak-player finishing conflict.
- Safe/contested neutral distinction is more important.
- Snipe opportunities and third-party retakes matter.
- Diplomacy is implicit: the bot cannot negotiate, but it can exploit who is fighting whom.

Implementation rule:

- Keep separate mode parameters and mission gates for 2P and 4P.

### 6. Comets Are A Tactical Hypothesis, Not A Proven Core

Local public agents mostly treat comets with low chase horizons/value multipliers and evacuation rules, so the working hypothesis is that comets are tactical opportunities rather than the strategic core. This should be benchmarked, not assumed. Comets can be valuable if cheap and timely, but:

- they expire,
- path prediction matters,
- ships left on them disappear,
- chasing them can waste travel time.
- they spawn at fixed steps, start off-board, advance by `path_index`, and can be removed both before launch when already expired and after movement when they leave.
- evacuation must happen before the final observable turn where launching from that comet is still legal.

Implementation rule:

- Treat comets with short-horizon ROI and evacuation logic.

### 7. Big Fleets Are A Strategic Tool

Because larger fleets move faster, stockpiling can be rational:

- large fleet arrives sooner,
- large attack can overwhelm growing production,
- hammer-style synchronized attacks can break stable positions.

But stockpiling also creates risk:

- passive early game,
- one lost stockpile is catastrophic,
- hammers can be stale if enemy reinforcement projection is wrong.

Implementation rule:

- Big-fleet plans need explicit triggers, revalidation, and abort conditions.

## Practical Playbook

### Opening

Goals:

- Capture static or short-ETA neutrals.
- Avoid rotating planets that need unreliable lead aim unless payoff is high.
- Do not overpay for low-production neutral planets.
- Preserve enough reserve to survive first enemy pressure.
- Do not budget ships produced this turn; launches spend only the source's observed garrison.

Preferred missions:

- safe neutral capture,
- cheap pickup,
- quick local reinforcement,
- anti-snipe only when visible enemy fleet creates a clear opportunity.

Avoid:

- long cross-map captures,
- high-garrison low-production neutrals,
- early all-in enemy attacks unless target is exposed.

### Midgame

Goals:

- Convert production lead into map control.
- Defend high-production owned planets.
- Exploit enemy fleets already committed in flight.
- Recapture or snipe contested planets after battles.

Preferred missions:

- rescue,
- reinforce-to-hold,
- recapture,
- snipe,
- swarm,
- crash exploit,
- selective hostile capture.

Avoid:

- captures that flip back quickly,
- spending all front-line reserves on backline neutrals,
- chasing comets past their payback window.

### Endgame

Goals:

- Maximize final total ships.
- Stop low-ROI expansion.
- Attack when immediate score swing exceeds opportunity cost.
- Flush ships from doomed or expiring locations.

Preferred missions:

- total-war pressure,
- enemy high-production capture if ETA is short enough,
- evacuation,
- final fleet preservation,
- leader/weakest target depending on 2P/4P situation.

Avoid:

- neutral captures that cannot repay before turn 500,
- long flights that arrive too late,
- overdefending planets that are irrelevant to final score.

Scoring note:

- Raw final score is owned planet ships plus owned fleet ships.
- In the local environment, every player tied for top score receives reward `1`; reward alone can hide a draw, so benchmark logs need raw scores.

### 4P Accidental Value Donation

Free-for-all mistakes are not just "overextension". Specific donation patterns:

- Two attacking owners can tie in same-turn combat and erase both forces, leaving the planet unchanged for someone else.
- One attacker can weaken a garrison without capturing it, making a later third-party capture cheaper.
- Capturing an enemy planet near a third player's reinforcement network can hand them a cheaper target.
- Eliminating or farming the weakest enemy can benefit the current leader more than us.

Implementation rule:

- 4P target choice should score our projected rank delta, not only target owner weakness or local capture ROI.

## What To Copy, What Not To Copy

Copy:

- Roman/Suneet's `Mission` and `ShotOption` style.
- Roman/Suneet's planet timeline model.
- Vicki's exact physics discipline and re-aim-after-send-size rule.
- Vicki's anti-snipe, neutral tempo, and comet evacuation concepts.
- Suneet's quick reinforcement and lead-conversion ideas, after benchmarking.
- Rahul's search layer only as a later selector over valid missions.

Do not copy blindly:

- Public constants.
- Broad `try/except` around strategic systems.
- MCTS over raw target choices before physics validation.
- One giant target score that handles all mission types.
- 4P aggression settings from 2P.

## Recommended North Star

The next maintainable agent should look like this:

```text
parse obs
  -> build WorldModel
  -> simulate/validate in-flight fleet collision destinations
  -> build arrival ledger and planet timelines
  -> compute mode: 2P/4P, opening/mid/end, lead/behind
  -> generate mission candidates
  -> validate each candidate with exact shot physics
  -> project ownership and hold status at ETA
  -> score by mission contract
  -> commit best mission
  -> update planned arrivals/inventory
  -> repeat until budget/deadline
  -> return moves
```

The game is won less by a clever single formula and more by never lying to yourself about delayed consequences.
