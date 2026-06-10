# calendar-for-data-speakers

Self-updating calendar of data-platform conferences, precons, and Call-for-Speakers deadlines from [callfordataspeakers.com](https://callfordataspeakers.com).

- Browse online: `https://<YOUR_GITHUB_USERNAME>.github.io/calendar-for-data-speakers/`
- Subscribe (ICS): `https://<YOUR_GITHUB_USERNAME>.github.io/calendar-for-data-speakers/calendar.ics`

## How it works

- `scripts/build_calendar.py` fetches event data and regenerates `docs/index.html` + `docs/calendar.ics`.
- `.github/workflows/rebuild-calendar.yml` runs daily and deploys the `docs/` folder to GitHub Pages.

## Local run

```bash
python scripts/build_calendar.py
```
