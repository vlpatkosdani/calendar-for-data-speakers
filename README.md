# Data Platform Conference Calendar

A free, self-updating calendar of data-platform conferences — **conference dates, precon days, and Call-for-Speakers (CfS) deadlines** — built from the public [callfordataspeakers.com](https://callfordataspeakers.com) feed.

It produces two things, rebuilt daily:

- **`calendar.ics`** — a subscribable feed (works in Google / Outlook / Apple Calendar). CfS deadlines are timed events at the exact closing instant, so they land on the right day in your local timezone and come with reminders; conference and precon days are all-day.
- **`index.html`** — a browsable page with two views you can toggle between: a **list** sorted by the next CfS deadline, and a **month-by-month calendar** grid. Both share filters for **online / in-person** and, for in-person events, **continent**; clicking a day in the calendar shows that day's deadlines, precons, and conferences.

Both are hosted on GitHub Pages. Hosting and compute are **$0**; the only thing that costs anything is the LLM step, which stays inside Gemini's free tier.

---

## How it works

```
callfordataspeakers.com/api/events   (public JSON)
        │  fetch
        ▼
   filter to conferences/precons      (drops weekly user groups)
        │
        ▼
   precon date extraction             (Gemini, free tier + on-disk cache)
        │
        ▼
   build.py  ──►  public/calendar.ics
             └──►  public/index.html
        │
        ▼
   GitHub Actions (daily cron) ──► GitHub Pages
```

The upstream feed only flags **that** an event has a precon (an `EventType` tag like `Conference, Precon`); the actual **precon date** usually lives in free text (`"24.09 pre-con workshops, 25.09 sessions"`) or has to be inferred from the date span. The Gemini step turns that into structured dates, with manual overrides for the cases it can't get.

---

## Setup (about 10 minutes)

1. **Create a repo from these files.** Easiest reliable way: `git init` in this folder, commit everything, and push — that preserves the `.github/workflows/` path and every module. (Uploading files one at a time in the web UI is where folders like `.github/workflows/` get missed.)
2. **Get a free Gemini API key** at [aistudio.google.com](https://aistudio.google.com) → *Get API key*. No credit card required.
3. **Add the key as a secret:** repo *Settings → Secrets and variables → Actions → New repository secret*, name it `GEMINI_API_KEY`.
4. **Enable Pages:** *Settings → Pages → Build and deployment → Source = GitHub Actions*.
5. *(Optional)* add repository **variables** (*same screen → Variables tab*):
   - `SITE_URL` — your Pages URL, e.g. `https://yourname.github.io/conference-calendar` (only used to print the subscribe URL on the page).
   - `GEMINI_MODEL` — defaults to `gemini-2.5-flash`; `gemini-2.5-flash-lite` has a higher free rate limit (≈15/min vs 5/min), so the first run finishes faster.
   - `GEMINI_RPM` — requests/minute cap to self-throttle under (auto-set to 5 for flash, 15 for flash-lite; override if Google changes the limit).
6. **Run it once:** *Actions → Build & deploy calendar → Run workflow* (or just push a commit).

Your calendar is then at `https://<you>.github.io/<repo>/` and the feed at `…/calendar.ics`.

### Subscribing
- **Google Calendar:** *Other calendars → + → From URL* → paste the `calendar.ics` URL.
- **Outlook:** *Add calendar → Subscribe from web* → paste the URL.
- **Apple Calendar:** *File → New Calendar Subscription* → paste the URL (tip: swap `https://` for `webcal://`).

Subscribed calendars refresh on the client's own schedule (often daily), so subscribers get updates automatically.

---

## Run locally

```bash
pip install -r requirements.txt
export GEMINI_API_KEY=...        # optional — without it, precon dates are skipped (everything else still builds)
python build.py                  # writes ./public/calendar.ics and ./public/index.html
```

Open `public/index.html` in a browser to preview.

---

## The precon free-text problem & overrides

For each event tagged as having a precon, Gemini reads the name, dates, and `Information` text and returns `{precon_date, main_start, main_end, confidence}`. It only returns a date it can justify from the text or span, and marks low/medium confidence when it had to infer — those rows show a "verify on the event page" note.

When a precon date **isn't in the feed at all**, add it by hand in **`overrides.json`** (keyed by exact `EventName`). Overrides always win:

```json
{
  "SQLDay Lite 2026": { "precon_date": "2026-09-24", "main_start": "2026-09-25", "main_end": "2026-09-25" }
}
```

---

## Costs & the Gemini free tier

- **Hosting/compute: $0.** Public-repo GitHub Actions and Pages are free.
- **Gemini: free tier.** Flash and Flash-Lite are available free via Google AI Studio with no credit card (Pro models moved to paid in 2026). Free-tier rate limits (~10–15 requests/min, a few hundred to ~1,500/day depending on model) are far more than this needs, because the **cache** means only *new or changed* events ever hit the API — typically a handful per day.
- **Privacy caveat:** on the free tier, Google may use your prompts/responses to improve their models. Here the inputs are **public conference info**, so the sensitivity is low — but if that matters to you, enable Gemini billing (paid tier excludes training use) or switch the parser to another provider.

---

## Operational notes

- **Daily cron is best-effort.** GitHub may delay scheduled runs under load. Also, scheduled workflows on a repo get **auto-disabled after ~60 days of inactivity**, and commits made by the default Actions bot don't reliably reset that timer. The workflow commits the precon cache on each run (which helps), but if your schedule ever goes quiet, either run it manually now and then or push the commit step with a Personal Access Token instead of the default token.
- **Adding / fixing conferences:** the data is upstream. Submit or correct events at [callfordataspeakers.com](https://callfordataspeakers.com) (via their GitHub) and they'll flow in on the next build. Use `overrides.json` only for local date fixes.
- **Customizing:** edit `INCLUDE_TAGS` in `build.py` to change which event types are listed, `CFS_REMINDER_DAYS` for reminder timing, and the `INDEX_TEMPLATE` string in `site_template.py` for the page design.
- **Rate limits & first run:** the free tier caps requests per minute (gemini-2.5-flash = 5/min). The parser self-throttles to `GEMINI_RPM` and backs off on HTTP 429, so the **first run can take a few minutes** while it parses every precon-bearing event once. After that the cache means only new events are parsed, so daily runs take seconds. Progress is saved to the cache after each parse, so an interrupted run resumes where it left off.
- **Online vs in-person & continent** are derived in `build.py` from the feed's `Regions` tokens (`Virtual` / `In-Person` / continent names), falling back for in-person events that list only a venue to: coordinates, then a country-name lookup, then a US state+ZIP pattern (e.g. `Alpharetta, GA 30009` → North America). They're also written to each event's iCalendar `CATEGORIES` (e.g. `Conference,In person,Europe`), so calendar apps that support category filtering or colouring can use them too. A few venues give no usable signal at all (e.g. a Lima or Joinville address with no country, ZIP, or coordinates) — those simply show no continent tag.

---

## Files

| File | Purpose |
|------|---------|
| `build.py` | Orchestrator: fetch → filter → ICS + HTML |
| `precon_parser.py` | Gemini precon-date extraction, caching, rate-limiting |
| `site_template.py` | Browse-page HTML template (embedded, no folder needed) |
| `overrides.json` | Manual precon/main date fixes |
| `.github/workflows/update.yml` | Daily build + Pages deploy |
| `requirements.txt` | Python dependencies |

---

*A community-built view of Call for Data Speakers' open data. Not affiliated with or endorsed by Call for Data Speakers / Structured Concepts.*