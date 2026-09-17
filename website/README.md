# MHM Website


> **File**: `website/README.md`
Marketing site, password and social login/create-account page, signed-in account
settings, task workspace, notebook, personal message library, and private insights.
The Python gateway uses the **same account store as MHM**. It never stores browser
passwords in plaintext or creates a separate website database. Passwords are
stored as salted scrypt hashes in the canonical account document.

## Local preview

From the project root, with `.venv` activated:

```powershell
python run_headless_service.py start
```

Open `http://localhost:8080`. The existing `EMAIL_SMTP_SERVER`,
`EMAIL_SMTP_USERNAME`, and `EMAIL_SMTP_PASSWORD` settings must be configured to
deliver codes. No test code or fake sign-in bypass is exposed in the UI.
This starts bots, scheduler, and gateway together as a background service without
the admin UI. The terminal can close after startup;
use `python run_headless_service.py stop` or `status` to manage it.
Stop any previously running standalone gateway before starting MHM. The gateway
also starts with the admin panel's Start Service action and belongs to that service,
so closing the admin window does not stop a headless gateway. Restarting the service
signs browsers out but preserves saved settings.

To run only the website without bots or scheduler, use `python run_headless_service.py
web` and keep that foreground process running. Set `WEB_GATEWAY_ENABLED=false`
when starting the MHM service alongside a standalone gateway.
`WEB_GATEWAY_HOST` and `WEB_GATEWAY_PORT` default to
`127.0.0.1` and `8080`; headless `--host` and `--port` override these. If the browser
origin changes, update `WEB_PUBLIC_ORIGIN` to match.

Existing users can continue signing in with an emailed code, then set a password
from the account page. Replacing a saved password requires either the current
password or a fresh emailed-code sign-in and revokes the account's other in-memory
browser sessions. Each email must belong to only
one account. Duplicate emails prevent browser sign-in until an administrator
corrects the user data. Accounts without an email require an administrator to
add one before browser sign-in.
Suspended and inactive accounts cannot sign in. Delivery failures and skipped
ambiguous logins are recorded in the main log without codes or email addresses.

New accounts choose a password and are created **after email verification**, through `create_new_user`.
They start with messaging, tasks, and check-ins disabled and no categories.
Users can configure these on their signed-in settings page. Account creation completes without
requiring a communication channel connection. Email is available immediately, Discord can be
connected optionally from the account page, and SMS can be added as another channel later.
The gateway exchanges the one-time
authorization code server-side, verifies the Discord identity, and stores only the Discord ID
and username in the existing MHM account. A Discord account already linked to another MHM
account is rejected. The bot's existing “Link account” flow remains available as a fallback.
Settings cover preferred name, birth date, identity and health-context lists,
time zone and linked delivery channel, natural-language phrase times, message
categories and reminder windows, task recurrence defaults, and check-in windows,
question selection, and counts. Each section saves to the same profile documents
used by the admin console, preserving other fields. Invalid input is rejected,
and edits made elsewhere require reloading the affected section.

Users can disconnect Discord or optional social sign-ins (while retaining at
least one sign-in method) and download a secret-scrubbed JSON data export,
including tasks and notebook entries. Email,
internal account identifiers, suspension, and other administrator controls still
cannot be changed here.

Tasks can be created from built-in templates, edited, linked to web resources,
completed, restored, deleted, snoozed, skipped, or simplified. The notebook adds
pinned and inbox views alongside active and archived entries. The message library
supports personal template creation, editing, scheduling, pausing, and deletion.
Insights show recent check-in patterns and history. Google Health can be viewed,
paused, enabled, synced, or deleted there; initial connection still uses the
existing callback configured by `GOOGLE_HEALTH_REDIRECT_URI` (the default local
callback works only when the browser can reach the MHM host). Completing check-ins
still uses the existing app interface, as intentionally excluded from this work.

## Cloudflare Workers deployment

Build command: leave blank (static HTML/CSS/JS)
Deploy command: `npx wrangler deploy`

Run the deploy command from `website/`. The Worker serves static assets and proxies
only supported `/api/` routes. The static site alone cannot access local Python data.
Gateway fetches use `redirect: 'manual'`, since the Workers runtime rejects
`redirect: 'error'`. Unexpected API redirects are rejected without following them;
Discord and social callback redirects are returned to the browser.

To enable live accounts:

1. Run one Python gateway on the MHM host, using the same `.env` and data directory
   as the app. Make it reachable at an HTTPS origin through your reverse proxy or
   tunnel. Keep the gateway on loopback when the proxy runs on the same machine.
2. Set `WEB_PUBLIC_ORIGIN` in MHM's `.env` to the website's exact HTTPS origin
   (no path). Set `WEB_PROXY_SECRET` to at least 32 random characters.
