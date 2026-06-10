"""
precon_parser.py
----------------
Extracts pre-conference ("precon") scheduling info from the free-text fields of
Call for Data Speakers events, using Google's Gemini API (free tier).

The upstream feed only flags THAT an event has a precon (via the EventType tag,
e.g. "Conference, Precon"); the actual precon *date* usually lives only in the
free-text `Information` field ("24.09 pre-con workshops, 25.09 sessions") or has
to be inferred from the Date..EndDate span. This module turns that mess into
structured fields.

Design notes:
- We only call Gemini for events that look like they have a precon (tag or
  keyword), so the vast majority of events cost nothing.
- Results are cached on disk keyed by a hash of the source fields, so we only
  ever pay for *new or changed* events. With caching this stays comfortably
  inside Gemini's free tier.
- If no API key is configured, parsing degrades gracefully: we still report
  has_precon from the tag, just without a specific date.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import re
import time
from typing import Optional, Literal

from pydantic import BaseModel, Field

# google-genai is only needed when an API key is present. Import lazily so the
# pipeline can run (degraded) without the package/key installed.
try:
    from google import genai
    _GENAI_AVAILABLE = True
except Exception:  # pragma: no cover
    genai = None
    _GENAI_AVAILABLE = False


PRECON_KEYWORDS = (
    "precon", "pre-con", "pre con", "pre-conference", "preconference",
    "pre-day", "pre day", "workshop", "training", "full day", "full-day",
    "tutorial", "masterclass", "master class", "deep dive", "deep-dive",
    "bootcamp", "boot camp", "hands-on", "hands on", "learning day",
)


class PreconInfo(BaseModel):
    """Schema Gemini must fill in. Dates are 'YYYY-MM-DD' strings or null."""
    has_precon: bool = Field(description="True if this event has a separate pre-conference / workshop / training day.")
    precon_date: Optional[str] = Field(default=None, description="Date of the precon as YYYY-MM-DD, or null if not determinable. Must fall within the event's overall span.")
    main_start: Optional[str] = Field(default=None, description="First day of the MAIN sessions as YYYY-MM-DD, or null.")
    main_end: Optional[str] = Field(default=None, description="Last day of the MAIN sessions as YYYY-MM-DD, or null.")
    confidence: Literal["high", "medium", "low"] = Field(description="high = explicitly stated in the text; medium = inferred from the date span; low = guess / unclear.")
    note: str = Field(default="", description="One short sentence explaining the reasoning. Empty if nothing to add.")


SYSTEM_INSTRUCTION = (
    "You extract pre-conference (precon) scheduling information for a data-platform "
    "conference calendar. A 'precon' is a separate paid day held before the main "
    "sessions, and goes by many names: pre-conference, pre-day, workshop / workshop "
    "day, training / training day / full-day training, tutorial, masterclass, deep-dive, "
    "bootcamp, or hands-on day. Treat any of these as a precon. "
    "Use ONLY the fields provided. Never invent dates. "
    "The event spans 'date' to 'end_date' (inclusive); these may include BOTH precon "
    "and main-session days. If the text explicitly states which day is the precon / "
    "workshop / training day, use it (confidence 'high'). If only the type tag says "
    "there is a precon but no specific day is given, you MAY infer that the precon is "
    "the first day of the span and the main sessions are the remaining day(s), but mark "
    "this 'medium' (or 'low' if the span is long/ambiguous) and explain in the note. "
    "If nothing in the tag or text indicates a separate precon/workshop/training day, "
    "set has_precon=false and leave precon_date null \u2014 do NOT invent a precon for an "
    "ordinary multi-day conference. "
    "Any date you return MUST fall within [date, end_date]. Return null for a date you "
    "cannot justify. Output strictly matches the provided schema."
)


def needs_parsing(event: dict) -> bool:
    """Cheap pre-filter: only bother calling the model when a precon is plausible."""
    etype = (event.get("EventType") or "").lower()
    if "precon" in etype:
        return True
    info = (event.get("Information") or "").lower()
    return any(k in info for k in PRECON_KEYWORDS)


def cache_key(event: dict) -> str:
    """Stable key over the fields that affect the extraction."""
    basis = "|".join(str(event.get(k) or "") for k in ("EventName", "EventType", "Date", "EndDate", "Information"))
    return hashlib.sha256(basis.encode("utf-8")).hexdigest()[:16]


def load_cache(path: str) -> dict:
    try:
        with open(path, "r", encoding="utf-8") as fh:
            return json.load(fh)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def save_cache(path: str, cache: dict) -> None:
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(cache, fh, indent=2, sort_keys=True, ensure_ascii=False)


def make_client(api_key: Optional[str]):
    """Return a Gemini client, or None if unavailable (pipeline then degrades)."""
    if not api_key or not _GENAI_AVAILABLE:
        return None
    return genai.Client(api_key=api_key)


def _call_gemini(client, model: str, event: dict) -> Optional[dict]:
    payload = {
        "name": event.get("EventName"),
        "type": event.get("EventType"),
        "date": (event.get("Date") or "")[:10],
        "end_date": (event.get("EndDate") or "")[:10] or None,
        "information": event.get("Information") or "",
    }
    prompt = (
        "Extract the precon scheduling for this event:\n"
        + json.dumps(payload, ensure_ascii=False)
    )
    resp = client.models.generate_content(
        model=model,
        contents=prompt,
        config={
            "system_instruction": SYSTEM_INSTRUCTION,
            "response_mime_type": "application/json",
            "response_schema": PreconInfo,
            "temperature": 0.0,
        },
    )
    parsed = getattr(resp, "parsed", None)
    if isinstance(parsed, PreconInfo):
        return parsed.model_dump()
    # Fallback: parse the raw text if .parsed is unavailable for any reason.
    try:
        return PreconInfo(**json.loads(resp.text)).model_dump()
    except Exception:
        return None


# --- rate limiting + backoff -------------------------------------------------
# Free-tier Gemini caps requests-per-minute per model (e.g. gemini-2.5-flash = 5/min).
# We self-throttle to stay under it, and also retry on 429 in case we drift over.
_CALL_TIMES: list[float] = []
_RETRY_RE = re.compile(r"retry in ([0-9.]+)s", re.IGNORECASE)


def _respect_rpm(rpm: int) -> None:
    """Block until issuing a request now keeps us within `rpm` over a rolling 60s."""
    if rpm <= 0:
        return
    now = time.monotonic()
    while _CALL_TIMES and _CALL_TIMES[0] < now - 60.0:
        _CALL_TIMES.pop(0)
    if len(_CALL_TIMES) >= rpm:
        wait = 60.0 - (now - _CALL_TIMES[0]) + 0.5
        if wait > 0:
            time.sleep(wait)


def _is_rate_limit(exc: Exception) -> bool:
    s = str(exc)
    return "429" in s or "RESOURCE_EXHAUSTED" in s


def _retry_delay(exc: Exception, default: float) -> float:
    m = _RETRY_RE.search(str(exc))
    if m:
        try:
            return float(m.group(1)) + 1.0
        except ValueError:
            pass
    return default


def _call_with_retry(client, model: str, event: dict, rpm: int, max_retries: int) -> Optional[dict]:
    """Call Gemini, self-throttling and retrying on 429. Re-raises other errors."""
    default_delay = math.ceil(60 / max(rpm, 1)) + 2
    for attempt in range(max_retries + 1):
        _respect_rpm(rpm)
        _CALL_TIMES.append(time.monotonic())
        try:
            return _call_gemini(client, model, event)
        except Exception as exc:
            if _is_rate_limit(exc) and attempt < max_retries:
                delay = _retry_delay(exc, default_delay)
                print(f"  \u00b7 rate-limited, waiting {delay:.0f}s (attempt {attempt + 1}/{max_retries})")
                time.sleep(delay)
                continue
            raise


def get_precon_info(event: dict, client, model: str, cache: dict, rpm: int = 5, max_retries: int = 4) -> dict:
    """
    Cache-aware extraction for a single event. Mutates `cache` in place.
    Returns a dict matching PreconInfo (always returns something usable).
    """
    tag_says_precon = "precon" in (event.get("EventType") or "").lower()

    if not needs_parsing(event):
        return PreconInfo(has_precon=False, confidence="high", note="No precon tag or keyword.").model_dump()

    key = cache_key(event)
    if key in cache:
        return cache[key]

    # No client (no key / package): report has_precon from the tag, no date.
    if client is None:
        return PreconInfo(
            has_precon=tag_says_precon,
            confidence="low",
            note="No Gemini key configured; precon date not extracted.",
        ).model_dump()

    try:
        result = _call_with_retry(client, model, event, rpm=rpm, max_retries=max_retries)
    except Exception as exc:  # non-rate-limit error -> don't cache, retry next run
        print(f"  ! Gemini error for {event.get('EventName')!r}: {exc}")
        result = None

    if result is None:
        return PreconInfo(
            has_precon=tag_says_precon,
            confidence="low",
            note="Extraction failed this run; will retry next time.",
        ).model_dump()

    cache[key] = result  # only successful results are cached
    return result
