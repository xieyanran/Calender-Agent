"""One-time local login: opens a browser for you to sign in to the Google
account that owns the target calendar, then writes token.json (an OAuth
refresh token, not a service-account key, since Chalmers' org blocks
creating those). Re-run this if token.json is deleted or the refresh token
gets revoked; ordinary runs never need this.

Usage:
    python -m src.auth_setup [--client-secret client_secret.json] [--token token.json]
"""

from __future__ import annotations

import argparse

from google_auth_oauthlib.flow import InstalledAppFlow

from src.calendar_sync import SCOPES


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--client-secret", default="client_secret.json")
    parser.add_argument("--token", default="token.json")
    args = parser.parse_args()

    flow = InstalledAppFlow.from_client_secrets_file(args.client_secret, SCOPES)
    credentials = flow.run_local_server(port=0)

    with open(args.token, "w", encoding="utf-8") as f:
        f.write(credentials.to_json())

    print(f"Wrote {args.token}. For GitHub Actions, put its full contents in the")
    print("GOOGLE_TOKEN_JSON repo secret.")


if __name__ == "__main__":
    main()
