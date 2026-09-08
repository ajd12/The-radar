# THE RADAR — fixed live PWA

This version fixes the GitHub Actions feed updater by creating `data/` automatically before writing `data/feeds.json`.

Repository structure:
- `index.html`
- `manifest.json`
- `sw.js`
- `scripts/update_feeds.py`
- `.github/workflows/update-feeds.yml`

After these files are committed to GitHub:
1. Open **Actions → Update Radar Feeds**.
2. Choose **Run workflow** on `main`.
3. A successful run creates `data/feeds.json` automatically.
4. GitHub Pages then serves the updated Radar.

Do not upload `__pycache__` folders.
