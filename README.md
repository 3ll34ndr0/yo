# marso.ar — personal site

Personal page built with [Nicolino](https://nicolino.ralsina.me/), hosted on
GitHub Pages at **https://marso.ar**. DNS lives in Cloudflare and is managed as
code. GitHub Actions builds and deploys the site and applies DNS changes.

- Repo: https://github.com/3ll34ndr0/yo
- Live: https://marso.ar (`www.marso.ar` redirects to the apex)

---

## 1. Status (2026-10-01)

| Item | State |
|------|-------|
| Nicolino site scaffolded (placeholder home / about / one post) | ✅ |
| `site` workflow: build + deploy to GitHub Pages | ✅ running |
| `dns` workflow: DNSControl preview + push to Cloudflare | ✅ running (first run failed on a wrong image tag, fixed in `f071ca8`) |
| Apex `marso.ar` → GitHub Pages (A/AAAA) | ✅ live, served by GitHub over HTTPS |
| `www.marso.ar` → CNAME `3ll34ndr0.github.io` | ✅ in DNS; ⏳ GitHub's check was failing on cached NXDOMAIN (30 min negative TTL), re-check |
| Pages custom domain `marso.ar` set in repo settings | ✅ |
| **Enforce HTTPS** ticked | ⏳ after the `www` check passes |
| GitHub **verified domain** (TXT `_github-pages-challenge-3ll34ndr0`) | ⏳ TODO: get value from account Settings → Pages |
| Home page: GitHub heatmap panel + contact/CV/links panel | ✅ built, contact data filled in; ⏳ add `assets/cv.pdf` |
| Home page: Claude Code usage panel (under the heatmap) | ✅ built; refreshed daily by a systemd user timer (`make usage-timer`) |
| Home page: Posts panel (under Contact) | ✅ latest 5 posts + link to `/posts/` |
| Home page: Projects panel (main column, under Claude Code usage) | ✅ step 1 of the apps plan (§9): cards link to the live apps |
| Real content, theme, language | ⏳ TODO (see §8) |

## 2. Decisions made

| Topic | Decision | Why |
|-------|----------|-----|
| Generator | **Nicolino**, pinned in `.nicolino-version` (currently `v0.27.0`) | Markdown, fast, and upstream ships a static Linux binary, so CI needs no compile step. Pinned because upstream warns that the config format may change |
| Nicolino features | Default set **minus `pandoc`** | `pandoc` is on by default and the build **aborts** without it. Markdown doesn't need it |
| Hosting | **GitHub Pages**, source = **GitHub Actions** (no `gh-pages` branch) | Free, nothing to maintain, no build output committed |
| Repo | **`3ll34ndr0/yo`**, public | Pages on a private repo needs a paid plan. With a custom domain the repo name doesn't matter |
| Domain | Apex **`marso.ar`** is canonical; `www` → CNAME → redirects to apex | |
| DNS as code | **DNSControl**, run from its Docker image `ghcr.io/dnscontrol/dnscontrol:5.2.0` | Single JS file, `preview` before `push`, **no state file** (unlike Terraform/OpenTofu) |
| Cloudflare proxy for Pages records | **DNS-only (grey cloud)** | GitHub has to see its own IPs to issue and renew the Let's Encrypt cert. GitHub already serves through a CDN |
| Existing records | **Imported** (2026-10-01) and kept as-is in `dns/dnsconfig.js` | DNSControl deletes anything not declared. The zone had 7 A + 2 SRV on subdomains, no apex, no MX |
| DNS approval gate | `push` job runs in environment **`dns-prod`** | Add a required reviewer there so DNS changes need a click |
| Home page | Two panels (Pico CSS grid, stacked on mobile): **GitHub contribution heatmap** and **contact / CV download / GitHub + LinkedIn links** | |
| Heatmap source | `scripts/contributions.py` fetches `github.com/users/3ll34ndr0/contributions` (the same fragment the profile page loads) and renders inline SVG, **at build time**, via Nicolino's `shell` shortcode | No token, no client-side JS, no third-party image service, and it follows the site's light/dark toggle. The endpoint is undocumented; the fallback is the GraphQL `contributionCalendar` API. If the fetch fails, the page shows a plain link and the build still passes |
| Claude Code usage panel | **Option A: local logs.** `scripts/claude_usage.py export` reads `~/.claude/projects/**/*.jsonl` on the notebook and writes **daily totals per model** to `data/claude-usage.json` (committed). `render` draws the panel at build time from that file | CI can't reach the notebook or the company HOMER server. Local logs have exact token counts. The JSON holds only dates, model names and numbers: no prompts, projects or session ids |
| Usage panel content | Last **90 days**: tokens (input + output + cache writes), cache reads, active days, one bar per day, model mix by tokens. **No dollar figures** (`render --no-cost`) | The API-list-price estimate (~$800) read like a bill, but usage is covered by the flat Claude Pro subscription. `render` without `--no-cost` brings it back; prices are in `PRICES` |
| Heatmap freshness | `site` workflow also runs **daily** (cron `17 6 * * *` UTC) | The heatmap is baked into static HTML |
| Secrets | `CLOUDFLARE_API_TOKEN` as a **repository** secret (both DNS jobs use it). Locally it's in `.env`, which is **git-ignored** | Token scope: `Zone → DNS → Edit` on `marso.ar` only |

## 3. How it works

```
 push to main                       ┌──────────────────────────────┐     ┌──────────────┐
 touching site paths  ───────────▶  │ site.yml                     │ ──▶ │ GitHub Pages │
 (content/, conf.yml, themes/ …)    │  install pinned nicolino     │     │  marso.ar    │
                                    │  nicolino build → output/    │     └──────▲───────┘
                                    └──────────────────────────────┘            │
 push to main / PR                  ┌──────────────────────────────┐     ┌──────┴───────┐
 touching dns/  ──────────────────▶ │ dns.yml                      │ ──▶ │ Cloudflare   │
                                    │  preview: check + preview    │ API │ zone marso.ar│
                                    │  push (main only, dns-prod)  │     └──────────────┘
                                    └──────────────────────────────┘
```

### When does CI run?

| You change… | `site` | `dns` |
|-------------|:------:|:-----:|
| `content/**`, `assets/**`, `themes/**`, `shortcodes/**`, `templates/**`, `user_templates/**`, `conf.yml`, `conf.*.yml`, `scripts/**`, `.nicolino-version`, `site.yml` | ✅ build (+ deploy on `main`) | — |
| `data/**` (e.g. after `make usage`) | ✅ build + deploy | — |
| *(nothing, daily at 06:17 UTC)* | ✅ build + deploy (refreshes heatmap) | — |
| `dns/**`, `dns.yml` | — | ✅ preview (+ push on `main`) |
| Anything else: `README.md`, `.gitignore`, … | — | — |

Details:
- `site` uses an **allow-list** (`paths:`), so new non-site files never trigger a deploy.
  If you add a new folder Nicolino reads, add it to the list in `site.yml`.
- On **pull requests** both workflows run, but only to build or preview. Nothing is deployed or pushed.
- **Mixed commits** (e.g. content + DNS) trigger both workflows.
- GitHub **disables scheduled workflows after 60 days without repo activity** (public repos).
  If the heatmap stops updating, re-enable `site` in the Actions tab, or just push something.
- Both workflows can be started by hand from the Actions tab (`workflow_dispatch`).
- Put `[skip ci]` in a commit message to skip all workflows for that push.
- Edge case: if a push's diff has more than 300 files, GitHub can't evaluate path filters
  and runs the workflow anyway.

## 4. Repository layout

```
.
├── conf.yml                ← Nicolino config (title, url, features…)
├── .nicolino-version       ← pinned Nicolino version used by CI and locally
├── scripts/
│   ├── contributions.py    ← GitHub heatmap → inline SVG (run at build time)
│   ├── claude_usage.py     ← export: ~/.claude logs → data/ (local) · render: panel (build time)
│   ├── push_usage.sh       ← daily export + commit + push, run by the systemd timer
│   ├── posts_list.py       ← latest posts for the home page (build time)
│   └── projects_list.py    ← Projects panel cards + live/down check (build time)
├── data/
│   └── claude-usage.json   ← daily Claude Code usage per model (committed)
├── systemd/                ← yo-usage.{service,timer}: daily usage push (make usage-timer)
├── Makefile                ← make usage | usage-timer | preview | build | clean (local helpers)
├── content/
│   ├── index.md            ← home page → / (heatmap + contact panels)
│   ├── about.md            ← → /about.html
│   ├── posts/              ← blog posts → /posts/…
│   ├── projects/           ← one .md per project → /projects/<name>.html + home card
│   └── galleries/          ← photo galleries
├── assets/                 ← copied as-is to the site root (css/custom.css, cv.pdf…)
├── shortcodes/, themes/    ← generated by `nicolino init`; customise freely
├── dns/
│   ├── dnsconfig.js        ← DNS for marso.ar: SOURCE OF TRUTH
│   └── creds.json          ← points to $CLOUDFLARE_API_TOKEN, no secrets
├── .github/workflows/
│   ├── site.yml
│   └── dns.yml
└── .env                    ← local only, git-ignored (CLOUDFLARE_API_TOKEN)
```

## 5. Everyday use

### Write / preview locally

```bash
# install the same binary CI uses
curl -fsSL -o ~/.local/bin/nicolino \
  "https://github.com/ralsina/nicolino/releases/download/$(cat .nicolino-version)/nicolino-static-linux-amd64"
chmod +x ~/.local/bin/nicolino

make preview                              # clean + live rebuild at http://localhost:8080
nicolino new content/posts/my-post.md
git commit -am "new post" && git push      # CI builds and deploys
```

### Home page

- **Panel layout** is the order of the blocks in `content/index.md`:
  `<div class="home-main">` is the left (wide) column, `<div class="home-side">` the right one.
  Each `<article class="panel …">` is a panel; move the whole block to reorder or switch
  column. On phones the left column comes first, then the right. Then run `make clean`, since the panels are cached.
- Contact data and profile links: edit `content/index.md` (plain HTML inside Markdown).
- CV: put the PDF at **`assets/cv.pdf`** → served at `/cv.pdf`. Replace the file to update it.
- Heatmap: called from `content/index.md` as
  `{{< shell "python3 scripts/contributions.py 3ll34ndr0" >}}`. Styles/colors are in
  `assets/css/custom.css` (`.gh-*`, `--gh-l0…4`).
- ⚠️ Locally, Nicolino's incremental build **won't re-run the heatmap** unless
  `content/index.md` changes. Run `make clean && nicolino build` (or `make preview`) to refresh it.
  CI always builds from scratch.

### Write a post

```bash
nicolino new content/posts/my-post.md     # or create the file by hand
```

Front matter: `title`, `date` (add a time, e.g. `2026-10-02 18:30`, to order
same-day posts), `tags`, and optionally `draft: true` to keep it off the home-page
list. The **Posts** panel (`scripts/posts_list.py`) shows the latest 5 posts, newest first,
linking to `/posts/<file-name>.html`, plus "All posts (N) →" → `/posts/`.
Pushing a new post rebuilds the site. Locally, run `make preview` (clean build) to see it in the panel.

### Add a project

Create `content/projects/<name>.md`:

```yaml
---
title: Thai read-aloud practice
date: 2026-09-22                     # card order, newest first (after `order`)
order: 2                             # optional: lower comes first; cards with it go before those without
summary: One line for the home-page card.
app: https://t.marso.ar              # "Open" button (external URL or /apps/<name>/)
repo: https://github.com/3ll34ndr0/thai-practice   # optional "Code" link
status: https://t.marso.ar/api/exercise           # optional: checked at build → live/down badge
stack: FastAPI, PyThaiNLP, Docker, k3s, Argo CD   # optional tags
---
Longer write-up (rendered as the project page).
```

The badge reflects the status at the last build (on push, plus the daily rebuild).
`draft: true` hides a project from the panel.

### Claude Code usage panel

```bash
make usage        # = python3 scripts/claude_usage.py export && git add data/claude-usage.json
git commit -m "data: refresh Claude usage" && git push
```

- Only this notebook's sessions are counted (other machines have their own `~/.claude`).
- Log lines are de-duplicated per API response (each response is logged once per content block).
- Cost = input/output/cache read/cache write (5m vs 1h) × the model's list price; Opus fast mode ×2.
  New models print as "unpriced" on export: add them to `PRICES`.
- Bar colors were validated for contrast and chroma against both theme surfaces
  (`--cu-bar` in `custom.css`).
- **Automated daily** by a systemd user timer (`make usage-timer` installs it; idempotent, re-run after
  editing `scripts/push_usage.sh` or `systemd/`):
  - 21:00 local (`Persistent=true`: runs at the next boot/resume if missed; retries every 10 min on failure).
  - Runs `~/.local/bin/yo-push-usage` (a copy of `scripts/push_usage.sh`) in its **own clone**
    `~/.local/share/yo-usage`, hard-reset to `origin/main` each run, so it never touches this working copy.
  - Commits `data: refresh Claude usage` only if the numbers changed (ignores `generated_at`); the push
    touches `data/**`, so `site` rebuilds. Daily commits also keep the scheduled workflow from being
    auto-disabled after 60 days.
  - Pushes with a repo-only **deploy key** `~/.ssh/yo_usage_deploy` (no passphrase, write access,
    GitHub → repo Settings → Deploy keys), set as `core.sshCommand` in the clone.
  - Check: `systemctl --user list-timers yo-usage` · logs: `journalctl --user -u yo-usage` ·
    run now: `systemctl --user start yo-usage`.

### Change DNS

1. Edit `dns/dnsconfig.js`.
2. Optional local dry run:
   ```bash
   source .env
   docker run --rm --user "$(id -u):$(id -g)" -e CLOUDFLARE_API_TOKEN \
     -v "$PWD/dns:/dns" ghcr.io/dnscontrol/dnscontrol:5.2.0 preview
   ```
3. Push (ideally via a PR, which shows the preview), then approve the `dns-prod` job if it's gated.

⚠️ Records **not** in `dnsconfig.js` are **deleted** on push. If you create something in
the Cloudflare dashboard, add it to the file too, or the next push removes it.
To re-import the live zone:
```bash
docker run --rm --user "$(id -u):$(id -g)" -e CLOUDFLARE_API_TOKEN -v "$PWD/dns:/dns" \
  ghcr.io/dnscontrol/dnscontrol:5.2.0 get-zones --format=js --out=imported.js cloudflare marso.ar
```
DNSControl v5 syntax is `get-zones <credkey> <zone>`; v4 also took a provider argument.
`dns/imported.js` is git-ignored.

### Upgrade tools

- **Nicolino:** change `.nicolino-version`, build locally to check, push.
- **DNSControl:** change the image tag in `dns.yml`. Tags have **no `v` prefix** (`5.2.0`, not `v5.2.0`).

## 6. One-time setup (done ✅ / pending ⏳)

1. ✅ Repo `3ll34ndr0/yo` created (public, empty)
2. ✅ Settings → Pages → Source: **GitHub Actions**
3. ✅ Secret `CLOUDFLARE_API_TOKEN` (repository level)
4. ✅ Initial push, DNS records applied
5. ✅ Settings → Pages → Custom domain: `marso.ar`
6. ⏳ `www.marso.ar` check passing → tick **Enforce HTTPS**
7. ⏳ Account Settings → Pages → **Add a verified domain** `marso.ar` → put the TXT value in
   `dnsconfig.js` (line is there, commented) → push → approve → click **Verify**
8. ⏳ (optional) Environment `dns-prod` with yourself as required reviewer

## 7. Troubleshooting log

| Symptom | Cause | Fix |
|---------|-------|-----|
| `get-zones`: `creds.json entry missing TYPE field` | No `creds.json` in the mounted dir, token not passed with `-e`, v4 syntax used on v5 | Created `dns/creds.json`, use `-e CLOUDFLARE_API_TOKEN`, `get-zones cloudflare marso.ar` |
| `nicolino build`: "pandoc feature enabled but pandoc is not installed" | Default config | Removed `pandoc` from `features:` |
| `dns` job exit code **125** | Image tag `v5.2.0` doesn't exist | Use `5.2.0` |
| GitHub: "DNS check unsuccessful … NotServedByPagesError" | DNS job had failed, so no records existed | Fixed the job, records pushed |
| GitHub: "www.marso.ar is improperly configured" while `dig` shows the CNAME | Resolvers cached the earlier NXDOMAIN (Cloudflare SOA negative TTL = 1800 s) | Wait ~30 min, then "Check again" in Pages settings |
| Heatmap stale / old layout locally after editing `scripts/contributions.py` | Incremental build cached the page; `nicolino clean` alone keeps the cache (`.kvstore`, `.croupier`) | `make clean && nicolino build` (or `make preview`) |
| Deleted post still listed in the home Posts panel | Same cache, holding the old shortcode output | `make clean` |
| `dns/imported.js` owned by root | Docker writes as root | Add `--user "$(id -u):$(id -g)"` |

## 8. Still open 🔧

- [ ] Add the CV at `assets/cv.pdf` (the download button 404s until then)
- [ ] Show private-repo activity in the heatmap? Enable *Include private contributions on my profile*
      in GitHub profile settings. Counts only, no repo names
- [x] Per-repo activity? → No: the profile-wide heatmap (all contributions) is preferred
- [x] Merge GitLab activity into the heatmap? → No, GitLab is almost abandoned; no GitLab link on the site either
- [x] Usage panel dollar estimate → hidden (tokens only)
- [x] Usage panel: automate `make usage`? → systemd user timer, 21:00 (`make usage-timer`)
- [ ] Site shape beyond the home page: blog? Galleries? Books (docs)?
- [ ] Theme: default with a [base16 color scheme](https://sixteen.ralsina.me/) (`color_scheme:` in `conf.yml`), or custom?
- [ ] Language: `es`, `en` or both (`conf.es.yml` per-language overrides)? Currently `en`.
- [ ] Later Cloudflare proxy (orange) for analytics/WAF? It would need SSL **Full (strict)** and
      may interfere with cert renewals. Not planned for now.
- [ ] Nice-to-haves: link checker on PRs, Dependabot for actions (`actions/checkout@v4` already
      warns about Node 20 deprecation), a scheduled check for new Nicolino releases,
      pin actions by SHA, verify the Nicolino binary's sha256.

## 9. Plan: self-hosted apps (t.marso.ar and future ones)

Goal: **all frontends in Nicolino** (one look, static, deployed in ~30 s from
this repo). Apps that need a server keep **only an API** on the k3s cluster
(GitOps with Argo CD, as today).

```
marso.ar (GitHub Pages, this repo)               k3s on the VPS (Argo CD)
├─ /                  home + Projects panel
├─ /projects/thai.html    project page
└─ /apps/thai/        app UI  ── fetch ──▶  t.marso.ar/api/*  (FastAPI, CORS: https://marso.ar)
                                             <next-app>.marso.ar/api/*
```

| Step | What | Where | State |
|------|------|-------|-------|
| 1 | Projects panel + `content/projects/thai.md` linking to `https://t.marso.ar` | this repo | ✅ |
| 2 | Port the UI to `/apps/thai/` (page in `content/apps/`, JS in `assets/js/`). API calls go to `https://t.marso.ar/api/...` instead of relative `/api/...`. Add CORS `allow_origins=["https://marso.ar"]` to the FastAPI app. Switch `app:` to `/apps/thai/` | both repos | ⏳ |
| 3 | Make the backend API-only: drop the `StaticFiles` mount and `frontend/` from the image; redirect `t.marso.ar/` → `marso.ar/apps/thai/` | thai-practice | ⏳ |

Rules for the next apps:
- **Static-only app** → lives entirely in this repo under `/apps/<name>/`, no k3s.
- **App with a server** → UI here, API repo with Dockerfile + `k8s/` + Argo CD Application;
  CORS for `https://marso.ar`; DNS record added in `dns/dnsconfig.js` (same PR/preview/approve flow).
- Frontend and backend deploy separately: keep API changes backward-compatible, or deploy the API first.
- The browser mic (`getUserMedia`) needs HTTPS: Pages provides it.

## References

- Nicolino user guide: https://nicolino.ralsina.me/books/user-guide/
- Nicolino releases: https://github.com/ralsina/nicolino/releases
- GitHub Pages custom domains: https://docs.github.com/en/pages/configuring-a-custom-domain-for-your-github-pages-site
- Workflow path filters: https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax#onpushpull_requestpull_request_targetpathspaths-ignore
- DNSControl + Cloudflare: https://docs.dnscontrol.org/provider/cloudflareapi
