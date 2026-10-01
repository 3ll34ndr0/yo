#!/usr/bin/env python3
"""Render a GitHub user's contribution calendar (the profile heatmap) as inline SVG.

Called at build time from content/index.md via the `shell` shortcode. Prints HTML to stdout.
Never fails the build: on any error it prints a plain link to the profile instead.

Data source: https://github.com/users/<user>/contributions, the HTML fragment the
GitHub profile page itself loads. It's public and needs no token, but it's
undocumented. If it breaks, switch to the GraphQL API
(user.contributionsCollection.contributionCalendar, needs a token).

Usage: contributions.py <github-user>
"""

import datetime as dt
import html
import re
import sys
import urllib.request

CELL = 10  # square size
GAP = 3  # space between squares
LEFT = 28  # room for weekday labels
TOP = 16  # room for month labels

TD_RE = re.compile(r"<td\b[^>]*\bdata-date=\"(?P<date>[\d-]+)\"[^>]*>", re.S)
ATTR_RE = re.compile(r'\b(id|data-level)="([^"]*)"')
TIP_RE = re.compile(r'<tool-tip\b[^>]*\bfor="(?P<for>[^"]+)"[^>]*>(?P<text>[^<]*)</tool-tip>', re.S)
TOTAL_RE = re.compile(r"([\d,]+)\s+contributions?\s+in\s+the\s+last\s+year", re.S)
COUNT_RE = re.compile(r"^(\d+)\s+contribution")


def fetch(user):
    req = urllib.request.Request(
        f"https://github.com/users/{user}/contributions",
        headers={"User-Agent": "marso.ar-site-build"},
    )
    with urllib.request.urlopen(req, timeout=15) as r:
        return r.read().decode("utf-8")


def parse(page):
    tips = {m["for"]: " ".join(m["text"].split()) for m in TIP_RE.finditer(page)}
    days = []
    for m in TD_RE.finditer(page):
        attrs = dict(ATTR_RE.findall(m.group(0)))
        tip = tips.get(attrs.get("id"), "")
        count = COUNT_RE.match(tip)
        days.append({
            "date": dt.date.fromisoformat(m["date"]),
            "level": int(attrs.get("data-level", 0)),
            "tip": tip or m["date"],
            "count": int(count.group(1)) if count else 0,
        })
    days.sort(key=lambda d: d["date"])
    total = TOTAL_RE.search(page)
    total = int(total.group(1).replace(",", "")) if total else sum(d["count"] for d in days)
    return days, total


def render(user, days, total):
    # GitHub weeks start on Sunday: column = week, row = weekday (Sun=0)
    first = days[0]["date"]
    start = first - dt.timedelta(days=(first.weekday() + 1) % 7)
    weeks = (days[-1]["date"] - start).days // 7 + 1
    step = CELL + GAP
    width = LEFT + weeks * step
    height = TOP + 7 * step

    parts = [
        f'<svg class="gh-heatmap" viewBox="0 0 {width} {height}" role="img" '
        f'aria-label="{total} contributions in the last year">'
    ]
    for row, name in ((1, "Mon"), (3, "Wed"), (5, "Fri")):
        parts.append(f'<text x="0" y="{TOP + row * step + CELL - 1}">{name}</text>')

    last_month, labels = None, []  # (col, x, text)
    for d in days:
        col = (d["date"] - start).days // 7
        row = (d["date"].weekday() + 1) % 7
        x, y = LEFT + col * step, TOP + row * step
        if row == 0 or d is days[0]:
            if d["date"].month != last_month:
                labels.append((col, x, f'{d["date"]:%b}'))
            last_month = d["date"].month
        parts.append(
            f'<rect x="{x}" y="{y}" width="{CELL}" height="{CELL}" rx="2" class="l{d["level"]}">'
            f'<title>{html.escape(d["tip"])}</title></rect>'
        )
    # Like GitHub: drop a month label that would collide with the next one
    for i, (col, x, text) in enumerate(labels):
        nxt = labels[i + 1][0] if i + 1 < len(labels) else weeks
        if nxt - col >= 3:
            parts.append(f'<text x="{x}" y="{TOP - 5}">{text}</text>')
    parts.append("</svg>")

    legend = "".join(f'<i class="l{n}"></i>' for n in range(5))
    profile = f"https://github.com/{html.escape(user)}"
    # Single line: blank lines would make the Markdown parser split the HTML
    return (
        f'<figure class="gh-contrib"><div class="gh-scroll">{"".join(parts)}</div>'
        f'<figcaption><span>{total:,} contributions in the last year · '
        f'<a href="{profile}">@{html.escape(user)}</a></span>'
        f'<span class="gh-legend">Less {legend} More</span></figcaption></figure>'
    )


def main():
    user = sys.argv[1] if len(sys.argv) > 1 else "3ll34ndr0"
    try:
        days, total = parse(fetch(user))
        if not days:
            raise ValueError("no days found in calendar (format changed?)")
        print(render(user, days, total))
    except Exception as e:  # never break the site build over a widget
        print(f"contributions.py: {e}", file=sys.stderr)
        print(f'<p><a href="https://github.com/{html.escape(user)}">GitHub activity of @{html.escape(user)}</a></p>')


if __name__ == "__main__":
    main()
