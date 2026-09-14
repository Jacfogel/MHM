# MHM Website

Marketing site, email-code login/create-account page, and signed-in user settings.
The Python gateway uses the **same account store as MHM**. It never stores browser
passwords or creates a separate website database.

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

Existing users sign in with their account email. Each email must belong to only
one account. Duplicate emails prevent browser sign-in until an administrator
corrects the user data. Accounts without an email require an administrator to
add one before browser sign-in.
Suspended and inactive accounts cannot sign in. Delivery failures and skipped
ambiguous logins are recorded in the main log without codes or email addresses.

New accounts are created **after email verification**, through `create_new_user`.
They start with messaging, tasks, and check-ins disabled and no categories.
Users can configure these on their signed-in settings page. When Discord OAuth is configured,
new accounts are sent through Discord immediately after email verification; the account page
also has a Connect Discord button for existing accounts. The gateway exchanges the one-time
authorization code server-side, verifies the Discord identity, and stores only the Discord ID
and username in the existing MHM account. A Discord account already linked to another MHM
account is rejected. The bot's existing “Link account” flow remains available as a fallback.
Settings cover preferred name and profile lists, time zone and linked delivery
channel, message categories and reminder windows, task recurrence defaults, and
check-in windows, question selection, and counts. Each section saves to the same
profile documents used by the admin console, preserving other fields. Invalid
input is rejected, and edits to a section made elsewhere require reloading it.
Email, account identifiers, and administrator controls cannot be changed here.
Creating tasks and completing check-ins still use the existing app interfaces.

## Cloudflare Workers deployment

Build command: leave blank (static HTML/CSS/JS)
Deploy command: `npx wrangler deploy`

Run the deploy command from `website/`. The Worker serves static assets and proxies
only supported `/api/` routes. The static site alone cannot access local Python data.

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

For Discord connection, create an OAuth2 redirect in the Discord Developer Portal that exactly
matches `DISCORD_OAUTH_REDIRECT_URI` (or `${WEB_PUBLIC_ORIGIN}/api/auth/discord/callback` when
the setting is blank), set `DISCORD_APPLICATION_ID` and `DISCORD_CLIENT_SECRET` on the gateway,
and keep the OAuth scope at `identify`. The Discord application and bot must be the same
application used by `DISCORD_BOT_TOKEN`.

Until configured, forms show an explicit unavailable message. Sessions use
HttpOnly, SameSite=Lax cookies, Secure over production HTTPS. Lax allows the top-level
Discord callback; exact Origin and JSON checks protect POST requests. Codes expire after 10
minutes, allow five attempts, and are single-use. Sessions expire after 12 hours;
logout revokes them. Both are held in memory; a restart signs users out. Run one
gateway process; scaling requires shared session storage and coordinated account
creation. Request and email limits reduce repeated sends.

Logout asks before discarding unsaved settings, then ends the session and returns
to login. Canceling leaves the session and drafts intact. Expired sessions also
return to login; request failures allow retrying logout.

## Files
- `index.html` — page content
- `styles.css` — layout and visual design
- `script.js` — small client-side enhancements
- `wrangler.jsonc` — Cloudflare Workers configuration
- `login.html`, `auth.js` — login and verified account creation
- `app.html`, `app.js` — connected account details and logout
- `settings.js` — signed-in user settings forms
- `worker.mjs` — same-origin API proxy
- `../core/web_account_service.py` — account API and email verification
- `../core/web_user_settings.py` — validated settings and shared-data persistence
- `../core/web_gateway_runtime.py` — background service gateway lifecycle

## Verification

```powershell
python -m pytest tests/unit/test_web_account_service.py tests/unit/test_web_user_settings.py tests/unit/test_web_gateway_runtime.py -q
node --test website/worker.test.mjs website/app.test.mjs
```

Tests inject isolated account and email adapters; they do not send real email or
write to production accounts.
