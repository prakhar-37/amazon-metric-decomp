"""Build a paste-into-Claude.ai prompt from decomposition.json (no API calls).

Workflow:
  1. python narrate.py            -> prints the prompt
  2. paste it into Claude.ai, save the reply to data/narrative.txt
  3. python narrate.py            -> prints the saved narrative; render.py embeds it
"""
import json

from config import DECOMP_JSON, NARRATIVE_TXT
from fmt import fmt_usd_delta, fmt_value


def build_prompt(result: dict) -> str:
    root = result["root_label"]
    lines = [
        "You are a business analyst writing the metric commentary section of an Amazon-style "
        "Weekly Business Review (WBR).",
        "",
        f"Headline: {root} moved {result['pct_change']:+.1f}% "
        f"({fmt_value(result['root'], result['last'])} -> {fmt_value(result['root'], result['this'])}, "
        f"{fmt_usd_delta(result['delta'])}).",
        "",
        "Driver contributions (ranked by absolute impact on the headline):",
    ]
    for l in result["leaves"]:
        note = f" | context: {l['note']}" if l.get("note") else ""
        lines.append(
            f"- {l['label']}: {fmt_value(l['name'], l['last'])} -> {fmt_value(l['name'], l['this'])} "
            f"({l['pct_change']:+.1f}%), contributed {fmt_usd_delta(l['contribution'])} "
            f"= {l['share_of_change_pct']:.0f}% of the move{note}")
    for i in result["interactions"]:
        lines.append(f"- {i['label']} (cross term): {fmt_usd_delta(i['contribution'])}")
    rc = result["root_cause"]
    lines += [
        "",
        f"Identified root cause: {rc['label']} ({'dominant' if rc['dominant'] else 'largest, not dominant'}).",
        "Metric tree: GMS = Units x ASP; Units = Traffic x Conversion.",
        "",
        "Write the narrative in WBR style, max 180 words, plain text, no markdown headers:",
        "1. A one-sentence headline with the number.",
        "2. 'What drove it' - the root cause first, then secondary drivers, with figures.",
        "3. 'So what' - the customer/business implication.",
        "4. 'Next steps' - 2-3 concrete actions with an owner type (e.g. Mobile PM).",
        "Use only the numbers above; do not invent causes beyond the context provided.",
    ]
    return "\n".join(lines)


def load_narrative() -> str | None:
    if NARRATIVE_TXT.exists():
        text = NARRATIVE_TXT.read_text(encoding="utf-8").strip()
        return text or None
    return None


def run() -> None:
    result = json.loads(DECOMP_JSON.read_text(encoding="utf-8"))
    print("=" * 70)
    print("PASTE THIS INTO CLAUDE.AI:")
    print("=" * 70)
    print(build_prompt(result))
    print("=" * 70)
    narrative = load_narrative()
    if narrative:
        print(f"NARRATIVE FOUND in {NARRATIVE_TXT}:\n")
        print(narrative)
    else:
        print(f"No narrative yet. Save Claude's reply to {NARRATIVE_TXT}, then re-run render/main.")


if __name__ == "__main__":
    run()
