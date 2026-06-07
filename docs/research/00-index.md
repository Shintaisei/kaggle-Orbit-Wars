# Orbit Wars Research Index

This folder turns prior-agent research into implementation steps for this repository.

## Documents

- [01-prior-art-agent-competitions.md](01-prior-art-agent-competitions.md)
  - What worked in similar bot competitions: Orbit Wars public baselines, Planet Wars, Kore 2022, Hungry Geese, Halite, and Lux AI.
- [02-orbit-wars-roadmap.md](02-orbit-wars-roadmap.md)
  - The recommended architecture and staged implementation path for this codebase.
- [03-action-review-cards.md](03-action-review-cards.md)
  - Reviewable action cards. Each card has a hypothesis, edit scope, tests, success criteria, and a stop/review decision.
- [04-public-notebook-game-map.md](04-public-notebook-game-map.md)
  - What the local public-notebook-derived agents imply about Orbit Wars' actual game dynamics and winning playbook.
- [05-reviewed-action-playbook.md](05-reviewed-action-playbook.md)
  - Concrete action sequence with reviewer prompts and pass/fail criteria for each implementation step.
- [06-autonomous-improvement-log.md](06-autonomous-improvement-log.md)
  - Chronological implementation and evaluation log for the autonomous improvement loop.
- [07-submission-postmortem-and-next-plan.md](07-submission-postmortem-and-next-plan.md)
  - Post-submit score interpretation, rejected loops, and the current promotion gates.
- [08-scored-candidate-analysis-and-improvement-backlog.md](08-scored-candidate-analysis-and-improvement-backlog.md)
  - Latest scored-candidate analysis and the reviewable backlog for the next improvement loop.

## Current Read

The strongest near-term path is not raw PPO/AlphaZero first. It is:

1. Build or verify the physics layer.
2. Build or verify the world model and arrival ledger.
3. Score mission families separately.
4. Commit actions one by one so later candidates see earlier launches.
5. Add local tournament evaluation and parameter search.
6. Only then add imitation learning or RL on a pruned action space.

The local repo already contains public Orbit Wars notebook-derived agents under `notebooks/`, and the current `main.py` appears to be an adapted public heuristic notebook rather than the tiny `baselines/path_safe_v1.py` baseline. Future work should treat `main.py` as an advanced but audit-heavy codebase, not as a clean minimal baseline.

As of the latest scored-candidate analysis, `candidates/production_candidate.py` / Loop046 is the current latest-observed public-LB leader and the working champion for future experiments. The next loop should branch from Loop046, run diagnostics first, and make only one reviewed micro-change at a time. `main.py` remains the previous-best fallback until a separate promotion review approves overwriting it.

## Review Rhythm

For each action card:

1. Run the baseline benchmark before edits.
2. Make only the named edit.
3. Run the same benchmark after edits.
4. Record result in the card.
5. Review whether to keep, tune, or revert the change.
