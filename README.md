# 📅 Chalmers Calendar Sync

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

One Google Calendar that always matches your real schedule -- no more
checking Canvas and TimeEdit separately, or re-subscribing every term when
Google Calendar's own ICS import goes stale.

## 🛠️ Setup

1. **Canvas**: on the Canvas Calendar page, open the sidebar's "Calendar
   feed" link (bottom right, under the calendar list) and copy its ICS URL.

   ![Canvas calendar feed link](docs/canvas-calendar-feed.png)

2. **TimeEdit**: click **Prenumerera** ("Subscribe") and copy the ICS link
   from there -- not the one-off download button, since it needs to be
   fetchable with a plain HTTP GET.

   ![TimeEdit subscribe dialog](docs/timeedit-subscribe.png)

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

## ▶️ Running

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

## 🤖 Automation

`.github/workflows/sync.yml` runs the sync every 4 hours via GitHub
Actions. In the repo, go to **Settings -> Secrets and variables ->
Actions** and add these repo secrets:

- `CANVAS_ICS_URL` -- the Canvas ICS URL from step 1
- `TIMEEDIT_ICS_URL` -- the TimeEdit ICS URL from step 2
- `GOOGLE_CALENDAR_ID` -- the same value you put in `.env`
- `GOOGLE_TOKEN_JSON` -- the full contents of the `token.json` that
  `src/auth_setup.py` produced locally


The refresh token in `token.json` doesn't expire from scheduled use, only
from long inactivity (~6 months) or if you revoke it yourself
(myaccount.google.com/permissions). If that happens, just re-run
`src/auth_setup.py` locally and update the secret.

