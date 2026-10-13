"""Central configuration: metric tree, thresholds, paths, theme.

To extend the tree, add a node to METRIC_TREE. A node with a non-empty
"children" list is computed as the PRODUCT of its children; a node without
children is a leaf and must have a row in data/periods.csv.

Example - split ASP into list price x (1 - discount):
    "ASP":      {"label": "ASP", "fmt": "usd2", "children": ["ListPrice", "NetRate"]},
    "ListPrice": {"label": "List price", "fmt": "usd2", "children": []},
    "NetRate":   {"label": "1 - discount", "fmt": "pct", "children": []},
"""
from pathlib import Path

# ---------------------------------------------------------------- metric tree
ROOT = "GMS"

# fmt: usd (big $ totals), usd2 ($ with cents), int (counts), pct (fraction -> %)
METRIC_TREE = {
    "GMS": {"label": "GMS", "fmt": "usd", "children": ["Units", "ASP"]},
    "Units": {"label": "Units", "fmt": "int", "children": ["Traffic", "Conversion"]},
    "ASP": {"label": "ASP", "fmt": "usd2", "children": []},
    "Traffic": {"label": "Traffic (sessions)", "fmt": "int", "children": []},
    "Conversion": {"label": "Conversion", "fmt": "pct", "children": []},
}

# ----------------------------------------------------------------- thresholds
# Top-line moves smaller than this (abs %) are reported as "flat".
MATERIALITY_PCT = 1.0
# Reconciliation passes if the cross (interaction) terms are within this
# share of the total change.
RECON_TOLERANCE_PCT = 10.0
# A root cause is "dominant" if it explains at least this share of the move.
DOMINANT_SHARE_PCT = 50.0

# ---------------------------------------------------------------------- paths
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
OUTPUT_DIR = BASE_DIR / "output"
TEMPLATE_DIR = BASE_DIR / "templates"

PERIODS_CSV = DATA_DIR / "periods.csv"
DECOMP_JSON = DATA_DIR / "decomposition.json"
NARRATIVE_TXT = DATA_DIR / "narrative.txt"
WATERFALL_PNG = OUTPUT_DIR / "waterfall.png"
REPORT_HTML = OUTPUT_DIR / "index.html"

# ---------------------------------------------------------------------- theme
TEAL = "#0d9488"
TEAL_DARK = "#0f766e"
TEAL_LIGHT = "#ccfbf1"
NEGATIVE = "#94a3b8"   # non-root-cause decreases (muted)
POSITIVE = "#2dd4bf"   # increases
ROOT_CAUSE = "#dc2626" # highlighted root cause

PERIOD_LAST_LABEL = "Last period"
PERIOD_THIS_LABEL = "This period"
