#!/usr/bin/env python3
"""Claude Code token usage → daily aggregates → home-page panel.

Two subcommands:

  export   Run LOCALLY (needs ~/.claude). Reads Claude Code session logs
           (~/.claude/projects/**/*.jsonl), de-duplicates messages, and writes
           daily totals per model to data/claude-usage.json. Only dates, model
           names and numbers are written: no prompts, projects or session ids.

  render   Run at BUILD time (from content/index.md via the `shell` shortcode).
           Reads data/claude-usage.json and prints the panel HTML. Needs no
           network and no ~/.claude, so it works in CI.

Costs are ESTIMATES at public API list prices (PRICES below). On a subscription
plan they are an API-equivalent figure, not what you pay.
"""

import argparse
import datetime as dt
import glob
import html
import json
import os
import sys
from collections import defaultdict

DATA = "data/claude-usage.json"

# USD per million tokens. Source: Anthropic model pricing (checked 2026-10-01).
# Keys: input, output, cache read, cache write 5m, cache write 1h.
PRICES = {
    "claude-opus-5-5": dict(inp=4.00, out=20.00, cr=0.20, cw5=5.00, cw1h=8.00),
    "claude-sonnet-5-5": dict(inp=2.00, out=10.00, cr=0.20, cw5=2.50, cw1h=4.00),
    "claude-sonnet-5": dict(inp=2.00, out=10.00, cr=0.20, cw5=2.50, cw1h=4.00),
    "claude-haiku-4-5": dict(inp=1.00, out=5.00, cr=0.10, cw5=1.25, cw1h=2.00),
}
FAST_MULTIPLIER = 2.0  # usage.speed == "fast" (Opus fast mode)
FIELDS = ("input", "output", "cache_read", "cache_write")


def price_for(model):
    if model in PRICES:
        return PRICES[model]
    # Dated variants, e.g. claude-haiku-4-5-20251001
    for name, p in PRICES.items():
        if model.startswith(name + "-"):
            return p
    return None


# ---------------------------------------------------------------- export

def iter_messages(root):
    """Yield (timestamp, model, usage) once per API response.

    Claude Code writes one log line per content block, each repeating the
    response's usage, so lines are de-duplicated by (message id, request id),
    keeping the line with the most output tokens.
    """
    best = {}
    for path in glob.glob(os.path.join(root, "**", "*.jsonl"), recursive=True):
        with open(path, errors="replace") as f:
            for line in f:
                if '"usage"' not in line:
                    continue
                try:
                    d = json.loads(line)
                except ValueError:
                    continue
                m = d.get("message")
                if d.get("type") != "assistant" or not isinstance(m, dict) or not m.get("usage"):
                    continue
                model = m.get("model") or ""
                if model.startswith("<"):  # "<synthetic>": local, not an API call
                    continue
                key = (m.get("id"), d.get("requestId"))
                u = m["usage"]
                prev = best.get(key)
                if prev is None or (u.get("output_tokens") or 0) > (prev[2].get("output_tokens") or 0):
                    best[key] = (d.get("timestamp"), model, u)
    return best.values()


def export(args):
    root = os.path.expanduser(args.claude_dir)
    days = defaultdict(lambda: defaultdict(lambda: dict.fromkeys(FIELDS + ("cost",), 0)))
    unpriced = set()
    for ts, model, u in iter_messages(root):
        if not ts:
            continue
        # Local calendar day (the machine's timezone)
        day = dt.datetime.fromisoformat(ts.replace("Z", "+00:00")).astimezone().date().isoformat()
        cc = u.get("cache_creation") or {}
        w1h = cc.get("ephemeral_1h_input_tokens") or 0
        w_all = u.get("cache_creation_input_tokens") or 0
        w5 = cc.get("ephemeral_5m_input_tokens", w_all - w1h) or 0
        inp, out, cr = (u.get(k) or 0 for k in ("input_tokens", "output_tokens", "cache_read_input_tokens"))

        row = days[day][model]
        row["input"] += inp
        row["output"] += out
        row["cache_read"] += cr
        row["cache_write"] += w5 + w1h

        p = price_for(model)
        if p is None:
            unpriced.add(model)
            continue
        cost = (inp * p["inp"] + out * p["out"] + cr * p["cr"] + w5 * p["cw5"] + w1h * p["cw1h"]) / 1e6
        if u.get("speed") == "fast":
            cost *= FAST_MULTIPLIER
        row["cost"] += cost

    out = {
        "generated_at": dt.datetime.now().astimezone().isoformat(timespec="seconds"),
        "note": "Daily Claude Code usage per model. Cost = estimate at API list prices.",
        "unpriced_models": sorted(unpriced),
        "days": {
            day: {model: {k: round(v, 4) if k == "cost" else v for k, v in row.items()}
                  for model, row in sorted(models.items())}
            for day, models in sorted(days.items())
        },
    }
    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    with open(args.out, "w") as f:
        json.dump(out, f, indent=1, sort_keys=False)
        f.write("\n")
    total = sum(r["cost"] for m in out["days"].values() for r in m.values())
    print(f"wrote {args.out}: {len(out['days'])} days, est. ${total:,.2f} total"
          + (f", unpriced models: {', '.join(sorted(unpriced))}" if unpriced else ""),
          file=sys.stderr)


# ---------------------------------------------------------------- render

