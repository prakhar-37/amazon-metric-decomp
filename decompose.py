"""Core engine: attribute a top-line change to leaf drivers.

MATH
----
Every non-leaf node is a product of its children:  P = x1 * x2 * ... * xn.
Between periods each child moves by dxi = xi_this - xi_last, so

    dP = P_this - P_last
       = sum_i [ dxi * prod_{j != i} xj_last ]   (first-order terms)
       + cross terms                              (interaction, products of deltas)

For two children this is the formula  dP = dA*B_last + dB*A_last + dA*dB.
We attribute the first-order terms to the children and keep the cross term
as an explicit "interaction" item, so nothing is hidden and everything sums
exactly to dP.

Recursion: child i's first-order contribution to its parent is
dxi * prod(siblings_last). If that child is itself a product, its change dxi
is split the same way, and each grandchild's share is scaled by the same
multiplier. We carry that multiplier down as `scale`, so every leaf ends up
expressed in the ROOT metric's units:

    leaf contribution to root = d_leaf * scale
    scale(child i) = scale(parent) * prod_{j != i} xj_last

Because contributions are linear in each delta, then:
    root change = sum(leaf contributions) + sum(interaction terms)   (exact)
"""
import json
import math

from config import (DECOMP_JSON, DATA_DIR, DOMINANT_SHARE_PCT, MATERIALITY_PCT,
                    METRIC_TREE, RECON_TOLERANCE_PCT, ROOT)
from generate import load_periods


def node_values(leaf_vals: dict[str, float]) -> dict[str, float]:
    """Compute every node's value (bottom-up product) from leaf values."""
    memo: dict[str, float] = {}

    def val(name: str) -> float:
        if name not in memo:
            kids = METRIC_TREE[name]["children"]
            memo[name] = leaf_vals[name] if not kids else math.prod(val(k) for k in kids)
        return memo[name]

    for n in METRIC_TREE:
        val(n)
    return memo


def _pct(this: float, last: float) -> float:
    return (this / last - 1) * 100 if last else 0.0


def decompose(periods: dict[str, dict]) -> dict:
    leaf_names = [n for n, s in METRIC_TREE.items() if not s["children"]]
    last = node_values({n: periods[n]["last"] for n in leaf_names})
    this = node_values({n: periods[n]["this"] for n in leaf_names})

    total = this[ROOT] - last[ROOT]
    leaves: list[dict] = []
    interactions: list[dict] = []

    def walk(name: str, scale: float, path: list[str]) -> dict:
        spec = METRIC_TREE[name]
        d = this[name] - last[name]
        node = {
            "name": name, "label": spec["label"],
            "last": last[name], "this": this[name],
            "delta": d, "pct_change": _pct(this[name], last[name]),
            "contribution": d * scale,  # in root-metric units
            "children": [], "interaction": 0.0,
        }
        kids = spec["children"]
        if not kids:
            leaves.append({**{k: node[k] for k in
                              ("name", "label", "last", "this", "delta", "pct_change", "contribution")},
                           "path": path, "note": periods[name].get("note", "")})
            return node

        explained = 0.0
        for k in kids:
            siblings_last = math.prod(last[o] for o in kids if o != k)
            explained += (this[k] - last[k]) * siblings_last      # first-order term
            node["children"].append(walk(k, scale * siblings_last, path + [k]))
        cross = d - explained                                      # interaction (cross terms)
        node["interaction"] = cross * scale
        interactions.append({"parent": name, "label": f"{spec['label']} interaction",
                             "contribution": cross * scale})
        return node

    tree = walk(ROOT, 1.0, [ROOT])

    for l in leaves:
        l["share_of_change_pct"] = l["contribution"] / total * 100 if total else 0.0
        l["impact_on_root_pct"] = l["contribution"] / last[ROOT] * 100 if last[ROOT] else 0.0
    leaves.sort(key=lambda l: abs(l["contribution"]), reverse=True)
    for i, l in enumerate(leaves, 1):
        l["rank"] = i

    # Root cause: biggest leaf pushing in the same direction as the top-line move.
    same_dir = [l for l in leaves if total == 0 or l["contribution"] * total > 0]
    root_cause = (same_dir or leaves)[0]
    flat = abs(_pct(this[ROOT], last[ROOT])) < MATERIALITY_PCT

    leaf_sum = sum(l["contribution"] for l in leaves)
    inter_sum = sum(i["contribution"] for i in interactions)
    residual = total - leaf_sum - inter_sum                      # should be ~0 (float error)
    inter_pct = abs(inter_sum) / abs(total) * 100 if total else 0.0
    recon = {
        "total_change": total, "sum_leaf_contributions": leaf_sum,
        "sum_interaction": inter_sum, "unexplained_residual": residual,
        "interaction_pct_of_total": inter_pct,
        "tolerance_pct": RECON_TOLERANCE_PCT,
        "passed": abs(residual) < 1e-6 * max(1.0, abs(total)) and inter_pct <= RECON_TOLERANCE_PCT,
    }

    return {
        "root": ROOT, "root_label": METRIC_TREE[ROOT]["label"],
        "last": last[ROOT], "this": this[ROOT], "delta": total,
        "pct_change": _pct(this[ROOT], last[ROOT]),
        "direction": "flat" if flat else ("up" if total > 0 else "down"),
        "leaves": leaves, "interactions": interactions, "tree": tree,
        "root_cause": {**root_cause, "dominant": abs(root_cause["share_of_change_pct"]) >= DOMINANT_SHARE_PCT},
        "reconciliation": recon,
    }


def print_check(result: dict) -> None:
    from fmt import fmt_usd_delta
    r = result["reconciliation"]
    print(f"[decompose] {result['root']} change {fmt_usd_delta(r['total_change'])} "
          f"({result['pct_change']:+.2f}%)")
    for l in result["leaves"]:
        print(f"    {l['rank']}. {l['label']:<20} {fmt_usd_delta(l['contribution']):>10} "
              f"({l['share_of_change_pct']:5.1f}% of move)")
    for i in result["interactions"]:
        print(f"       {i['label']:<20} {fmt_usd_delta(i['contribution']):>10}")
    status = "PASS" if r["passed"] else "FAIL"
    print(f"[decompose] reconciliation {status}: drivers {fmt_usd_delta(r['sum_leaf_contributions'])} "
          f"+ interaction {fmt_usd_delta(r['sum_interaction'])} = "
          f"{fmt_usd_delta(r['sum_leaf_contributions'] + r['sum_interaction'])} "
          f"vs actual {fmt_usd_delta(r['total_change'])} "
          f"(interaction {r['interaction_pct_of_total']:.2f}% of total, tolerance {r['tolerance_pct']:.0f}%)")
    rc = result["root_cause"]
    print(f"[decompose] root cause: {rc['label']} ({rc['pct_change']:+.1f}%), "
          f"{rc['share_of_change_pct']:.0f}% of the move")


def run() -> dict:
    result = decompose(load_periods())
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    DECOMP_JSON.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print_check(result)
    print(f"[decompose] wrote {DECOMP_JSON}")
    return result


if __name__ == "__main__":
    run()
