# Why Did This Metric Move? — metric decomposition engine

Given a metric tree and two periods of numbers, find which leaf driver caused a
top-line movement, quantify each driver's contribution, and render a waterfall
chart plus a one-page WBR-style HTML report. No API keys, no paid services.

## Quick start

```powershell
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
python main.py --mock        # synthesizes a scenario, runs everything
start output\index.html
```

Without `--mock`, `main.py` reads `data/periods.csv`:

```csv
metric,last_period,this_period,note
Traffic,10000000,9850000,Sessions
Conversion,0.0320,0.0301,Mobile conversion fell
ASP,42.00,41.70,
```

Only **leaf** metrics need rows; parents are computed from the tree.

## Pipeline

| Step | File | Output |
|---|---|---|
| 1. load / mock data | `generate.py` | `data/periods.csv` (mock only) |
| 2. decompose | `decompose.py` | `data/decomposition.json` + reconciliation check |
| 3. chart | `waterfall.py` | `output/waterfall.png` |
| 4. render | `render.py` + `templates/index.html.j2` | `output/index.html` |
| orchestrate | `main.py [--mock]` | all of the above |
| narrative (manual) | `narrate.py` | prompt to paste into Claude.ai |

`config.py` holds the metric tree, thresholds, paths and the teal theme.

## How the decomposition works

`GMS = Units x ASP`, `Units = Traffic x Conversion`. For a product node,

```
dP = dA*B_last + dB*A_last  +  dA*dB
     \_____ first-order ___/    \_ interaction (cross term)
```

First-order terms are attributed to each child; the cross term is reported
explicitly as an "interaction" line so contributions sum **exactly** to the
top-line change. The same split is applied recursively, scaling each leaf by
its ancestors' sibling multipliers so every contribution is in GMS units.
The root cause is the largest leaf pushing in the direction of the move.
`main.py` prints a reconciliation check (interaction must be within
`RECON_TOLERANCE_PCT` of the total change).

## Adding nodes

Edit `METRIC_TREE` in `config.py` — give a node `children` and it becomes the
product of them; add a `periods.csv` row for each new leaf. Only product
relationships are supported today.

## Narrative workflow (no API)

1. `python narrate.py` prints a ready-made prompt.
2. Paste it into Claude.ai; save the reply to `data/narrative.txt`.
3. `python main.py` (or `python render.py`) embeds it in the report. Until then
   the report shows a short auto-generated summary.

## Notes

- The waterfall's y-axis is truncated so driver steps are readable; the chart says so.
- `data/` is git-ignored, so keep your real `periods.csv` elsewhere if you commit.
