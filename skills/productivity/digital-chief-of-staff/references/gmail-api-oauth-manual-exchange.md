# Gmail API OAuth — Manual Code Exchange

When automated browser OAuth flows trigger Google's bot detection, fall back to this manual exchange pattern. The user authorizes in their own browser and pastes back the redirect URL.

## Critical Setup: Understand the Traps

This flow has three gotchas that produce cryptic Google errors if missed:

1. **`flow.redirect_uri` MUST be set explicitly.** `InstalledAppFlow.from_client_secrets_file()` does NOT read `redirect_uris` from the credentials JSON. Without `flow.redirect_uri = 'http://localhost'`, the auth URL has no `redirect_uri` parameter and Google returns `"Error 400: blocked authorization error missing redirect_uri"`.

2. **PKCE code_verifier must be preserved in the same session.** The URL generation and code exchange MUST happen in the same Python process. If you split them across two separate Python invocations, the second process generates a new code_verifier that doesn't match the code_challenge in the URL, producing `(invalid_grant) Missing code verifier`. Use a single long-lived script (via PTY+background mode) rather than a one-shot URL generator.

3. **`OAUTHLIB_INSECURE_TRANSPORT=1` is required.** The credentials' redirect URI is `http://localhost` (not HTTPS). The oauthlib library rejects this as insecure unless the environment variable is set.

## Full exchange script (recommended — single process, fixes all three traps)

Save as `~/.local/bin/gmail-auth-manual` and run it with `~/{email_venv}/bin/python`:

```python
#!/usr/bin/env python3
"""Gmail API OAuth flow — manual code exchange, single session."""
import os
from pathlib import Path
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ['https://www.googleapis.com/auth/gmail.modify']
CONFIG_DIR = Path.home() / '.config' / 'gmail-api'
CREDENTIALS = CONFIG_DIR / 'credentials.json'
TOKEN = CONFIG_DIR / 'token.json'

os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'   # ← Trap 3: allow http://localhost

def main():
    if TOKEN.exists():
        print(f"Token already exists at {TOKEN}")
        return

    flow = InstalledAppFlow.from_client_secrets_file(str(CREDENTIALS), SCOPES)
    flow.redirect_uri = 'http://localhost'          # ← Trap 1: required, not inherited

    auth_url, _ = flow.authorization_url(
        access_type='offline',
        prompt='consent',
        include_granted_scopes='true'
    )                                               # ← Trap 2: same flow used for exchange below

    print("=" * 70)
    print("OPEN THIS URL IN YOUR BROWSER:")
    print("=" * 70)
    print(auth_url)
    print("=" * 70)
    print()
    print("After authorizing, you'll be redirected to a page that says")
    print("\"This site can't be reached\" or shows an error — that's expected.")
    print("Copy the ENTIRE URL from the address bar and paste it below.")
    print()

    redirect_response = input("Paste the redirect URL here: ").strip()

    flow.fetch_token(authorization_response=redirect_response)
    creds = flow.credentials

    TOKEN.write_text(creds.to_json())
    print(f"\nToken saved to {TOKEN}")
    print("Gmail API is ready.")

if __name__ == '__main__':
    main()
```

### How to run (PTY + background)

Since the script calls `input()` (waiting for the user to paste the redirect URL), it must run in PTY+background mode:

```bash
# Start the script
terminal(command='~/{email_venv}/bin/python ~/.local/bin/gmail-auth-manual', background=True, pty=True)

# Wait a few seconds, then poll to get the auth URL
process(action='poll', session_id='<id>')

# Write the generated URL to a file for the user
process(action='submit', session_id='<id>', data='<full-redirect-url>')

# Poll again to confirm token was saved
```

## Fallback: Auth URL generator only (if you're using a different exchange path)

Use only when you cannot run the full exchange script. WARNING: this creates a new flow with a new code_verifier — if you exchange the resulting code against a different Python process, you'll hit Trap 2 (Missing code verifier). For a reliable flow, ALWAYS use the full exchange script above.

```bash
~/{email_venv}/bin/python3 -c "
from pathlib import Path
from google_auth_oauthlib.flow import InstalledAppFlow

flow = InstalledAppFlow.from_client_secrets_file(
    str(Path.home() / '.config' / 'gmail-api' / 'credentials.json'),
    ['https://www.googleapis.com/auth/gmail.modify']
)
flow.redirect_uri = 'http://localhost'    # ← CRITICAL: missing by default
auth_url, _ = flow.authorization_url(
    access_type='offline',
    prompt='consent',
    include_granted_scopes='true'
)
print(auth_url)
"
```

## User instructions to paste back

Give the user these exact instructions:

1. Click the link above to open Google's sign-in/consent screen.
2. Sign in as the Gmail account.
3. Click **Continue** → **Allow** on the app consent screen.
4. You'll be redirected to a URL starting with `http://localhost/?code=...` — that page will fail to load (no server listening there; this is expected and harmless).
5. **Copy the entire URL** from your browser's address bar (the one starting with `http://localhost/?code=...`).
6. Paste it back and the tokens will be saved automatically.

When the user pastes the URL on a platform that doesn't support inline input (e.g. Hermes CLI TUI), use the PTY+background approach above with `process(action='submit')` to feed it.

## What gets saved

`~/.config/gmail-api/token.json` — contains `access_token`, `refresh_token`, `scope`, `token_uri`, `client_id`, `client_secret`, and `expiry`. The refresh token enables persistent access with auto-renewal; no user action needed again unless the token is revoked or the refresh token expires (Google limits refresh token lifetime for some app types; if auth fails months later, re-run this flow).