"""
build.py
--------
Builds a data-platform conference calendar from the Call for Data Speakers API.

Outputs (into ./public, ready for GitHub Pages):
  - calendar.ics : a subscribable feed with CfS deadlines + conference + precon days
  - index.html   : a browsable, sortable page (newest CfS deadline first)

Run locally:
  pip install -r requirements.txt
  export GEMINI_API_KEY=...        # optional; precon dates are skipped without it
  python build.py
"""

from __future__ import annotations

import hashlib
import json
import os
import re
from datetime import date, datetime, timedelta, timezone
from typing import Optional

import requests
from dateutil import parser as dtparser
from icalendar import Alarm, Calendar, Event
from jinja2 import Environment

import precon_parser as pp
from site_template import INDEX_TEMPLATE

# ----------------------------------------------------------------------------- config
API_URL = "https://callfordataspeakers.com/api/events"
OUTPUT_DIR = "public"
CACHE_PATH = "cache/precon_cache.json"
OVERRIDES_PATH = "overrides.json"

# Which EventType tags to treat as "a conference worth listing". Anything that is
# ONLY a user group is dropped. Tweak this set to taste.
INCLUDE_TAGS = {"conference", "precon", "external"}

MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
# Free-tier requests/minute cap (gemini-2.5-flash = 5, flash-lite ~15). The parser
# self-throttles to this and also backs off on 429, so a wrong value just costs time.
GEMINI_RPM = int(os.environ.get("GEMINI_RPM") or (15 if "lite" in MODEL else 5))

# Optional absolute URL of the published calendar, shown on the page for copying.
SITE_URL = os.environ.get("SITE_URL", "").rstrip("/")

CAL_NAME = "Data Platform Conference Calendar"
CAL_DESC = "Conference & precon dates plus Call-for-Speakers deadlines for the data platform community. Source: callfordataspeakers.com"
PRODID = "-//community//data-conf-calendar//EN"

# Reminders (days before) attached to each CfS-deadline event.
CFS_REMINDER_DAYS = (7, 1)

