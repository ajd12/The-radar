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
