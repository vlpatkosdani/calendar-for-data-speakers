from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import html
import json
import re
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

SOURCE_URL = "https://callfordataspeakers.com"
DEFAULT_OUTPUT_DIR = "docs"


@dataclass(frozen=True)
class Event:
    title: str
    conference_start: dt.date | None = None
    conference_end: dt.date | None = None
    precon_start: dt.date | None = None
    precon_end: dt.date | None = None
    cfp_deadline: dt.date | None = None
    url: str | None = None
    location: str | None = None


def fetch_text(url: str) -> str:
    with urllib.request.urlopen(url, timeout=30) as response:
        return response.read().decode("utf-8")


def fetch_json(url: str) -> Any:
    text = fetch_text(url)
    return json.loads(text)


def _parse_date(value: Any) -> dt.date | None:
    if not value:
        return None
    if isinstance(value, dt.date):
        return value
    if isinstance(value, dt.datetime):
        return value.date()
    text = str(value).strip()
    if not text:
        return None
    text = text.replace("Z", "+00:00")
    for parser in (dt.date.fromisoformat, dt.datetime.fromisoformat):
        try:
            parsed = parser(text)
            return parsed if isinstance(parsed, dt.date) and not isinstance(parsed, dt.datetime) else parsed.date()
        except ValueError:
            pass
    match = re.search(r"(\d{4}-\d{2}-\d{2})", text)
    if match:
        return dt.date.fromisoformat(match.group(1))
    return None


def _pick(data: dict[str, Any], *keys: str) -> Any:
    for key in keys:
        if key in data:
            return data[key]
    lowered = {k.lower(): v for k, v in data.items()}
    for key in keys:
        if key.lower() in lowered:
            return lowered[key.lower()]
    return None


def _is_event_like(item: Any) -> bool:
    if not isinstance(item, dict):
        return False
    title = _pick(item, "title", "name", "conference", "event", "event_name")
    dateish = _pick(
        item,
        "cfp_deadline",
        "deadline",
        "conference_start",
        "start_date",
        "date",
        "startDate",
    )
    return bool(title and dateish)


def _extract_candidates(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    if isinstance(payload, dict):
        for key in ("events", "data", "items", "conferences", "cfps"):
            value = payload.get(key)
            if isinstance(value, list):
                return [item for item in value if isinstance(item, dict)]
        candidates: list[dict[str, Any]] = []
        stack: list[Any] = [payload]
        while stack:
            current = stack.pop()
            if isinstance(current, dict):
                if _is_event_like(current):
                    candidates.append(current)
                stack.extend(current.values())
            elif isinstance(current, list):
                stack.extend(current)
        if candidates:
            return candidates
    raise ValueError("Unable to locate event data in payload")


def normalize_events(payload: Any) -> list[Event]:
    events: list[Event] = []
    for item in _extract_candidates(payload):
        title = _pick(item, "title", "name", "conference", "event", "event_name")
        if not title:
            continue
        events.append(
            Event(
                title=str(title).strip(),
                conference_start=_parse_date(_pick(item, "conference_start", "start_date", "startDate", "event_start")),
                conference_end=_parse_date(_pick(item, "conference_end", "end_date", "endDate", "event_end")),
                precon_start=_parse_date(_pick(item, "precon_start", "preconference_start", "preconf_start")),
                precon_end=_parse_date(_pick(item, "precon_end", "preconference_end", "preconf_end")),
                cfp_deadline=_parse_date(_pick(item, "cfp_deadline", "deadline", "cfpDeadline")),
                url=_pick(item, "url", "link", "event_url"),
                location=_pick(item, "location", "city", "venue"),
            )
        )
    if not events:
        raise ValueError("No events were parsed from payload")
    return events


def _ics_escape(value: str) -> str:
    return value.replace("\\", "\\\\").replace(";", "\\;").replace(",", "\\,").replace("\n", "\\n")


def _event_uid(event: Event, kind: str, date: dt.date) -> str:
    key = f"{event.title}|{kind}|{date.isoformat()}"
    digest = hashlib.sha1(key.encode("utf-8")).hexdigest()
    return f"{digest}@calendar-for-data-speakers"


def _ical_all_day(summary: str, date_start: dt.date, date_end_exclusive: dt.date, uid: str, description: str = "") -> str:
    stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    lines = [
        "BEGIN:VEVENT",
        f"UID:{uid}",
        f"DTSTAMP:{stamp}",
        f"DTSTART;VALUE=DATE:{date_start.strftime('%Y%m%d')}",
        f"DTEND;VALUE=DATE:{date_end_exclusive.strftime('%Y%m%d')}",
        f"SUMMARY:{_ics_escape(summary)}",
    ]
    if description:
        lines.append(f"DESCRIPTION:{_ics_escape(description)}")
    lines.append("END:VEVENT")
    return "\r\n".join(lines)


def build_ics(events: Iterable[Event]) -> str:
    vevents: list[str] = []
    for event in events:
        if event.cfp_deadline:
            vevents.append(
                _ical_all_day(
                    summary=f"CFP deadline: {event.title}",
                    date_start=event.cfp_deadline,
                    date_end_exclusive=event.cfp_deadline + dt.timedelta(days=1),
                    uid=_event_uid(event, "cfp", event.cfp_deadline),
                    description=event.url or "",
                )
            )
        if event.precon_start:
            end = event.precon_end or event.precon_start
            vevents.append(
                _ical_all_day(
                    summary=f"Precon: {event.title}",
                    date_start=event.precon_start,
                    date_end_exclusive=end + dt.timedelta(days=1),
                    uid=_event_uid(event, "precon", event.precon_start),
                    description=event.url or "",
                )
            )
        if event.conference_start:
            end = event.conference_end or event.conference_start
            vevents.append(
                _ical_all_day(
                    summary=f"Conference: {event.title}",
                    date_start=event.conference_start,
                    date_end_exclusive=end + dt.timedelta(days=1),
                    uid=_event_uid(event, "conference", event.conference_start),
                    description=event.url or "",
                )
            )

    header = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//calendar-for-data-speakers//EN",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
    ]
    footer = ["END:VCALENDAR", ""]
    return "\r\n".join(header + vevents + footer)