3. Set the Worker's `MHM_API_ORIGIN` variable to the gateway's HTTPS origin in
   `wrangler.jsonc` (currently `https://mhm-gateway.jacfogel.com`). `keep_vars=true`
   also preserves additional dashboard text variables when deploying. These are
   runtime settings under **Settings > Variables and Secrets**, not Build variables.
   Set its `MHM_API_SECRET` secret to match `WEB_PROXY_SECRET` using
   `npx wrangler secret put MHM_API_SECRET`. Never put it in client JavaScript.
4. Deploy the Worker, then test creation and login with a controlled email.

Keep `global_fetch_strictly_public` enabled in `wrangler.jsonc`. The website and
gateway share the `jacfogel.com` zone; this flag makes gateway requests use the
public Cloudflare path, matching requests that successfully reach the tunnel
from a browser. See [Cloudflare's fetch routing documentation](https://developers.cloudflare.com/workers/configuration/compatibility-flags/#global-fetch-strictly-public).
After changing Wrangler configuration, commit and push to trigger the connected
Cloudflare build, or deploy from `website/` with an authenticated Wrangler CLI.

For social sign-in, configure any of the following credential groups on the gateway.
Buttons remain disabled until both the client ID and secret are present. A verified
provider email is linked only when it uniquely matches an active MHM account; after
that, the stable provider subject is used and OAuth access/refresh tokens are not stored.

- Google: `GOOGLE_OAUTH_CLIENT_ID`, `GOOGLE_OAUTH_CLIENT_SECRET`, and optionally
  `GOOGLE_OAUTH_REDIRECT_URI`.
- Facebook: `FACEBOOK_OAUTH_CLIENT_ID`, `FACEBOOK_OAUTH_CLIENT_SECRET`, and optionally
  `FACEBOOK_OAUTH_REDIRECT_URI`. Connect Facebook once from the signed-in account
  page before using it from the login page; the Graph email field is not treated
  as an independently verified email claim.
- Apple: `APPLE_OAUTH_CLIENT_ID` (Services ID), `APPLE_OAUTH_CLIENT_SECRET` (the signed
  client-secret JWT), and `APPLE_OAUTH_REDIRECT_URI`. Apple requires a registered HTTPS
  domain callback and posts its authorization response to the callback.

When a redirect setting is blank it defaults to
`${WEB_PUBLIC_ORIGIN}/api/auth/oauth/<provider>/callback`. Register the exact callback
with the provider. Apple's signed client-secret JWT expires and must be rotated.

For Discord connection, create an OAuth2 redirect in the Discord Developer Portal that exactly
matches `DISCORD_OAUTH_REDIRECT_URI` (or `${WEB_PUBLIC_ORIGIN}/api/auth/discord/callback` when
the setting is blank), set `DISCORD_APPLICATION_ID` and `DISCORD_CLIENT_SECRET` on the gateway,
and keep the OAuth scope at `identify`. The Discord application and bot must be the same
application used by `DISCORD_BOT_TOKEN`.

Until configured, social buttons stay disabled and forms show an explicit unavailable message. Sessions use
HttpOnly, SameSite=Lax cookies, Secure over production HTTPS. Lax allows the top-level
Discord callback; exact Origin and JSON checks protect POST requests. Codes expire after 10
minutes, allow five attempts, and are single-use. Sessions expire after 12 hours;
logout revokes them. Both are held in memory; a restart signs users out. Run one
gateway process; scaling requires shared session storage and coordinated account
creation. Password attempts, code requests, and email delivery are rate-limited.

Logout asks before discarding unsaved settings, then ends the session and returns
to login. Canceling leaves the session and drafts intact. Expired sessions also
return to login; request failures allow retrying logout.

## Files
- `index.html` — page content
- `styles.css` — layout and visual design
- `mhm-logo.png` — supplied Discord bot logo, used throughout the site and as the favicon
- `script.js` — small client-side enhancements
- `wrangler.jsonc` — Cloudflare Workers configuration
- `login.html`, `auth.js` — password, email-code, and social login plus verified account creation
- `app.html`, `app.js` — connected account details, password/provider setup, and logout
- `tasks.html`, `tasks.js` — signed-in task workspace and CRUD interactions
- `notes.html`, `notes.js` — signed-in notebook for creating and editing notes, journals, and lists
- `messages.html`, `messages.js` — personal message-template library and schedules
- `insights.html`, `insights.js` — private check-in analytics and Google Health controls
- `settings.js` — signed-in user settings forms
- `worker.mjs` — same-origin API proxy
- `../core/web_account_service.py` — account API and email verification
- `../core/web_user_settings.py` — validated settings and shared-data persistence
- `../core/web_gateway_runtime.py` — background service gateway lifecycle

## Verification

```powershell
python -m pytest tests/unit/test_web_account_service.py tests/unit/test_web_user_settings.py tests/unit/test_web_tasks.py tests/unit/test_web_notes.py tests/unit/test_web_gateway_runtime.py -q
node --test website/worker.test.mjs website/app.test.mjs website/auth.test.mjs website/settings.test.mjs
```

Tests inject isolated account and email adapters; they do not send real email or
write to production accounts.
