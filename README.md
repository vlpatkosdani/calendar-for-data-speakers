# Data Conference Calendar

Self-updating calendar of data-platform conferences, precons, and Call-for-Speakers (CfS) deadlines — sourced from [callfordataspeakers.com](https://callfordataspeakers.com/). Subscribe once and it stays current on its own.

## Use it

- **Browse:** https://vlpatkosdani.github.io/calendar-for-data-speakers/
- **Subscribe (.ics):** `https://vlpatkosdani.github.io/calendar-for-data-speakers/calendar.ics`

Add that `.ics` URL to Google Calendar, Apple Calendar, or Outlook (look for *"Subscribe to calendar"* / *"From URL"*) and new conferences and deadlines show up automatically — with reminders ahead of each CfS deadline. Free, no account, no signup, no ads.

## Who it's for

Anyone in the data-platform community — SQL Server, Azure Data, Fabric, Power BI and friends — who wants the season in one place:

- **Speakers** tracking Call-for-Speakers deadlines so a submission window never slips by.
- **Attendees** choosing which conferences and pre-conference (precon) days to attend.
- **Organizers and community folks** who just want it all at a glance.

## Built upon

Event data comes from the community-run [callfordataspeakers.com](https://callfordataspeakers.com/) — the open [dataplat/DataSpeakers](https://github.com/dataplat/DataSpeakers/) project. That site doesn't publish a calendar feed, so this project reads its data and turns it into one. The listings aren't mine; all credit for them goes upstream.

## How it works

A GitHub Action runs once a day and:

1. **Fetches** the latest events from the callfordataspeakers.com API.
2. **Filters** them down to conferences and precons (leaving out things like user-group meetups).
3. **Resolves precon dates** — conference and CfS dates come straight from the source, but precon dates are usually buried in free-text descriptions, so they're extracted automatically (with an AI model), backed by a manual override file for anything it misreads.
4. **Generates** a subscribable `calendar.ics` feed and a web page (month view, filters, and a "closing soon" panel) from the same data.
5. **Publishes** it to GitHub Pages.

> Note: some precon dates are inferred from descriptions, so confirm the exact day on the event's own page.

## Status & contributing

This is an early, evolving project and help is genuinely welcome. If a date looks wrong, an event is missing, or you have an idea:

- **Open an issue** here, or
- **Message me on [LinkedIn](https://www.linkedin.com/in/danielgaborpatkos/)**
Corrections to precon dates are especially useful.

## License

Code is released under the [MIT License](LICENSE). The event data isn't covered by that — it belongs to callfordataspeakers.com / the dataplat/DataSpeakers project and is subject to their terms.
