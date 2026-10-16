---
title: Thai read-aloud practice
date: 2026-09-22
order: 2
summary: Read a Thai sentence aloud and get a pronunciation score from speech-to-text.
app: https://t.marso.ar
repo: https://github.com/3ll34ndr0/thai-practice
status: https://t.marso.ar/api/exercise
stack: FastAPI, PyThaiNLP, Docker, k3s, Argo CD
---

A small web app to practice reading Thai out loud. It shows a sentence in Thai
script with its romanization and English translation, records you reading it,
sends the audio to a speech-to-text service and scores how close the
transcription is to the original sentence.

**[Open the app ↗](https://t.marso.ar)** · [Source code](https://github.com/3ll34ndr0/thai-practice)

## How it works

- **Frontend:** plain HTML, CSS and JavaScript that records audio in the browser.
- **Backend:** FastAPI with two endpoints, `GET /api/exercise` (a random sentence from
  15 beginner phrases) and `POST /api/submit` (audio in, transcription and score out).
  Thai text is compared with [PyThaiNLP](https://pythainlp.org/). Uploads are
  size-limited and rate-limited, since every attempt calls a paid speech-to-text API.
- **Deployment:** GitOps. A push to `main` builds a container image and pushes it to
  GHCR. The workflow then commits the new image tag to the Kubernetes manifests,
  and Argo CD syncs them into a k3s cluster on a VPS. Cloudflare sits in front.
