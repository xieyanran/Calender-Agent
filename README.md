# Chalmers Calendar Sync

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

One Google Calendar that always matches your real schedule -- no more
checking Canvas and TimeEdit separately, or re-subscribing every term when
Google Calendar's own ICS import goes stale.

This pulls Canvas assignment deadlines and TimeEdit's class schedule
(translated out of Swedish, stripped of noise) into a single calendar, and
updates it incrementally on every run instead of wiping and re-importing
from scratch.

## Setup

1. **Canvas**: on the Canvas Calendar page, find the "Calendar Feed" link
   (bottom of the page) and copy its ICS URL.
2. **TimeEdit**: find the "Subscribe"/"Prenumerera" ICS link (not the
   one-off download button) -- it needs to be fetchable with a plain HTTP
   GET.
3. **Google Calendar**:
   - Create a dedicated calendar for this (Settings -> "Create new
     calendar"), so it's safe to wipe/resync without touching your main
     calendar. Put its ID (Settings -> that calendar -> "Calendar ID")
     in `.env` as `GOOGLE_CALENDAR_ID` -- not in `config.yaml`, since
     that's tracked in git and this value is personal.
   - In a Google Cloud project, enable the **Google Calendar API**.
   - This authenticates as *you*, via OAuth, rather than a service account
     -- Google now disables service-account key downloads by default on
     every new project (not specific to this project or Chalmers), so
     that path is a dead end. OAuth is actually simpler here anyway: since
     it's your own calendar under your own account, there's no separate
     "share the calendar with a service account" step.
     - APIs & Services -> OAuth consent screen: set it up as **External**,
       fill in the required fields, and add your own Google account under
       **Test users**.
     - APIs & Services -> Credentials -> Create Credentials -> **OAuth
       client ID** -> Application type **Desktop app**. Download the JSON
       and save it as `client_secret.json` in the repo root.
     - Run `python -m src.auth_setup` locally. It opens a browser to log
       in with the account that owns the calendar; since the app is
       unverified you'll need to click through "Advanced -> Go to
       (app name)". This writes `token.json`, which `src/main.py` reads by
       default.
4. Copy `.env.example` to `.env` and fill in the URLs above, or export the
   same variables in your shell.
5. `pip install -r requirements.txt`

## Running

```bash
# Fetch + normalize + print, writes nothing:
python -m src.main --dry-run

# Actually sync to Google Calendar:
python -m src.main
```

Check the dry run output carefully before doing a real sync -- especially
new courses each term, since `_parse_summary` in `src/sources/timeedit.py`
was written against Chalmers' actual TimeEdit field layout but course
names still need adding to `config.yaml`'s `timeedit.translations` as they
show up (there's no general Swedish translator, just a fixed dictionary).

## Automation

`.github/workflows/sync.yml` runs the sync every 4 hours via GitHub
Actions. Add these as repo secrets (Settings -> Secrets and variables ->
Actions): `CANVAS_ICS_URL`, `TIMEEDIT_ICS_URL`, `GOOGLE_CALENDAR_ID`, and
`GOOGLE_TOKEN_JSON` (the full contents of the `token.json` that
`src/auth_setup.py` produced locally). Repo secrets aren't readable by
anyone even on a public repo, but the ICS URLs and token effectively act as
bearer credentials to your school accounts and calendar -- don't paste them
anywhere else. The refresh token in `token.json` doesn't expire from
scheduled use, only from long inactivity (~6 months) or if you revoke it
yourself (myaccount.google.com/permissions) -- if that happens, just re-run
`src/auth_setup.py` locally and update the secret.

