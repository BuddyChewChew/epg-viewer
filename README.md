# EPG Now/Next

Paste in a link to a TV guide file (called an "XMLTV" file), click a button,
and see a webpage listing every channel's ID, name, and what's playing right
now and next. No coding, no installing anything on your computer — it all
runs on GitHub's servers for free.

This guide assumes you've never set up a GitHub repo before. Every step is
spelled out. If a step doesn't say to type something, just click.

---

## Part 1 — Create the repo

1. Go to **github.com** and log in.
2. Click the **+** icon in the top-right corner of the page → **New repository**.
3. Under "Repository name," type a name with no spaces, for example:
   `epg-now-next`
4. Leave everything else as the default.
5. Make sure **Public** is selected (not Private) — this lets the free
   GitHub Pages hosting work without needing a paid plan.
6. Check the box that says **"Add a README file."**
7. Click the green **Create repository** button at the bottom.

You now have an empty repo with one file in it (`README.md`). We're about
to replace it and add the rest.

---

## Part 2 — Add the 4 files

You should now be looking at your new repo's main page.

1. Click **Add file** (a button near the top right, above the file list) →
   **Create new file**.
2. In the box that says "Name your file...", type exactly:
   `fetch_epg.py`
3. Below that, a big empty text box appears. Open the `fetch_epg.py` file
   you were given, select all its text, copy it, and paste it into that box.
4. Scroll down, click the green **Commit changes...** button, then click
   **Commit changes** again in the popup.

Repeat the same 4 steps for **`index.html`** — click **Add file → Create
new file**, name it `index.html`, paste its contents, commit.

Now for the workflow file, which needs to go in a specific folder:

5. Click **Add file → Create new file** again.
6. In the name box, type exactly (including the slashes):
   `.github/workflows/update-epg.yml`
   GitHub will automatically turn this into folders for you as you type the
   slashes — that's normal and correct.
7. Paste in the contents of the `update-epg.yml` file you were given.
8. Commit changes, same as before.

Last, create an empty placeholder so the `data` folder exists:

9. Click **Add file → Create new file**.
10. Name it: `data/.gitkeep`
11. Leave the contents completely empty.
12. Commit changes.

**Check yourself:** click on your repo's name at the top to go back to the
main page. You should now see: `.github`, `data`, `fetch_epg.py`,
`index.html`, `README.md` — five items total.

---

## Part 3 — Turn on two settings (one-time)

These two switches are off by default on every new repo. Both are required.

### Setting A — let the robot save files

1. Click the **Settings** tab (top of the repo page, may need to click a
   `...` if your screen is narrow).
2. In the left sidebar, click **Actions**, then click **General**
   underneath it.
3. Scroll down to the section called **"Workflow permissions."**
4. Click the circle next to **"Read and write permissions."**
5. Click the **Save** button just below it.

### Setting B — turn on the website

1. Still in **Settings**, click **Pages** in the left sidebar.
2. Under "Build and deployment" → "Source," make sure it says
   **"Deploy from a branch."**
3. Under "Branch," click the dropdown that says "None," change it to
   **`main`**, leave the folder as **`/ (root)`**, and click **Save**.
4. Wait about 1 minute, then refresh the page. A green box should appear
   near the top saying your site is live, with a link like:
   `https://yourname.github.io/epg-now-next/`

**Write that link down or bookmark it** — that's your permanent page. It
won't change.

---

## Part 4 — Get your first data

The page is live, but it'll just say "Loading…" forever until you run it
once.

1. Click the **Actions** tab at the top of your repo.
2. If you see a yellow banner about enabling workflows, click the green
   **"I understand my workflows, go ahead and enable them"** button.
3. In the left sidebar, click **"Fetch EPG (manual)."**
4. On the right side, click the **Run workflow** dropdown button.
5. A small box appears with a field called **url**. Paste in a TV guide
   link, for example:
   `https://epgshare01.online/epgshare01/epg_ripper_US_LOCALS1.xml.gz`
6. (Optional) In the **label** field, type something short like `US Locals`
   — this is just a name that'll show on your page.
7. Click the green **Run workflow** button inside that box.
8. Wait about 15 seconds, then refresh the page. A small dot or checkmark
   will turn from yellow to green when it's done. A red ✕ means something
   went wrong — see Troubleshooting below.
9. Go to your bookmarked page link from Part 3. Refresh it. You should now
   see a table of channels.

**That's it — fully set up.**

---

## Checking a different source later

Anytime you want to look at a different TV guide:

1. **Actions tab → "Fetch EPG (manual)" → Run workflow**
2. Paste in the new link
3. Run workflow, wait ~15 seconds
4. Refresh your bookmarked page

Each time you do this, it **replaces** what was there before — old channels
disappear, only the newest source you ran shows up. That's expected.

---

## Who else can use this

- **Anyone can view your page** (the bookmarked link) — it's a public
  website. No limit on how many people look at it at once; it costs you
  nothing.
- **Only you can click "Run workflow"** — that button only appears for
  people with write access to the repo (you, or anyone you specifically
  add as a collaborator in Settings → Collaborators). A visitor just
  looking at your repo or your page cannot run anything.
- If someone else wants their own copy to run themselves, they'd need to
  click **Fork** (top of your repo page) to make their own separate copy.
  Their copy runs on their own account and never touches yours.

---

## Troubleshooting

**Page says "Loading data/epg_data.json…" forever**
You haven't run the workflow yet, or it failed. Go to the Actions tab and
check for a red ✕ next to the most recent run.

**Red ✕ next to a run in the Actions tab**
Click on that run, then click the step with the ✕ to see the error message
in red text. Common causes:
- The URL was typo'd or isn't a real XMLTV file
- The source website was temporarily down

**Page shows "404" when you visit your bookmarked link**
- Double check the exact link from the green box in Settings → Pages —
  it must match exactly, including the repo name.
- Pages can take a minute or two after first turning it on. Wait and
  refresh.

**"Run workflow" button doesn't appear in the Actions tab**
You're logged into an account that doesn't have write access to this repo.
Make sure you're logged in as the account that created the repo.

**Nothing happens after pasting in a really huge file's URL**
Very large sources can take longer than usual. Give it up to a minute
before assuming it failed — check the Actions tab for progress.
