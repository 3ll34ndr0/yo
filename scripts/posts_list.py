#!/usr/bin/env python3
"""Print an HTML list of the latest posts for the home page.

Called at build time from content/index.md via the `shell` shortcode.
Reads the front matter of content/posts/*.md (title, date, draft) and links
each post to /posts/<file name>.html, the URL Nicolino gives it.

Usage: posts_list.py [--limit N]
"""

import argparse
import datetime as dt
import glob
import html
import os
import re

POSTS = "content/posts"
FM_RE = re.compile(r"\A---\s*\n(.*?)\n---\s*\n", re.S)
DEFAULT_LANG = "en"  # conf.yml `language`
LANG_RE = re.compile(r"\.([a-z]{2})\.md$")  # foo.es.md → "es"; foo.md has none


def is_translation(path):
    """True for another language's version (foo.es.md); foo.md and foo.en.md are the default."""
    m = LANG_RE.search(path)
    return bool(m) and m.group(1) != DEFAULT_LANG


def slug(path):
    """foo.md / foo.en.md → "foo", the name Nicolino gives the default-language page."""
    return LANG_RE.sub("", os.path.basename(path)).removesuffix(".md")


def front_matter(path):
    with open(path, encoding="utf-8") as f:
        m = FM_RE.match(f.read())
    meta = {}
    for line in (m.group(1) if m else "").splitlines():
        if ":" in line and not line.startswith((" ", "\t", "#")):
            key, value = line.split(":", 1)
            meta[key.strip()] = value.strip().strip("\"'")
    return meta


def parse_date(value):
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d"):
        try:
            return dt.datetime.strptime(value[:19], fmt)
        except ValueError:
            pass
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=5)
    args = ap.parse_args()

    posts = []
    for path in glob.glob(os.path.join(POSTS, "*.md")):
        if is_translation(path):
            continue
        meta = front_matter(path)
        if meta.get("draft", "").lower() in ("true", "yes", "1"):
            continue
        date = parse_date(meta.get("date", ""))
        if not date:
            continue
        name = slug(path)
        posts.append((date, meta.get("title") or name, name))
    # Newest first. Same-day posts: give them a time ("date: 2026-10-01 18:30")
    # to control the order; otherwise the file name decides (deterministic in CI).
    posts.sort(key=lambda p: (p[0], p[2]), reverse=True)

    if not posts:
        print('<p class="posts-empty">No posts yet.</p>')
        return
    items = "".join(
        f'<li><a href="/posts/{html.escape(name)}.html">{html.escape(title)}</a>'
        f'<time datetime="{date:%Y-%m-%d}">{date:%b %d, %Y}</time></li>'
        for date, title, name in posts[: args.limit]
    )
    more = f'<p class="posts-more"><a href="/posts/">All posts ({len(posts)}) →</a></p>'
    # Single line: blank lines would make the Markdown parser split the HTML
    print(f'<ul class="posts-list">{items}</ul>{more}')


if __name__ == "__main__":
    main()
