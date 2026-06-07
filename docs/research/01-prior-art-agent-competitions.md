# Prior Art From Similar Agent Competitions

## Executive Summary

Across similar game-agent competitions, the repeatable pattern is:

- Strong entrants usually build a reliable simulator-facing bot first.
- The key layers are physics, future-state prediction, candidate generation, value scoring, and action commitment.
- Learning methods are most useful after action pruning and after a strong baseline exists.
- Parameter tuning is practical; training a full policy from scratch is expensive and brittle.
- For Orbit Wars specifically, moving-target aiming and arrival-time ownership are more important than another flat target-score formula.

## Orbit Wars Public Baseline Pattern

Pilkwang Kim's structured baseline methodology frames Orbit Wars as online multi-agent control with delayed action resolution, where launches chosen now resolve after movement, production, existing fleets, and combat. The core operating rule is to find a legal direct shot, forecast the target at the real arrival time, and spend ships only if the mission still makes sense after prior launches are committed.

Important transferable patterns:

- Separate `physics -> world model -> strategy`.
- Do not score illegal or physically suspect shots.
- Evaluate targets at ETA, not at the current snapshot.
- Treat capture, rescue, reinforce, recapture, snipe, and swarm as different mission contracts.
- Use commitment-aware planning so accepted launches become future facts.

