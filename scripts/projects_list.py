#!/usr/bin/env python3
"""Print the home-page Projects panel from content/projects/*.md.

Called at build time from content/index.md via the `shell` shortcode.
Each project file's front matter provides:
  title, summary, date   card text and order (newest first)
  order                  optional number: lower comes first, before projects without it
  app                    where "Open" points (external URL or a local /apps/... page)
  repo                   optional source link
  stack                  optional, comma-separated tech list
  status                 optional URL checked at build time → "live"/"down" badge
  draft: true            hide from the panel
The card title links to the project page Nicolino renders: /projects/<file>.html
"""

import concurrent.futures
import glob
import html
import os
import urllib.request

from posts_list import front_matter, parse_date  # same folder

PROJECTS = "content/projects"


def check(url):
    """True if the URL answers 2xx/3xx within a few seconds, False otherwise."""
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "marso.ar-site-build"})
        with urllib.request.urlopen(req, timeout=8) as r:
            return 200 <= r.status < 400
    except Exception:
        return False


def main():
    projects = []
    for path in glob.glob(os.path.join(PROJECTS, "*.md")):
        meta = front_matter(path)
        if meta.get("draft", "").lower() in ("true", "yes", "1"):
            continue
        meta["slug"] = os.path.splitext(os.path.basename(path))[0]
        meta["_date"] = parse_date(meta.get("date", "")) or parse_date("1970-01-01")
        projects.append(meta)
    if not projects:
        print('<p class="projects-empty">No projects yet.</p>')
        return
    projects.sort(key=lambda p: (p["_date"], p["slug"]), reverse=True)
    projects.sort(key=lambda p: float(p.get("order") or "inf"))  # stable: date order within ties

    with concurrent.futures.ThreadPoolExecutor() as pool:
        status = dict(zip(
            (p["slug"] for p in projects),
            pool.map(lambda p: check(p["status"]) if p.get("status") else None, projects),
        ))

    cards = []
    for p in projects:
        e = lambda k: html.escape(p.get(k, ""))
        page = f'/projects/{html.escape(p["slug"])}.html'
        badge = ""
        if status[p["slug"]] is not None:
            ok = status[p["slug"]]
            # Text + dot: state is never conveyed by color alone
            badge = f'<span class="proj-status {"is-up" if ok else "is-down"}">● {"live" if ok else "down"}</span>'
        stack = "".join(f"<li>{html.escape(s.strip())}</li>" for s in p.get("stack", "").split(",") if s.strip())
        external = p.get("app", "").startswith("http")
        links = []
        if p.get("app"):
            links.append(f'<a href="{e("app")}" role="button" class="proj-open">Open{" ↗" if external else ""}</a>')
        links.append(f'<a href="{page}">Details</a>')
        if p.get("repo"):
            links.append(f'<a href="{e("repo")}">Code</a>')
        cards.append(
            f'<li class="proj-card"><div class="proj-head"><a class="proj-title" href="{page}">{e("title")}</a>{badge}</div>'
            f'<p class="proj-summary">{e("summary")}</p>'
            + (f'<ul class="proj-stack">{stack}</ul>' if stack else "")
            + f'<div class="proj-links">{"".join(links)}</div></li>'
        )
    # Single line: blank lines would make the Markdown parser split the HTML
    print(f'<ul class="projects-list">{"".join(cards)}</ul>')


if __name__ == "__main__":
    main()
