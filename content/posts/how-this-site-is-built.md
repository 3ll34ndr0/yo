---
title: How this site is built
date: 2026-10-01
tags: meta, ci-cd
---

This site has no server, no database and no admin panel. It's a folder of
Markdown in a Git repo, and a `git push` publishes it in about 30 seconds.

<div class="flow">
<svg viewBox="0 0 820 340" role="img" aria-labelledby="flow-title flow-desc">
<title id="flow-title">How marso.ar is built and deployed</title>
<desc id="flow-desc">A git push to the GitHub repo triggers two GitHub Actions workflows. site.yml builds static HTML with Nicolino and deploys it to GitHub Pages. dns.yml applies DNS records to Cloudflare with DNSControl. Cloudflare points marso.ar to GitHub Pages. A daily schedule also rebuilds the site.</desc>
<defs>
<marker id="flow-arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" class="flow-arrowhead"/></marker>
</defs>
<rect class="flow-lane flow-lane-site" x="360" y="22" width="455" height="136" rx="14"/>
<text class="flow-lane-label" x="376" y="42">BUILD &amp; DEPLOY</text>
<rect class="flow-lane flow-lane-dns" x="360" y="190" width="455" height="136" rx="14"/>
<text class="flow-lane-label" x="376" y="210">DNS AS CODE</text>
<g class="flow-node"><rect x="8" y="133" width="134" height="76" rx="12"/><text class="flow-title" x="75" y="166">git push</text><text class="flow-sub" x="75" y="186">Markdown + config</text></g>
<g class="flow-node flow-node-repo"><rect x="178" y="125" width="150" height="92" rx="12"/><text class="flow-title" x="253" y="158">GitHub repo</text><text class="flow-sub" x="253" y="178">3ll34ndr0/yo</text><text class="flow-sub" x="253" y="196">single source of truth</text></g>
<g class="flow-node flow-pill"><rect x="190" y="38" width="126" height="40" rx="20"/><text class="flow-sub" x="253" y="63">daily rebuild ⏱</text></g>
<g class="flow-node flow-node-site"><rect x="380" y="52" width="200" height="94" rx="12"/><text class="flow-title" x="480" y="82">site.yml</text><text class="flow-sub" x="480" y="102">nicolino build → static HTML</text><text class="flow-sub" x="480" y="120">only when site files change</text></g>
<g class="flow-node flow-node-dns"><rect x="380" y="220" width="200" height="94" rx="12"/><text class="flow-title" x="480" y="250">dns.yml</text><text class="flow-sub" x="480" y="270">DNSControl preview → push</text><text class="flow-sub" x="480" y="288">reviewed + approved</text></g>
<g class="flow-node flow-node-site"><rect x="628" y="52" width="176" height="94" rx="12"/><text class="flow-title" x="716" y="82">GitHub Pages</text><text class="flow-sub" x="716" y="102">CDN + free HTTPS</text><text class="flow-sub flow-url" x="716" y="122">https://marso.ar</text></g>
<g class="flow-node flow-node-dns"><rect x="628" y="220" width="176" height="94" rx="12"/><text class="flow-title" x="716" y="250">Cloudflare</text><text class="flow-sub" x="716" y="270">DNS zone marso.ar</text><text class="flow-sub" x="716" y="288">records live in Git</text></g>
<path class="flow-edge" d="M142,171 H174" marker-end="url(#flow-arrow)"/>
<path class="flow-edge flow-edge-site" d="M328,155 C354,155 352,114 376,114" marker-end="url(#flow-arrow)"/>
<path class="flow-edge flow-edge-dns" d="M328,187 C354,187 352,267 376,267" marker-end="url(#flow-arrow)"/>
<path class="flow-edge flow-edge-dashed" d="M316,58 C350,58 352,70 376,70" marker-end="url(#flow-arrow)"/>
<path class="flow-edge flow-edge-site" d="M580,99 H624" marker-end="url(#flow-arrow)"/>
<text class="flow-edge-label" x="602" y="91">deploy</text>
<path class="flow-edge flow-edge-dns" d="M580,267 H624" marker-end="url(#flow-arrow)"/>
<text class="flow-edge-label" x="602" y="259">API</text>
<path class="flow-edge flow-edge-dns" d="M716,220 V150" marker-end="url(#flow-arrow)"/>
<text class="flow-edge-label flow-edge-label-left" x="708" y="190">A / AAAA</text>
</svg>
</div>

## The pieces

- **[Nicolino](https://nicolino.ralsina.me/)** turns Markdown into HTML. It's a
  single static binary that builds this site in under a second.
- **GitHub Actions** runs two workflows. `site.yml` builds and deploys the site,
  and `dns.yml` applies DNS changes with [DNSControl](https://docs.dnscontrol.org/).
- **GitHub Pages** serves the result over HTTPS, at no cost.
- **Cloudflare** hosts the DNS, but its records are defined in the repo, not
  clicked together in a dashboard.

## Why do it this way

- **Push to deploy.** Committing is publishing, and a typo fix goes live in about
  30 seconds. Pull requests build the site first, so a broken page never reaches `main`.
- **Static output.** The result is plain HTML and CSS, with nothing running on a
  server: no runtime to patch, no database to back up and no login to attack. It's fast
  everywhere and served from a CDN.
- **Free, managed hosting.** GitHub Pages handles hosting, the CDN and TLS certificates,
  so there are no servers or renewals to look after.
- **Everything as code, DNS included.** The DNS records live in `dns/dnsconfig.js`.
  A change shows a preview on the pull request and is applied only after approval.
  Records can't drift and every change has a history.
- **Live data, baked in at build time.** The GitHub heatmap and the Claude Code
  usage panel on the home page are computed during the build and embedded as SVG.
  Visitors' browsers make no API calls and the site keeps no tokens. A daily
  scheduled build keeps them fresh.
- **CI only when needed.** Path filters decide what runs. Editing a post rebuilds
  the site, editing DNS runs the DNS job, and editing the README runs nothing.

The whole setup is in the
[3ll34ndr0/yo](https://github.com/3ll34ndr0/yo) repository, including the README
with every decision and why it was made.
