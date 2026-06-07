# Deterministic Research Clones

These files are for local research evaluation only. Do not submit them.

Purpose:
- Disable the agent soft deadline by calling `plan_moves(world, deadline=None)`.
- Separate strategy quality from CPU timing noise in local comparisons.

Production checks must still use the original files because Kaggle submissions
need to respect `actTimeout`.
