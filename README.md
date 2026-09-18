# THE RADAR — V4 foundation build

This ZIP is a complete replacement for the existing static PWA. It is designed for GitHub Pages and requires no build system, npm install, API key, backend server, or manual code merging.

## Install

1. Back up the current repository.
2. Extract this ZIP into the repository root.
3. Commit and push all files to the branch used by GitHub Pages.
4. Open **Actions → Update Radar Feeds → Run workflow** once.
5. After the workflow succeeds, reload the GitHub Pages site.

The scheduled workflow refreshes the committed `data/feeds.json` snapshot every two hours.

## Included

- Responsive PWA interface
- Doomscroll feed with category tabs
- Search and sorting
- Local saved signals
- Radar/map placeholder view
- Feed health panel
- Normalized signal schema
- Source registry
- Automotive-aware ontology covering design, development, testing and release intelligence
- GitHub Actions feed updater
- Service-worker cache with network-first feed behavior

## Important GitHub Pages setting

If GitHub Pages is configured to deploy from `/root` or `/docs`, use the same location as before. This ZIP assumes the repository root is the published directory.

## Feed behavior

The browser does not call RSS, Reddit, arXiv, or Hacker News directly. GitHub Actions fetches and normalizes sources into `data/feeds.json`; the PWA reads that committed file. This avoids browser CORS problems and makes the deployed app deterministic.

If a source fails, the workflow still writes a snapshot and records the source failure in the `health` array.

## Files

- `index.html` — complete UI and client logic
- `manifest.json` — PWA metadata
- `sw.js` — service worker
- `data/source-registry.json` — source configuration
- `data/ontology.json` — signal and automotive ontology
- `data/feeds.json` — generated snapshot placeholder
- `scripts/update_feeds.py` — source ingestion and normalization
- `.github/workflows/update-feeds.yml` — scheduled updater

## Local testing

From the repository root:

```bash
python -m http.server 8000
```

Then open `http://localhost:8000/`.

Do not open `index.html` directly with `file://`; browser fetch restrictions will prevent the feed snapshot from loading.


## Expanded automotive sources

The feed registry includes Reddit engineering/automotive discussions, selected Substack newsletters, DieselNet, Google News RSS queries for Automotive News and SAE-related technical papers, plus vehicle-connectivity, automotive-cybersecurity, and software-defined-vehicle searches. Reddit is fetched server-side through its public JSON listing endpoint; the browser still consumes only the committed `data/feeds.json` snapshot.

Some publishers do not expose a stable public RSS feed or place content behind a subscription. For those, the registry uses a clearly labelled Google News RSS query rather than pretending it is a direct publisher feed.


## Source strategy
This build includes university/research sources (MIT News, Stanford Engineering, Berkeley transportation research), specialist automotive sources, and consulting/industry-monitoring queries for McKinsey, BCG, Bain, Deloitte, and PwC. Consulting feeds use Google News RSS site queries because many consulting sites do not expose stable public RSS feeds.

## If the website shows no signals
The browser reads `data/feeds.json`; it does not fetch sources directly. In GitHub, run **Actions → Update Radar Feeds → Run workflow** and confirm that the action commits a changed `data/feeds.json`. If the action fails, open the failed **Fetch and normalize sources** step. The updater records individual source failures in `health` while still writing the snapshot.
