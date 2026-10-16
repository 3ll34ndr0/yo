---
title: Lectura
date: 2026-10-15
order: 3
summary: Press a button, speak Spanish, read what you said. A speech-to-text page built in one afternoon on top of an existing pipeline.
app: https://lectura.marso.ar
repo: https://github.com/3ll34ndr0/lectura
status: https://lectura.marso.ar/healthz
stack: FastAPI, Orchardrun, Docker, k3s, Argo CD, Cloudflare
---

Lectura is a one-button page in Spanish: tap **Hablar**, speak, tap **Detener**, and
the text you said appears on screen. The next tap clears it and starts again. That's
the whole app.

**[Open the app ↗](https://lectura.marso.ar)** · [Source code](https://github.com/3ll34ndr0/lectura)

## How easy it was

Lectura went from idea to live in one afternoon, from the first commit to the
first real transcription on [lectura.marso.ar](https://lectura.marso.ar). Almost none of that time
went into infrastructure, because the infrastructure already existed:

- **The app was a copy, not a rewrite.** The [Thai practice app](thai.html) already
  recorded audio in the browser and sent it to a speech-to-text API. Lectura keeps that
  shape and drops the rest: no exercises, no scoring, just audio in and Spanish text out
  (`language=es` on the [Orchardrun](https://orchardrun.com) transcription API).
- **The delivery pipeline was a copy too.** The same GitHub Actions workflow runs the
  tests, builds the image to GHCR and commits the new tag to the Kubernetes manifests.
  The only new piece was one Argo CD Application pointing at the new repo. From then on,
  every push to `main` deploys itself.
- **The domain was one line.** DNS for marso.ar is code (DNSControl), so `lectura.marso.ar`
  was a single `A` record in one commit. Cloudflare proxies it and provides HTTPS.
- **The manual steps were a handful of one-time clicks and commands:** create the GitHub
  repo, make the container image public, apply the Argo CD Application, and create the
  Kubernetes Secret with the Orchardrun API key by hand on the cluster, so it never touches git.

I built it with [Claude Code](https://claude.com/claude-code) as a pair: I described
what I wanted (the button, the Spanish wording, the clear-and-record-again behaviour)
and reviewed each step, and the reusable pieces above did the rest.

## What's inside

- **Frontend:** one static page with plain JavaScript. `MediaRecorder` records in the
  browser's own format (WebM/Opus in Chrome and Firefox, MP4 in Safari) and stops on its
  own after 60 seconds.
- **Backend:** FastAPI with one endpoint, `POST /api/transcribir`, which forwards the
  audio and returns `{"texto": "..."}`. Recordings and transcripts are never stored or logged.
- **Limits:** every request is a paid API call, so uploads are capped at 2 MB, each
  visitor gets 6 a minute and 60 a day, and the whole app 500 a day.
- **Hardening:** a non-root container with a read-only filesystem, health probes, and
  tests that fake the speech-to-text API so CI needs no key.
