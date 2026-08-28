# Calender-Agent

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

If you're at Chalmers, your term is scattered across three systems: Canvas
(assignment deadlines), TimeEdit (the actual class schedule, in Swedish,
full of fields you don't need), and Ladok (course/exam/re-exam
registration). This pulls the first two into a single Google Calendar on a
schedule, translating and trimming TimeEdit's noisy Swedish entries along
the way. Ladok isn't wired up yet -- see `src/sources/ladok.py` for why.

Deliberately not an LLM agent: it's a plain fetch -> normalize -> upsert
sync script, run on a schedule. Deterministic and easy to debug.

Built against and tested on Chalmers' actual Canvas/TimeEdit feeds -- other
schools' TimeEdit instances format fields differently (`src/sources/timeedit.py`'s
`_parse_summary`/`_parse_location` will likely need adjusting), so treat
this as a working reference rather than something that'll run unmodified
elsewhere.

## How it works

- `src/sources/canvas.py` / `src/sources/timeedit.py` fetch each source's
  ICS feed and turn it into a list of `Event`s (`src/normalize.py`).
- `src/calendar_sync.py` upserts those events into a Google Calendar. Every
  event it writes carries a stable `sourceUid` in `extendedProperties`, so
  re-running the sync updates/deletes instead of duplicating.
- `src/main.py` wires it together and is what actually runs.

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

## Ladok

Not implemented. `ladok3` (the only real open-source Python wrapper) turns
out to be built for staff reporting grades, not for a student reading their
own registration/exam-registration deadlines -- see the docstring in
`src/sources/ladok.py` for what was checked and what to try next.

## License

[MIT](LICENSE)