def _milestone_rows(events: Iterable[Event]) -> list[tuple[dt.date, str, str, str | None]]:
    rows: list[tuple[dt.date, str, str, str | None]] = []
    for event in events:
        if event.cfp_deadline:
            rows.append((event.cfp_deadline, "CFP deadline", event.title, event.url))
        if event.precon_start:
            rows.append((event.precon_start, "Precon starts", event.title, event.url))
        if event.conference_start:
            rows.append((event.conference_start, "Conference starts", event.title, event.url))
    return sorted(rows, key=lambda row: row[0])


def build_html(events: Iterable[Event]) -> str:
    rows = _milestone_rows(events)
    table_rows: list[str] = []
    for date, kind, title, url in rows:
        linked_title = f'<a href="{html.escape(url)}">{html.escape(title)}</a>' if url else html.escape(title)
        table_rows.append(
            f"<tr><td>{date.isoformat()}</td><td>{html.escape(kind)}</td><td>{linked_title}</td></tr>"
        )

    generated_at = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    body = "\n".join(table_rows) or "<tr><td colspan='3'>No events available</td></tr>"
    return f"""<!doctype html>
<html lang=\"en\">
<head>
  <meta charset=\"utf-8\" />
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
  <title>Calendar for Data Speakers</title>
  <style>
    body {{ font-family: Arial, sans-serif; max-width: 900px; margin: 2rem auto; padding: 0 1rem; line-height: 1.5; }}
    table {{ width: 100%; border-collapse: collapse; }}
    th, td {{ border: 1px solid #ddd; padding: 0.5rem; text-align: left; }}
    th {{ background: #f3f3f3; }}
  </style>
</head>
<body>
  <h1>Calendar for Data Speakers</h1>
  <p>Subscribe via <a href=\"calendar.ics\">calendar.ics</a>. Data source: <a href=\"{SOURCE_URL}\">callfordataspeakers.com</a>.</p>
  <table>
    <thead><tr><th>Date</th><th>Milestone</th><th>Event</th></tr></thead>
    <tbody>
      {body}
    </tbody>
  </table>
  <p><small>Last generated: {generated_at}</small></p>
</body>
</html>
"""


def _load_payload_from_source(source_url: str) -> Any:
    endpoint_candidates = [
        f"{source_url.rstrip('/')}/api/events",
        f"{source_url.rstrip('/')}/api/events.json",
        f"{source_url.rstrip('/')}/events.json",
    ]
    errors: list[str] = []
    for endpoint in endpoint_candidates:
        try:
            return fetch_json(endpoint)
        except Exception as exc:  # noqa: BLE001
            errors.append(f"{endpoint}: {exc}")

    homepage = fetch_text(source_url)
    next_data_match = re.search(
        r"<script[^>]+id=[\"']__NEXT_DATA__[\"'][^>]*>(.*?)</script>",
        homepage,
        flags=re.DOTALL,
    )
    if next_data_match:
        try:
            return json.loads(next_data_match.group(1))
        except json.JSONDecodeError:
            pass

    raise RuntimeError("Unable to fetch structured event data. Tried:\n" + "\n".join(errors))


def write_outputs(events: list[Event], output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "calendar.ics").write_text(build_ics(events), encoding="utf-8")
    (output_dir / "index.html").write_text(build_html(events), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Build ICS and HTML calendar outputs")
    parser.add_argument("--source-url", default=SOURCE_URL)
    parser.add_argument("--output-dir", default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--input-json", help="Optional local JSON payload for offline generation")
    args = parser.parse_args()

    payload = json.loads(Path(args.input_json).read_text(encoding="utf-8")) if args.input_json else _load_payload_from_source(args.source_url)
    events = normalize_events(payload)
    write_outputs(events, Path(args.output_dir))
    print(f"Generated outputs for {len(events)} events in {args.output_dir}")


if __name__ == "__main__":
    main()