Source: [Orbit Wars: Structured Baseline Methodology](https://pilkwangkim.github.io/posts/Orbit-Wars-Structured-Baseline/)

## Planet Wars / Galcon-Like Strategy

Orbit Wars is explicitly close to Planet Wars/Galcon-style planet conquest, but with continuous geometry, moving planets, and comets. The older strategic lessons still map well.

Transferable ideas:

- Basic tactical goals are taking neutral planets, taking enemy planets, and defending owned planets.
- Ship positioning matters because ships should support future goals, not just current targets.
- Reaction time/latency matters: a planet near the enemy's reinforcement network is hard to hold even if cheap to capture.
- Long moves have opportunity cost because ships in flight are unavailable.
- Greedy expansion and aggression need balance; both can lose if overdone.
- A doomed planet should sometimes evacuate ships into a useful counterattack instead of passively losing them.
- Tacking is valuable: pressure one area to pull defense, then attack another underprotected area.

Source: [Planet Wars strategy](https://satirist.org/ai/planetwars/strategy.html)

Relevant research also treats fast Planet Wars variants as useful Game AI testbeds because the game is simple to state but strategically deep, and because fast simulation enables rapid experiments.

Sources:

- [Game AI Research with Fast Planet Wars Variants](https://arxiv.org/abs/1806.08544)
- [Efficient Evolutionary Methods for Game Agent Optimisation](https://arxiv.org/abs/1901.00723)

## Kore 2022

Kore 2022 is a Kaggle simulation competition with fleet launch planning and delayed effects. The relevant lesson is not the exact rules; it is the design pressure created by path planning and visible future fleet trajectories.

Observed patterns:

- First places in the beta phase were rule-based agents with simple heuristics.
- Strong solutions framed flight-plan selection as path planning.
- Future positions of fleets were useful features because plans were visible.
- Graph representations were proposed because board symmetry matters and future-timestamp nodes can carry delayed-effect information.
- Imitation learning from strong agents is plausible, but it depends on a good action representation.

Sources:

- [Applying Graph Neural Networks to Kaggle Competition](https://astralord.github.io/posts/applying-graph-neural-networks-to-kaggle-competition/)
- [Kaggle Solutions list, Kore 2022 section](https://dawiddworak88.github.io/kaggle-solutions/)

Orbit Wars implication:

- Maintain a future arrival ledger for all visible fleets.
- Do not treat a launch as an immediate effect.
- Use symmetry carefully, but break symmetry in tie cases to avoid self-play stagnation.
- If learning is attempted, predict over pruned target/source/ship candidates rather than raw continuous angles.

## Hungry Geese

Hungry Geese is not a planet conquest game, but it is a Kaggle multi-agent game with sparse rewards, collision risk, and strong benefit from search and imitation.

Observed patterns:

- A high-performing approach used behavior cloning, reinforcement learning, modified MCTS evaluation, strong handcrafted features, and iterative imitation from newer stronger agents.
- Compute cost was significant.
- Practical optimizations included saving time when only one valid move exists and batching inference.
- Candidate agents were evaluated against standard agents, filtered by win rate, and ranked in a local arena.

Source: [Kaggle Hungry Geese deck](https://d1eu30co0ohy4w.cloudfront.net/hoxomaxwell/kaggle-hungry-geese)

Orbit Wars implication:

- Build a local arena before chasing learning.
- Use self-play/episode data only after a strong heuristic policy can generate meaningful games.
- If MCTS/search is added, restrict it to high-value candidate missions rather than raw action branching.

## Halite

Halite competitions are useful because many strong bots were practical rule-based systems with tuned parameters.

Observed patterns:

- Rule-based bots can perform well when strategy modes are explicit.
- One Halite writeup used separate strategies such as balanced expansion, aggressive opening, and mining/economy-first behavior.
- Genetic algorithms are useful for tuning a parameterized bot, not for inventing the bot from scratch.
- Parameter tuning becomes expensive unless the bot and local evaluation loop are fast.

Sources:

- [Halite - A rule-based AI bot](https://muetsch.io/halite-a-rule-based-ai-bot.html)
- [Genetic Algorithm Bot | Halite AI Challenge](https://halite3webapp.azurewebsites.net/learn-programming-challenge/tutorials/ml-ga)

Orbit Wars implication:

- Define strategy modes explicitly: opening expansion, defense, pressure, total-war endgame.
- Expose key constants for tuning.
- Use local tournaments to tune weights after the logic is stable.

## Lux AI

Lux AI is useful because it separates high-level decision making from low-level action execution. That split maps directly to Orbit Wars.

Observed patterns:

- A greedy heuristic agent was broken into decision making and action taking.
- Rule-based RL was used to learn parameters for handcrafted policies, reducing the burden of learning obvious rules from scratch.
- Learned parameters helped avoid bad emergent behavior such as workers clustering on the same resources.

Source: [LuxAI Season 1 writeup](https://michaelriedl.com/writeups/LuxAIs01.html)

Orbit Wars implication:

- Separate mission selection from shot execution.
- Parameter learning can be valuable after rules exist.
- Avoid making neural/RL policy responsible for basic legality, geometry, or combat rules.

## Current Orbit Wars Community Signals

Community discussion around Orbit Wars points in the same direction:

- The action space is huge but pruneable.
- PPO/AlphaZero-style attempts can struggle without reward shaping and action pruning.
- Heuristic-first approaches are common because they expose where mechanics and replay patterns break down.
- Holding planets long enough for production to pay off is a central difficulty, especially in 4-player games.

Sources:

- [r/reinforcementlearning Orbit Wars thread](https://www.reddit.com/r/reinforcementlearning/comments/1t15z3k/anyone_participating_in_orbit_wars_on_kaggle_50k/)
- [r/kaggle Orbit Wars thread](https://www.reddit.com/r/kaggle/comments/1t1769f/orbit_wars_welp_there_goes_my_weekend/)
- [Orbit Wars note by Hyperion](https://note.com/hyperion_ai/n/n29284bb7e0de)

## What This Means For This Repo

The next implementation base should not be "make the target score smarter" in isolation. The base should be:

1. A reproducible benchmark harness.
2. A physics audit for shot legality and ETA.
3. An arrival ledger for visible fleets.
4. A projected owner/garrison function.
5. Mission families with separate validity checks.
6. A commitment loop.
7. Parameter search on top.
8. Optional imitation/RL after action pruning.

