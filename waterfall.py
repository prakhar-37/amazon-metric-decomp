"""Waterfall chart: last-period top line -> driver steps -> this-period top line."""
import json

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

from config import (DECOMP_JSON, NEGATIVE, OUTPUT_DIR, PERIOD_LAST_LABEL, PERIOD_THIS_LABEL,
                    POSITIVE, ROOT_CAUSE, TEAL, WATERFALL_PNG)  # noqa: E402
from fmt import fmt_usd_delta, fmt_value  # noqa: E402


def build(result: dict, path=WATERFALL_PNG) -> None:
    root = result["root"]
    steps = [(l["label"], l["contribution"], l["name"] == result["root_cause"]["name"])
             for l in result["leaves"]]
    steps += [(i["label"], i["contribution"], False) for i in result["interactions"]
              if abs(i["contribution"]) > 0]

    labels = [f"{PERIOD_LAST_LABEL}\n{root}"] + [s[0].replace(" (", "\n(") for s in steps] + \
             [f"{PERIOD_THIS_LABEL}\n{root}"]
    fig, ax = plt.subplots(figsize=(10, 5.2), dpi=150)

    running = result["last"]
    ax.bar(0, running, color=TEAL, width=0.6)
    ax.text(0, running, fmt_value(root, running), ha="center", va="bottom", fontsize=9, fontweight="bold")
    tops = [running]
    bottoms = [running]
    for i, (_, c, is_root) in enumerate(steps, 1):
        lo = min(running, running + c)
        color = ROOT_CAUSE if is_root else (POSITIVE if c >= 0 else NEGATIVE)
        ax.bar(i, abs(c), bottom=lo, color=color, width=0.6)
        ax.plot([i - 1 + 0.3, i - 0.3], [running, running], color="#64748b", lw=0.8)
        ax.text(i, max(running, running + c), fmt_usd_delta(c), ha="center", va="bottom", fontsize=9,
                fontweight="bold" if is_root else "normal", color=ROOT_CAUSE if is_root else "#334155")
        running += c
        tops.append(max(running, running - c))
        bottoms.append(lo)
    n = len(steps) + 1
    ax.plot([n - 1 + 0.3, n - 0.3], [running, running], color="#64748b", lw=0.8)
    ax.bar(n, result["this"], color=TEAL, width=0.6)
    ax.text(n, result["this"], fmt_value(root, result["this"]), ha="center", va="bottom",
            fontsize=9, fontweight="bold")

    # Zoom the y-axis so driver steps are legible; the totals' bars are truncated.
    lo, hi = min(bottoms + [result["this"]]), max(tops + [result["this"]])
    pad = (hi - lo) * 0.35 or hi * 0.05
    ax.set_ylim(lo - pad, hi + pad * 0.6)
    ax.set_xticks(range(n + 1))
    ax.set_xticklabels(labels, fontsize=8)
    ax.yaxis.set_major_formatter(lambda v, _: fmt_value(root, v))
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.set_title(f"Why did {root} move {result['pct_change']:+.1f}%?  "
                 f"Root cause: {result['root_cause']['label']}",
                 loc="left", fontsize=12, fontweight="bold", color="#0f172a")
    ax.text(0, -0.2, "Y-axis truncated to show driver steps. Red = root cause; "
            "interaction = cross term of simultaneous changes.",
            transform=ax.transAxes, fontsize=7.5, color="#64748b")
    fig.tight_layout()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    fig.savefig(path)
    plt.close(fig)
    print(f"[waterfall] wrote {path}")


def run(result: dict | None = None) -> None:
    if result is None:
        result = json.loads(DECOMP_JSON.read_text(encoding="utf-8"))
    build(result)


if __name__ == "__main__":
    run()
