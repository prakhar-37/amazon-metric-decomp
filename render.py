"""Render output/index.html from decomposition.json, waterfall.png, narrative."""
import base64
import json

from jinja2 import Environment, FileSystemLoader, select_autoescape

import config
from fmt import fmt_pct, fmt_usd_delta, fmt_value
from narrate import load_narrative


def _fallback_narrative(r: dict) -> str:
    rc = r["root_cause"]
    return (f"{r['root_label']} moved {r['pct_change']:+.1f}% ({fmt_usd_delta(r['delta'])}). "
            f"The largest driver was {rc['label']} ({rc['pct_change']:+.1f}%), explaining "
            f"{rc['share_of_change_pct']:.0f}% of the change.")


def build_context(r: dict) -> dict:
    img = config.WATERFALL_PNG
    img_b64 = base64.b64encode(img.read_bytes()).decode() if img.exists() else ""
    narrative = load_narrative()
    return {
        "r": r, "teal": config.TEAL, "teal_dark": config.TEAL_DARK, "teal_light": config.TEAL_LIGHT,
        "negative": config.NEGATIVE, "root_cause_color": config.ROOT_CAUSE,
        "waterfall_b64": img_b64,
        "narrative_paras": [p.strip() for p in (narrative or _fallback_narrative(r)).split("\n\n") if p.strip()],
        "narrative_is_fallback": narrative is None,
        "last_label": config.PERIOD_LAST_LABEL, "this_label": config.PERIOD_THIS_LABEL,
    }


def run(result: dict | None = None) -> None:
    if result is None:
        result = json.loads(config.DECOMP_JSON.read_text(encoding="utf-8"))
    env = Environment(loader=FileSystemLoader(config.TEMPLATE_DIR),
                      autoescape=select_autoescape(["html", "j2"]))
    env.filters["val"] = fmt_value
    env.filters["usd_delta"] = fmt_usd_delta
    env.filters["pct"] = fmt_pct
    html = env.get_template("index.html.j2").render(**build_context(result))
    config.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    config.REPORT_HTML.write_text(html, encoding="utf-8")
    print(f"[render] wrote {config.REPORT_HTML}")


if __name__ == "__main__":
    run()
