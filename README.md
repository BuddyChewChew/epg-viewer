# EPG Now/Next (GitHub Actions edition)

Paste an XMLTV URL into the GitHub Actions "Run workflow" form, and see
channel IDs, display names, and what's airing now/next — fetched server-side
by Python (no CORS, no browser proxy, no download-manager interference).

## How it fits together

```
fetch_epg.py                     -- fetches ONE source, trims to now+next, overwrites the JSON
.github/workflows/update-epg.yml -- manual-only trigger (Actions tab "Run workflow"), takes a URL input
data/epg_data.json                -- output of the script, committed to the repo
index.html                        -- static page that reads data/epg_data.json
```

The page never fetches epgshare01.online (or anywhere else) directly — it
only reads a small JSON file already sitting in the repo. All network
fetching happens inside the GitHub Actions runner, which makes a plain
server-side HTTP request. CORS is a browser-only concept and never applies
there.

## Why the output stays small

Real XMLTV guides carry multiple days of programmes per channel — across a
few hundred channels that adds up to tens of megabytes per source, easily
blowing past GitHub's 100 MB file limit if dumped to JSON as-is (this is
what happened originally: 146 MB from combining several full sources at
once).

`fetch_epg.py` fixes this at the parsing stage, not after: it streams
through the XML with `iterparse` and, for each channel, keeps only the
programme that's airing **right now** and the one **immediately after it**.
Everything else — all past programmes, and anything beyond the very next
one — is discarded as it's read, never held in memory or written out. A
650-channel, multi-day guide that's 13 MB uncompressed typically reduces to
well under 1 MB of output.

## One-time setup

1. Add these files to a repo, keeping the same relative paths:
   - `fetch_epg.py`
   - `.github/workflows/update-epg.yml`
   - `index.html`
   - `data/` (starts empty — the workflow creates `epg_data.json` inside it
     on first run)
2. Push to GitHub.
3. **Settings → Actions → General → Workflow permissions** → "Read and
   write permissions" → Save. (Needed so the Action can commit
   `data/epg_data.json`.)
4. **Settings → Pages** → Source: "Deploy from a branch" → Branch `main`,
   folder `/ (root)` → Save. You'll get a URL like
   `https://yourname.github.io/your-repo/`.

## Using it

1. Go to the **Actions** tab → "Fetch EPG (manual)" → **Run workflow**
2. Paste an XMLTV URL into the `url` field (`.xml` or `.xml.gz` both work)
3. Optionally set a `label` (e.g. "US Locals") — shown on the page
4. Click **Run workflow**, wait ~10–20 seconds
5. Open (or reload) your GitHub Pages URL

Each run **fully replaces** `data/epg_data.json`. There's no merging with a
previous run and nothing accumulates — paste a new URL and run again, and
the old source's channels are gone entirely, replaced by the new one. If
you want to compare two sources, run one, note what you need, then run the
other.

## What the page shows

- Channel ID (what you match against `tvg-id` in your `.m3u` files)
- Display Name
- Now Playing, with a live progress bar
- Up Next
- Search box filters by ID or name
- Click a column header to sort; "copy id" button per row

## Adjusting the size of the deliberately tiny output

The lookahead is hard-fixed at exactly one programme (current + next) per
channel — this is what keeps the file small and commit-friendly on every
run. If you want a bit more lookahead later, the place to change it is the
`next` logic inside `parse_xmltv_streaming()` in `fetch_epg.py` (currently
keeps only the single soonest future programme per channel; extending it to
keep, say, the next 3 would need a small list instead of a single slot,
trading some file size for more visibility).