MONTHS = ["", "Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


# ----------------------------------------------------------------------------- helpers
def fetch_events() -> list[dict]:
    resp = requests.get(API_URL, timeout=30, headers={"Accept": "application/json"})
    resp.raise_for_status()
    return resp.json()


def type_tags(event: dict) -> set[str]:
    raw = (event.get("EventType") or "").lower()
    return {t.strip() for t in raw.split(",") if t.strip()}


def is_conference(event: dict) -> bool:
    return bool(type_tags(event) & INCLUDE_TAGS)


# ----------------------------------------------------------------------------- location / modality
CONTINENTS = ["Europe", "North America", "South America", "Asia", "Africa", "Oceania"]
_CONTINENT_ALIASES = {
    "europe": "Europe", "north america": "North America", "south america": "South America",
    "asia": "Asia", "africa": "Africa", "oceania": "Oceania", "australia": "Oceania",
    "middle east": "Asia",
}
_ONLINE_VENUE_HINTS = ("online", "virtual", "teams", "zoom", "webinar", "remote", "hybrid")

# Minimal country -> continent fallback for in-person events that list only a country
# (no continent token, no coordinates). Matched as a substring of the Venue string.
_COUNTRY_CONTINENT = {
    "united states": "North America", "usa": "North America", "canada": "North America", "mexico": "North America",
    "brazil": "South America", "peru": "South America", "argentina": "South America",
    "chile": "South America", "colombia": "South America",
    "united kingdom": "Europe", "ireland": "Europe", "germany": "Europe", "france": "Europe",
    "spain": "Europe", "portugal": "Europe", "italy": "Europe", "netherlands": "Europe",
    "belgium": "Europe", "denmark": "Europe", "sweden": "Europe", "norway": "Europe",
    "finland": "Europe", "poland": "Europe", "czechia": "Europe", "czech republic": "Europe",
    "austria": "Europe", "switzerland": "Europe", "bulgaria": "Europe", "croatia": "Europe",
    "romania": "Europe", "hungary": "Europe", "greece": "Europe",
    "india": "Asia", "singapore": "Asia", "japan": "Asia", "china": "Asia", "israel": "Asia",
    "united arab emirates": "Asia",
    "south africa": "Africa", "nigeria": "Africa", "kenya": "Africa", "egypt": "Africa",
    "australia": "Oceania", "new zealand": "Oceania",
}

MODALITY_LABELS = {"online": "Online", "in_person": "In person", "hybrid": "Hybrid"}


def latlong_to_continent(lat: Optional[float], lng: Optional[float]) -> Optional[str]:
    """Rough coordinate -> continent bucket. Fuzzy; used only as a fallback."""
    if lat is None or lng is None or (lat == 0 and lng == 0) or lat < -60:
        return None
    if -170 <= lng <= -30:                       # western hemisphere
        return "North America" if lat >= 13 else "South America"
    if 110 <= lng <= 180 and lat <= 0:           # Australia / NZ / Pacific
        return "Oceania"
    if -20 <= lng <= 52 and -37 <= lat <= 37:    # Africa
        return "Africa"
    if -25 <= lng <= 45 and 34 <= lat <= 72:     # Europe
        return "Europe"
    return "Asia"                                # default eastern-hemisphere landmass


def classify_location(event: dict) -> dict:
    """
    Returns {"modality": "online"|"in_person"|"hybrid", "continents": [...]}.
    `continents` is empty for online-only events (they aren't on a continent).
    """
    tokens = {t.strip().lower() for t in (event.get("Regions") or "").split(",") if t.strip()}
    venue = (event.get("Venue") or "").lower()
    venue_is_online = any(h in venue for h in _ONLINE_VENUE_HINTS)

    continents: list[str] = []
    for t in tokens:
        c = _CONTINENT_ALIASES.get(t)
        if c and c not in continents:
            continents.append(c)

    has_virtual = ("virtual" in tokens) or ("online" in tokens) or venue_is_online
    has_physical = bool(continents) or ("in-person" in tokens) or ("in person" in tokens) \
        or (bool(venue) and not venue_is_online)

    # Physical but no continent token -> try coordinates, then country, then a US ZIP.
    if has_physical and not continents:
        c = latlong_to_continent(event.get("Lat"), event.get("Long"))
        if not c:
            c = next((cont for country, cont in _COUNTRY_CONTINENT.items() if country in venue), None)
        if not c and re.search(r"\b[A-Z]{2}\s+\d{5}(?:-\d{4})?\b", event.get("Venue") or ""):
            c = "North America"  # e.g. "Alpharetta, GA 30009" (US state + ZIP)
        if c:
            continents.append(c)

    if has_virtual and has_physical:
        modality = "hybrid"
    elif has_virtual:
        modality = "online"
    else:
        modality = "in_person"

    if modality == "online":
        continents = []
    return {"modality": modality, "continents": continents}


def to_date(value: Optional[str]) -> Optional[date]:
    if not value:
        return None
    try:
        return dtparser.isoparse(value).date()
    except (ValueError, TypeError):
        return None


def to_datetime(value: Optional[str]) -> Optional[datetime]:
    """Parse an ISO timestamp into a timezone-aware UTC datetime (for exact deadlines)."""
    if not value:
        return None
    try:
        dt = dtparser.isoparse(value)
        return dt.replace(tzinfo=timezone.utc) if dt.tzinfo is None else dt.astimezone(timezone.utc)
    except (ValueError, TypeError):
        return None


def within_span(d: Optional[date], start: Optional[date], end: Optional[date]) -> bool:
    if d is None:
        return False
    lo = start or d
    hi = end or start or d
    return lo <= d <= hi


def fmt_range(start: Optional[date], end: Optional[date]) -> str:
    if not start:
        return "Date TBD"
    if not end or end == start:
        return f"{start.day} {MONTHS[start.month]} {start.year}"
    if start.year == end.year and start.month == end.month:
        return f"{start.day}\u2013{end.day} {MONTHS[start.month]} {start.year}"
    if start.year == end.year:
        return f"{start.day} {MONTHS[start.month]} \u2013 {end.day} {MONTHS[end.month]} {start.year}"
    return f"{start.day} {MONTHS[start.month]} {start.year} \u2013 {end.day} {MONTHS[end.month]} {end.year}"


def fmt_day(d: Optional[date]) -> str:
    return f"{d.day} {MONTHS[d.month]} {d.year}" if d else ""


def stable_uid(*parts: str) -> str:
    h = hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()[:20]
    return f"{h}@data-conf-calendar"


def all_day(ev: Event, start: date, end_inclusive: Optional[date] = None) -> None:
    """Set DTSTART/DTEND for an all-day event (DTEND is exclusive in iCalendar)."""
    ev.add("dtstart", start)
    last = end_inclusive or start
    ev.add("dtend", last + timedelta(days=1))


def add_alarm(ev: Event, days_before: int, text: str) -> None:
    alarm = Alarm()
    alarm.add("action", "DISPLAY")
    alarm.add("description", text)
    alarm.add("trigger", timedelta(days=-days_before))
    ev.add_component(alarm)


# ----------------------------------------------------------------------------- precon resolution
def resolve_schedule(event: dict, info: dict) -> dict:
    """
    Combine the upstream span with the extracted precon info into concrete dates.
    Returns {precon_date, main_start, main_end, has_precon, confidence, note}.
    """
    span_start = to_date(event.get("Date"))
    span_end = to_date(event.get("EndDate")) or span_start

    precon = to_date(info.get("precon_date"))
    main_start = to_date(info.get("main_start"))
    main_end = to_date(info.get("main_end"))

    # Discard any model dates that fall outside the authoritative span.
    if not within_span(precon, span_start, span_end):
        precon = None
    if not within_span(main_start, span_start, span_end):
        main_start = None
    if not within_span(main_end, span_start, span_end):
        main_end = None

    # If we have a precon day but no main range, infer the main range as the rest.
    if precon and not main_start:
        main_start = precon + timedelta(days=1) if (span_end and precon < span_end) else span_start
        main_end = span_end
    if not main_start:
        main_start, main_end = span_start, span_end
    if not main_end:
        main_end = main_start

    return {
        "precon_date": precon,
        "main_start": main_start,
        "main_end": main_end,
        "has_precon": bool(info.get("has_precon")),
        "confidence": info.get("confidence", "low"),
        "note": info.get("note", ""),
    }


def apply_override(name: str, sched: dict, overrides: dict) -> dict:
    ov = overrides.get(name)
    if not ov:
        return sched
    for field in ("precon_date", "main_start", "main_end"):
        if field in ov:
            sched[field] = to_date(ov[field])
    if "has_precon" in ov:
        sched["has_precon"] = bool(ov["has_precon"])
    sched["confidence"] = "high"
    sched["note"] = (sched.get("note", "") + " [manual override]").strip()
    return sched


# ----------------------------------------------------------------------------- ICS
def build_ics(rows: list[dict]) -> bytes:
    cal = Calendar()
    cal.add("prodid", PRODID)
    cal.add("version", "2.0")
    cal.add("method", "PUBLISH")
    cal.add("calscale", "GREGORIAN")
    cal.add("x-wr-calname", CAL_NAME)
    cal.add("name", CAL_NAME)  # RFC 7986
    cal.add("x-wr-caldesc", CAL_DESC)
    cal.add("x-published-ttl", "PT12H")
    cal.add("refresh-interval", timedelta(hours=12), parameters={"VALUE": "DURATION"})

    now = datetime.now(timezone.utc)

    for r in rows:
        name = r["name"]
        venue = r.get("venue") or ""
        url = r.get("url") or ""
        regions = ", ".join(r.get("regions") or [])
        info = (r.get("info") or "").strip()
        base_desc = "\n".join(p for p in [info, f"Regions: {regions}" if regions else "", url] if p)
        loc_cats = [c for c in [MODALITY_LABELS.get(r.get("modality"), "")] + (r.get("continents") or []) if c]

        # 1) Call-for-Speakers deadline (the actionable one) — an exact instant, so it
        #    localizes correctly in each subscriber's calendar (no UTC off-by-one).
        if r.get("cfs_close"):
            deadline = r["cfs_close"]
            cfs = Event()
            cfs.add("uid", stable_uid("cfs", name, deadline.isoformat()))
            cfs.add("summary", f"CfS deadline \u00b7 {name}")
            cfs.add("dtstamp", now)
            cfs.add("dtstart", deadline)
            cfs.add("dtend", deadline + timedelta(minutes=30))
            cfs.add("description", "\n".join(p for p in [f"Call for Speakers closes for {name}.", url] if p))
            if venue:
                cfs.add("location", venue)
            if url:
                cfs.add("url", url)
            cfs.add("categories", ["CfS deadline"] + loc_cats)
            cfs.add("transp", "TRANSPARENT")
            for d in CFS_REMINDER_DAYS:
                add_alarm(cfs, d, f"CfS closing soon: {name}")
            cal.add_component(cfs)

        # 2) Precon day (only when we have a concrete date)
        if r.get("precon_date"):
            pre = Event()
            pre.add("uid", stable_uid("precon", name, str(r["precon_date"])))
            pre.add("summary", f"Precon \u00b7 {name}")
            pre.add("dtstamp", now)
            all_day(pre, r["precon_date"])
            pre.add("description", base_desc)
            if venue:
                pre.add("location", venue)
            if url:
                pre.add("url", url)
            pre.add("categories", ["Precon"] + loc_cats)
            cal.add_component(pre)

        # 3) Main conference
        if r.get("main_start"):
            main = Event()
            main.add("uid", stable_uid("conf", name, str(r["main_start"])))
            main.add("summary", name)
            main.add("dtstamp", now)
            all_day(main, r["main_start"], r.get("main_end"))
            desc = base_desc
            if r.get("has_precon") and not r.get("precon_date"):
                desc = "Includes a pre-con (date TBD \u2014 see event page).\n" + desc
            main.add("description", desc)
            if venue:
                main.add("location", venue)
            if url:
                main.add("url", url)
            main.add("categories", ["Conference"] + loc_cats)
            cal.add_component(main)

    return cal.to_ical()


# ----------------------------------------------------------------------------- HTML
def build_html(rows: list[dict]) -> str:
    env = Environment(autoescape=True)
    template = env.from_string(INDEX_TEMPLATE)

    now = datetime.now(timezone.utc)
    today = now.date()
    view = []
    for r in rows:
        cfs = r.get("cfs_close")            # timezone-aware UTC datetime, or None
        modality = r.get("modality", "in_person")
        _end = r.get("main_end") or r.get("main_start")   # last day the event occupies
        view.append({
            "name": r["name"],
            "url": r.get("url") or "",
            "venue": r.get("venue") or "",
            "continents": r.get("continents") or [],
            "modality": modality,
            "modality_label": MODALITY_LABELS.get(modality, ""),
            "is_online": modality in ("online", "hybrid"),
            "is_in_person": modality in ("in_person", "hybrid"),
            "is_hybrid": modality == "hybrid",
            "is_precon": bool(r.get("has_precon")),
            "cfs_iso": cfs.isoformat() if cfs else "",
            "cfs_display": fmt_day(cfs),
            "cfs_open": bool(cfs and cfs >= now),
            "conf_display": fmt_range(r.get("main_start"), r.get("main_end")),
            "conf_iso": r["main_start"].isoformat() if r.get("main_start") else "",
            "main_end_iso": r["main_end"].isoformat() if r.get("main_end") else "",
            "precon_iso": r["precon_date"].isoformat() if r.get("precon_date") else "",
            "precon_display": fmt_day(r.get("precon_date")),
            "precon_known": bool(r.get("precon_date")),
            "confidence": r.get("confidence", ""),
            "info": (r.get("info") or "").strip(),
            "is_past": bool(_end and _end < today),
        })

    upcoming = [r for r in view if not r["is_past"]]
    present_continents = [c for c in CONTINENTS if any(c in r["continents"] for r in view)]
    open_count = sum(1 for r in upcoming if r["cfs_open"])

    return template.render(
        rows=view,
        continents=present_continents,
        total=len(upcoming),
        open_count=open_count,
        calendar_url=f"{SITE_URL}/calendar.ics" if SITE_URL else "",
        generated_at=datetime.now(timezone.utc).strftime("%d %b %Y, %H:%M UTC"),
    )


# ----------------------------------------------------------------------------- main
def main() -> None:
    print(f"Fetching {API_URL} ...")
    events = fetch_events()
    confs = [e for e in events if is_conference(e)]
    print(f"  {len(events)} events -> {len(confs)} conferences/precons kept")

    cache = pp.load_cache(CACHE_PATH)
    try:
        with open(OVERRIDES_PATH, "r", encoding="utf-8") as fh:
            overrides = json.load(fh)
    except (FileNotFoundError, json.JSONDecodeError):
        overrides = {}

    client = pp.make_client(GEMINI_API_KEY)
    if client:
        to_parse = sum(1 for e in confs if pp.needs_parsing(e) and pp.cache_key(e) not in cache)
        est = (to_parse + GEMINI_RPM - 1) // max(GEMINI_RPM, 1)
        print(f"  Gemini: enabled ({MODEL}) \u2014 {to_parse} new to parse at \u2264{GEMINI_RPM}/min (~{est} min)")
    else:
        print("  Gemini: disabled (no key) \u2014 precon dates skipped")

    rows = []
    try:
        for e in confs:
            before = len(cache)
            info = pp.get_precon_info(e, client, MODEL, cache, rpm=GEMINI_RPM)
            if len(cache) > before:                 # a new event was parsed -> persist progress now
                pp.save_cache(CACHE_PATH, cache)
            sched = apply_override(e.get("EventName", ""), resolve_schedule(e, info), overrides)
            rows.append({
                "name": e.get("EventName", "Untitled"),
                "venue": e.get("Venue"),
                "url": e.get("URL"),
                "info": e.get("Information"),
                "regions": [x.strip() for x in (e.get("Regions") or "").split(",") if x.strip()],
                "cfs_close": to_datetime(e.get("Cfs_Closes")),
                **classify_location(e),
                **sched,
            })
    finally:
        pp.save_cache(CACHE_PATH, cache)             # save even if interrupted

    # Sort: soonest UPCOMING CfS deadline first; expired/none afterwards (by conf date).
    now = datetime.now(timezone.utc)
    far = date(2999, 1, 1)

    def sort_key(r):
        cfs = r.get("cfs_close")
        if cfs and cfs >= now:
            return (0, 0, cfs.date())
        return (1, 0, r.get("main_start") or far)

    rows.sort(key=sort_key)

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    with open(os.path.join(OUTPUT_DIR, "calendar.ics"), "wb") as fh:
        fh.write(build_ics(rows))
    with open(os.path.join(OUTPUT_DIR, "index.html"), "w", encoding="utf-8") as fh:
        fh.write(build_html(rows))
    # Stop GitHub Pages from running the files through Jekyll.
    open(os.path.join(OUTPUT_DIR, ".nojekyll"), "w").close()

    print(f"  Precon dates cached for {sum(1 for r in rows if r.get('precon_date'))} event(s).")
    print(f"Wrote {OUTPUT_DIR}/calendar.ics and {OUTPUT_DIR}/index.html ({len(rows)} events)")


if __name__ == "__main__":
    main()