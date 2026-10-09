---
title: Extractos
date: 2026-04-17
order: 1
summary: Search a phrase from a Redondos song and get the exact clip where it's sung. Also my end-to-end DevOps playground, with real users.
app: https://extractos.marso.ar
repo: https://github.com/3ll34ndr0/redo
status: https://extractos.marso.ar/healthz
stack: Flask, Kubernetes (k3s), Argo CD, Grafana, OpenTelemetry, Trivy, OpenTofu
---

Type a phrase from a song by Patricio Rey y sus Redonditos de Ricota and get an
audio clip of exactly the moment it's sung, ready to play, download or share.
The index covers 101 songs and about 14,600 sung words, each with its timing.

**[Open the app ↗](https://extractos.marso.ar)** · [Source code](https://github.com/3ll34ndr0/redo)

## Why I built it

Extractos is my **end-to-end DevOps project**: one real application taken all the way
from a commit to production on Kubernetes, with GitOps, observability and security
built in from the start rather than added later.

The goal is for it to **attract real users**. Real traffic brings real problems
(load, slow clips, abuse, bad timings, outages), and those are what I want to work
on: solving them with my experience, and using them as a testing ground for new tools.

## The DevOps flow

- **CI (GitHub Actions):** unit tests, then a smoke test of the built container
  (read-only, non-root) and browser tests with Playwright before anything ships.
- **Security:** every image is scanned with Trivy; findings go to GitHub code scanning,
  and any fixable high or critical vulnerability blocks the push and the deploy.
  Rate limits per visitor, no visitor IPs stored, HTTPS through Cloudflare.
- **GitOps delivery:** the image goes to GHCR, CI commits the new tag to the Kubernetes
  manifests, and Argo CD deploys it to a k3s cluster on a VPS.
- **Observability:** Prometheus metrics (searches, clips, latency, rate-limit hits),
  structured JSON logs and OpenTelemetry traces, collected by Grafana Alloy into
  Grafana Cloud. The dashboard is code too, applied by OpenTofu from CI.
- **Feedback loop:** visitors can report a clip that doesn't match and nudge its start
  and end; reports are tracked as metrics and feed back into the timings.

## How the clips are made

Each song's vocals are separated from the music with
[Demucs](https://github.com/facebookresearch/demucs), then the lyrics are force-aligned
to the vocal track (CTC alignment with torchaudio's MMS model). Choruses that the lyrics
leave out are detected and added back. On hand-labelled songs, 93% of line starts land
within 0.3 s. The app searches a SQLite index of those word timings and cuts clips on
demand with ffmpeg.
