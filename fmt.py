"""Value formatting helpers shared by waterfall, render and narrate."""
from config import METRIC_TREE


def _compact(v: float) -> str:
    a = abs(v)
    if a >= 1e9:
        return f"{v / 1e9:.2f}B"
    if a >= 1e6:
        return f"{v / 1e6:.2f}M"
    if a >= 1e3:
        return f"{v / 1e3:.1f}K"
    return f"{v:,.0f}"


def fmt_value(metric: str, v: float) -> str:
    kind = METRIC_TREE[metric]["fmt"]
    if kind == "usd":
        return "$" + _compact(v)
    if kind == "usd2":
        return f"${v:,.2f}"
    if kind == "pct":
        return f"{v * 100:.2f}%"
    return _compact(v)


def fmt_usd_delta(v: float) -> str:
    """Signed $ amount, used for contributions expressed in root-metric units."""
    return ("+" if v >= 0 else "-") + "$" + _compact(abs(v))


def fmt_pct(v: float, digits: int = 1) -> str:
    return f"{v:+.{digits}f}%"