def human(n):
    for unit, size in (("B", 1e9), ("M", 1e6), ("k", 1e3)):
        if n >= size:
            return f"{n / size:.1f}{unit}".replace(".0", "")
    return str(int(n))


def render(args):
    try:
        with open(args.data) as f:
            data = json.load(f)
    except (OSError, ValueError) as e:
        print(f"claude_usage.py: {e}", file=sys.stderr)
        print('<p class="cu-empty">No usage data yet (run <code>make usage</code>).</p>')
        return

    today = dt.date.fromisoformat(data["generated_at"][:10])
    window = [today - dt.timedelta(days=i) for i in range(args.days - 1, -1, -1)]

    def day_totals(day):
        models = data["days"].get(day.isoformat(), {})
        t = dict.fromkeys(FIELDS + ("cost",), 0)
        for row in models.values():
            for k in t:
                t[k] += row.get(k, 0)
        return t

    series = [(d, day_totals(d)) for d in window]
    # Bar height = tokens the model actually processed fresh: input + output +
    # cache writes. Cache reads are shown separately; they dwarf everything else.
    fresh = [t["input"] + t["output"] + t["cache_write"] for _, t in series]
    tot = {k: sum(t[k] for _, t in series) for k in FIELDS + ("cost",)}
    active = sum(1 for v in fresh if v)

    # Model mix over the window (share of cost when shown, else of fresh tokens)
    mix = defaultdict(float)
    for d in window:
        for model, row in data["days"].get(d.isoformat(), {}).items():
            mix[model] += row.get("cost", 0) if args.cost else row["input"] + row["output"] + row["cache_write"]
    mix_total = sum(mix.values()) or 1

    # --- bar chart (inline SVG): single series, bars grow from one baseline,
    # rounded data-end / square base, 2px surface gap, full-height hover target.
    W, H, gap = 600, 120, 2
    bw = W / len(series)
    peak = max(fresh) or 1
    bars = []
    for i, ((d, t), v) in enumerate(zip(series, fresh)):
        x, w = i * bw, bw - gap
        h = max(v / peak * (H - 2), 2 if v else 0)
        tip = f"{d:%b %d}: {human(v)} tokens"
        if args.cost:
            tip += f" · ~${t['cost']:,.2f}"
        tip += f" · {human(t['cache_read'])} cache reads"
        r = min(2, w / 2, h)
        y = H - h
        bar = (f'<path d="M{x:.1f},{H}V{y + r:.1f}Q{x:.1f},{y:.1f} {x + r:.1f},{y:.1f}'
               f'H{x + w - r:.1f}Q{x + w:.1f},{y:.1f} {x + w:.1f},{y + r:.1f}V{H}Z"/>') if v else ""
        bars.append(
            f'<g><title>{html.escape(tip)}</title>'
            f'<rect class="cu-hit" x="{x:.1f}" y="0" width="{bw:.1f}" height="{H}"/>{bar}</g>'
        )
    first, last = window[0], window[-1]
    chart = (
        f'<svg class="cu-chart" viewBox="0 0 {W} {H}" role="img" '
        f'aria-label="Daily tokens, last {args.days} days">{"".join(bars)}'
        f'<line class="cu-base" x1="0" y1="{H}" x2="{W}" y2="{H}"/></svg>'
        f'<div class="cu-axis"><span>{first:%b %d}</span><span>peak {human(peak)}/day</span>'
        f'<span>{last:%b %d}</span></div>'
    )

    stats = [
        (human(tot["input"] + tot["output"] + tot["cache_write"]), "tokens"),
        (human(tot["cache_read"]), "cache reads"),
    ]
    if args.cost:
        stats.append((f"~${tot['cost']:,.0f}", "API-equivalent"))
    stats.append((str(active), f"active days of {args.days}"))
    tiles = "".join(f'<div class="cu-stat"><b>{v}</b><small>{l}</small></div>' for v, l in stats)

    pretty = lambda m: m.replace("claude-", "").replace("-", " ").title().replace(" 4 5", " 4.5").replace(" 5 5", " 5.5")
    legend = " · ".join(
        f"{html.escape(pretty(m))} {v / mix_total:.0%}" for m, v in sorted(mix.items(), key=lambda x: -x[1]) if v / mix_total >= 0.01
    )
    updated = data["generated_at"][:10]
    note = f"Last {args.days} days · updated {updated}"
    if args.cost:
        note += " · cost estimated at API list prices"

    # Single line: blank lines would make the Markdown parser split the HTML
    print(
        f'<div class="claude-usage"><div class="cu-stats">{tiles}</div>{chart}'
        f'<p class="cu-mix">{"By cost" if args.cost else "By tokens"}: {legend}</p>'
        f'<p class="cu-note">{note}</p></div>'
    )


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    e = sub.add_parser("export", help="read ~/.claude logs, write daily JSON")
    e.add_argument("--claude-dir", default="~/.claude/projects")
    e.add_argument("--out", default=DATA)
    e.set_defaults(func=export)
    r = sub.add_parser("render", help="print the panel HTML")
    r.add_argument("--data", default=DATA)
    r.add_argument("--days", type=int, default=90)
    r.add_argument("--no-cost", dest="cost", action="store_false", help="hide dollar figures")
    r.set_defaults(func=render)
    args = ap.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
