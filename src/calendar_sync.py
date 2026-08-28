from __future__ import annotations

import logging
from datetime import date, datetime
from typing import Iterable

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

from src.normalize import Event

logger = logging.getLogger(__name__)

# Chalmers' Google Workspace org blocks service-account key creation
# (iam.disableServiceAccountKeyCreation), so this authenticates as the user
# directly via OAuth instead -- see src/auth_setup.py for the one-time login
# that produces token.json. Bonus: since it's the user's own calendar under
# their own account, there's no separate "share the calendar" step needed.
SCOPES = ["https://www.googleapis.com/auth/calendar"]
MANAGED_BY_KEY = "managedBy"
MANAGED_BY_VALUE = "calender-agent"
SOURCE_UID_KEY = "sourceUid"


def get_service(token_file: str):
    try:
        credentials = Credentials.from_authorized_user_file(token_file, SCOPES)
    except FileNotFoundError:
        raise SystemExit(
            f"{token_file} not found. Run `python -m src.auth_setup` once locally "
            "to log in and create it (see README)."
        )
    if credentials.expired and credentials.refresh_token:
        credentials.refresh(Request())
    return build("calendar", "v3", credentials=credentials, cache_discovery=False)


def _to_google_event(event: Event, reminders_minutes: list[int]) -> dict:
    if event.all_day:
        start_body = {"date": event.start.date().isoformat()}
        end_body = {"date": event.end.date().isoformat()}
    else:
        start_body = {"dateTime": event.start.isoformat()}
        end_body = {"dateTime": event.end.isoformat()}

    body = {
        "summary": event.title,
        "location": event.location,
        "description": event.description,
        "start": start_body,
        "end": end_body,
        "extendedProperties": {
            "private": {
                MANAGED_BY_KEY: MANAGED_BY_VALUE,
                SOURCE_UID_KEY: event.uid,
            }
        },
        "reminders": {
            "useDefault": False,
            "overrides": [{"method": "popup", "minutes": m} for m in reminders_minutes],
        },
    }
    return body


def _list_managed_events(service, calendar_id: str) -> dict[str, dict]:
    """Return {source_uid: google_event} for every event this tool manages."""
    existing: dict[str, dict] = {}
    page_token = None
    while True:
        response = (
            service.events()
            .list(
                calendarId=calendar_id,
                privateExtendedProperty=f"{MANAGED_BY_KEY}={MANAGED_BY_VALUE}",
                pageToken=page_token,
                showDeleted=False,
                maxResults=2500,
            )
            .execute()
        )
        for item in response.get("items", []):
            source_uid = (
                item.get("extendedProperties", {}).get("private", {}).get(SOURCE_UID_KEY)
            )
            if source_uid:
                existing[source_uid] = item
        page_token = response.get("nextPageToken")
        if not page_token:
            break
    return existing


def _parsed_time(time_body: dict) -> datetime | date | None:
    """A Google Calendar start/end object has either `dateTime` (timed) or
    `date` (all-day) -- never both. Parse rather than compare raw strings:
    Google may echo a `dateTime` back with a different (but equal) UTC
    offset than what we sent -- e.g. the calendar's own timezone offset
    instead of "+00:00" -- which would otherwise look like a change on
    every single run forever."""
    if "dateTime" in time_body:
        return datetime.fromisoformat(time_body["dateTime"].replace("Z", "+00:00"))
    if "date" in time_body:
        return date.fromisoformat(time_body["date"])
    return None


def _needs_update(google_event: dict, new_body: dict) -> bool:
    for field_name in ("summary", "location", "description"):
        if google_event.get(field_name, "") != new_body.get(field_name, ""):
            return True
    if _parsed_time(google_event.get("start", {})) != _parsed_time(new_body["start"]):
        return True
    if _parsed_time(google_event.get("end", {})) != _parsed_time(new_body["end"]):
        return True
    return False


def sync_events(
    service,
    calendar_id: str,
    events: Iterable[Event],
    reminders_by_category: dict[str, list[int]],
    dry_run: bool = False,
) -> dict[str, int]:
    """Idempotent upsert: insert new events, update changed ones, delete ones
    that disappeared from the source. Google Calendar is the only state we
    keep — matched via the sourceUid stashed in extendedProperties.private,
    so re-running this never creates duplicates."""
    events = list(events)
    existing = _list_managed_events(service, calendar_id)
    seen_uids: set[str] = set()
    stats = {"created": 0, "updated": 0, "deleted": 0, "unchanged": 0}

    for event in events:
        seen_uids.add(event.uid)
        reminders = reminders_by_category.get(event.category, [])
        body = _to_google_event(event, reminders)

        if event.uid in existing:
            google_event = existing[event.uid]
            if _needs_update(google_event, body):
                if not dry_run:
                    service.events().patch(
                        calendarId=calendar_id, eventId=google_event["id"], body=body
                    ).execute()
                stats["updated"] += 1
                logger.info("Updated: %s", event.title)
            else:
                stats["unchanged"] += 1
        else:
            if not dry_run:
                service.events().insert(calendarId=calendar_id, body=body).execute()
            stats["created"] += 1
            logger.info("Created: %s", event.title)

    for source_uid, google_event in existing.items():
        if source_uid not in seen_uids:
            if not dry_run:
                service.events().delete(
                    calendarId=calendar_id, eventId=google_event["id"]
                ).execute()
            stats["deleted"] += 1
            logger.info("Deleted: %s", google_event.get("summary"))

    return stats
