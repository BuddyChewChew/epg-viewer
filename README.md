# EPG Now/Next (GitHub Actions edition)

Shows channel IDs, display names, and what's airing now/next from any XMLTV
source — fetched server-side by GitHub Actions (Python), so there's no CORS,
no browser proxy, and no download-manager-extension interference of any kind.

## How it fits together

```
fetch_epg.py                    -- does the actual fetching + parsing
.github/workflows/update-epg.yml -- runs fetch_epg.py on a schedule, or on demand
data/epg_data.json               -- output of the script, committed to the repo
index.html                       -- static page that reads data/epg_data.json
```

The page never makes a request to epgshare01.online (or anywhere else)
itself — it only ever reads a JSON file sitting in the same repo. All the
actual network fetching happens inside the GitHub Actions runner, which is a
plain server making a plain HTTP request — CORS is a browser-only concept
and doesn't apply there at all.

## One-time setup

1. Create a new GitHub repo (or use an existing one) and add these four
   files/folders, keeping the same relative paths:
   - `fetch_epg.py`
   - `.github/workflows/update-epg.yml`
   - `index.html`
   - `data/` (can start empty — the workflow creates `epg_data.json` inside it)
2. Push to GitHub.
3. **Settings → Actions → General → Workflow permissions** → select
   "Read and write permissions" and save. (Needed so the Action can commit
   `data/epg_data.json` back to the repo.)
4. **Settings → Pages** → Source: "Deploy from a branch" → Branch: `main`,
   folder `/ (root)` → Save. GitHub will give you a URL like
   `https://yourname.github.io/your-repo/`.
5. Go to the **Actions** tab → click into "Update EPG data" → **Run workflow**
   (leave the URL field blank) to do the first run manually instead of
   waiting for the schedule. This creates `data/epg_data.json` for the
   first time.
6. Visit your GitHub Pages URL. You should see the table.

## Day-to-day use

**Automatic:** every 30 minutes, the workflow re-fetches the three default
sources (US Locals, US1, US2) and commits the updated JSON if anything
changed. The page picks up the new data automatically (it re-checks the
JSON file every 5 minutes).

**Paste a URL to spot-check anything:**
1. Go to the **Actions** tab → "Update EPG data" → **Run workflow**
2. Paste any XMLTV URL into the `url` field (works with `.xml` or `.xml.gz`)
3. Optionally set a `label` (defaults to "Manual Check")
4. Click **Run workflow**, wait ~10–20 seconds
5. Reload the page — your pasted source now shows as a tab with Channel ID,
   Name, Now Playing, and Up Next

Note: a manual run **replaces** the committed dataset with just that one
source until the next scheduled run restores the three defaults. That's
intentional — it's meant for quick spot-checks, not permanent additions.
If you want a source to stick around permanently, add it to
`DEFAULT_SOURCES` in `fetch_epg.py` instead (see below).

## Adding a permanent source

Edit `DEFAULT_SOURCES` near the top of `fetch_epg.py`:

```python
DEFAULT_SOURCES = [
    {"key": "locals", "label": "US Locals", "url": "https://epgshare01.online/epgshare01/epg_ripper_US_LOCALS1.xml.gz"},
    {"key": "us1",    "label": "US1",       "url": "https://epgshare01.online/epgshare01/epg_ripper_US1.xml.gz"},
    {"key": "us2",    "label": "US2",       "url": "https://epgshare01.online/epgshare01/epg_ripper_US2.xml.gz"},
    # add more here:
    # {"key": "uk1", "label": "UK", "url": "https://epgshare01.online/epgshare01/epg_ripper_UK1.xml.gz"},
]
```

Commit the change; the next scheduled (or manual, blank-URL) run picks it up.

## Changing the refresh schedule

Edit the cron line in `.github/workflows/update-epg.yml`:

```yaml
schedule:
  - cron: "*/30 * * * *"   # every 30 min. Change to "0 * * * *" for hourly, etc.
```

## What the page shows

- One tab per source. A source that failed to fetch/parse shows in red with
  the error message instead of a row count.
- Table columns: Channel ID (what you match against `tvg-id` in your `.m3u`
  files), Display Name, Now Playing (with a live progress bar), Up Next.
- Search box filters by ID or name.
- Click a column header to sort. "copy id" button per row.
