"""Load (or synthesize) this-period vs last-period leaf numbers.

data/periods.csv columns: metric, last_period, this_period, note
Only leaf metrics of the tree need rows; parents are derived from the tree.
"""
import argparse
import csv

from config import DATA_DIR, METRIC_TREE, PERIODS_CSV

# Scenario: GMS ~ -8%, driven mostly by a mobile conversion drop.
MOCK_ROWS = [
    ("Traffic", 10_000_000, 9_850_000, "Sessions; -1.5% WoW, within normal range"),
    ("Conversion", 0.0320, 0.0301, "Mobile app/web conversion fell ~12%; desktop flat"),
    ("ASP", 42.00, 41.70, "Mix shift toward lower-priced items; -0.7%"),
]


def leaves() -> list[str]:
    return [n for n, spec in METRIC_TREE.items() if not spec["children"]]


def write_mock(path=PERIODS_CSV) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["metric", "last_period", "this_period", "note"])
        w.writerows(MOCK_ROWS)


def load_periods(path=PERIODS_CSV) -> dict[str, dict]:
    """Return {leaf: {"last": float, "this": float, "note": str}}."""
    if not path.exists():
        raise FileNotFoundError(f"{path} not found. Create it, or run with --mock.")
    out = {}
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            out[row["metric"].strip()] = {
                "last": float(row["last_period"]),
                "this": float(row["this_period"]),
                "note": (row.get("note") or "").strip(),
            }
    missing = [m for m in leaves() if m not in out]
    if missing:
        raise ValueError(f"periods.csv is missing leaf metrics: {missing}")
    return out


def run(mock: bool = False) -> dict[str, dict]:
    if mock:
        write_mock()
        print(f"[generate] wrote mock scenario -> {PERIODS_CSV}")
    data = load_periods()
    print(f"[generate] loaded {len(data)} leaf metrics from {PERIODS_CSV}")
    return data


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--mock", action="store_true")
    run(ap.parse_args().mock)
