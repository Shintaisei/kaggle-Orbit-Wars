# Kaggle Orbit Wars

Research workspace and submission code for the Kaggle [Orbit Wars](https://www.kaggle.com/competitions/orbit-wars/overview) competition.

The primary Kaggle submission file is `main.py`. It is a single-file heuristic agent with local candidate variants, evaluation scripts, and notes used during iterative tuning.

## Repository Layout

```text
.
|-- main.py                         # Current single-file submission agent
|-- test_local.py                   # Local evaluator using kaggle-environments
|-- review_action_accuracy.py       # Action/replay inspection helper
|-- requirements.txt                # Lightweight Python requirements
|-- setup_windows.ps1               # Windows environment bootstrap
|-- baselines/                      # Earlier baseline agents
|-- candidates/                     # Iteration candidates and research variants
|-- docs/research/                  # Research notes, logs, and tuning plan docs
|-- eval_clones/                    # Deterministic local-only clones
|-- external/                       # External/public reference agents
|-- locked_submissions/             # Exact snapshots of important Kaggle submissions
|-- notebooks/                      # Referenced public notebooks and exports
|-- tools/                          # Evaluation and analysis utilities
`-- variants/                       # Named public/reference variants
```

Generated files such as `__pycache__`, `data`, `logs`, `replays`, and `eval_results` are intentionally ignored by Git.

## Setup

On Windows, this project uses `C:\owv` for the virtual environment because the full `kaggle-environments` dependency tree can hit path length limits inside OneDrive workspaces.

```powershell
.\setup_windows.ps1
```

Activate the environment:

```powershell
C:\owv\Scripts\Activate.ps1
```

Install the lightweight requirements:

```powershell
C:\owv\Scripts\python.exe -m pip install -r requirements.txt
```

Install `kaggle-environments` separately with no dependencies:

```powershell
C:\owv\Scripts\python.exe -m pip install --no-deps kaggle-environments==1.28.0
```

## Local Evaluation

Run a small smoke test against the built-in random agent:

```powershell
C:\owv\Scripts\python.exe test_local.py --games 5
```

Evaluate the current agent against a specific opponent:

```powershell
C:\owv\Scripts\python.exe test_local.py --agent main.py --opponents locked_submissions\53418690_vickimar_heuristic_fixed_SCORE_908_0.py --games 20 --seats 2
```

Run both 2-player and 4-player checks:

```powershell
C:\owv\Scripts\python.exe test_local.py --agent main.py --opponents random --games 10 --seats 2,4 --rotate-seats --out eval_results\smoke_main.jsonl
```

## Kaggle CLI

Check the Kaggle CLI:

```powershell
C:\owv\Scripts\kaggle.exe --version
```

Log in to Kaggle:

```powershell
C:\owv\Scripts\kaggle.exe auth login
```

Verify the competition:

```powershell
C:\owv\Scripts\kaggle.exe competitions list -s "orbit wars"
```

Download competition files:

```powershell
C:\owv\Scripts\kaggle.exe competitions download orbit-wars -p data
```

Submit the current single-file agent:

```powershell
C:\owv\Scripts\kaggle.exe competitions submit orbit-wars -f main.py -m "submission message"
```

## Notes

- `main.py` is adapted from public Kaggle Orbit Wars notebooks and local heuristic iterations.
- `locked_submissions/README.md` records exact submission snapshots and observed public scores.
- `eval_clones/` files disable soft deadline behavior for deterministic local research only. Do not submit them to Kaggle.
- The competition page listed entries closing on June 16, 2026 and final submissions closing on June 23, 2026 at 11:59 PM UTC.
