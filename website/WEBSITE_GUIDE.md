# MHM Website Guide


> **File**: `website/WEBSITE_GUIDE.md`
> **Audience**: Developers and maintainers
> **Purpose**: Website features, gateway setup, deployment, billing, and verification

For shared channel boundaries and the website inbox, see [COMMUNICATION_GUIDE.md](../communication/COMMUNICATION_GUIDE.md). For SMS pilot setup or health connection behavior surfaced by MHM, see [SMS_GUIDE.md](../communication/communication_channels/sms/SMS_GUIDE.md) and [GOOGLE_HEALTH_GUIDE.md](../integrations/google_health/GOOGLE_HEALTH_GUIDE.md).

The Home chat welcome remains at the beginning of the conversation after replies and refreshes; when older history is collapsed, More reveals it with the oldest turns. Basic help offers examples and points to commands for the full list instead of appending every slash alias.

Marketing site, password and social login/create-account page, signed-in home,
first-run setup, account settings, task workspace, notebook, personal message
library, and private insights.
New website-created accounts receive a 30-day trial. Account settings shows the
remaining trial, offers Discord ($10 CAD/month), SMS ($20 CAD/month), or WhatsApp ($20 CAD/month), and opens Stripe-hosted Checkout for the selected plan. It
uses Stripe's hosted Customer Portal for billing management. MHM stores Stripe
customer/subscription identifiers and lifecycle status, never card details.
The Python gateway uses the **same account store as MHM**. It never stores browser
passwords in plaintext or creates a separate website database. Passwords are
stored as salted scrypt hashes in the canonical account document.

Browser failure messages identify the attempted action, distinguish view failures from unconfirmed mutations, and explain how to check saved state before retrying. Keep draft text when a request fails; tell users to copy it before reloading. Network failures can occur after a successful save, so never infer that nothing changed from a missing response. Settings provide Reload this section after save failures, while validation retains its specific guidance.

## 1. Local preview

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
from the account page. After a successful sign-in, the browser opens Home, or
first-run setup when messages, tasks, and check-ins are all off, rather than
Account settings. Replacing a saved password requires either the current
password or a fresh emailed-code sign-in and revokes the account's other in-memory
browser sessions. The login page also has a **Forgot your password?** flow: the
replacement password is saved only after a six-digit email code is verified, all
older browser sessions are revoked, and the recovered account is signed in. Each email must belong to only
one account. Duplicate emails prevent browser sign-in until an administrator
corrects the user data. Accounts without an email require an administrator to
add one before browser sign-in.
Suspended and inactive accounts cannot sign in. Delivery failures and skipped
ambiguous logins are recorded in the main log without codes or email addresses.

New accounts choose a password and are created **after email verification**, through `create_new_user`.
Retrying Create account with an email belonging to a unique active account SHALL send an email sign-in code and resume that account after verification. This preserves its password, profile, and setup progress; it does not create another account or save the newly entered password. Suspended, inactive, and ambiguous accounts SHALL receive no code. Leaving before email verification SHALL allow a fresh signup code request, subject to the existing email rate limit.
They start with messaging, tasks, and check-ins disabled and no categories.
After sign-in they land on first-run setup for preferred name and time zone,
then choose messages, task reminders, and/or check-ins. The Personalized from your profile category reminds users to complete their profile in Account after setup. Each feature that stays
on gets its own steps: message categories and windows, an optional first task
and task windows, or check-in questions and windows. Window steps can keep the
gentle defaults. Accounts that already have
any of those features enabled skip setup. First-run also uses the same enabled
flags as Account settings, so a user with messages, tasks, and check-ins all off
still gets setup even if the account summary is missing `needs_setup`. Users can still change everything later
on the signed-in settings page. Account creation completes without
requiring a communication channel connection. New trial accounts can deliver through
Email immediately or connect Discord during first-run setup. The Delivery step
also offers SMS ($20 CAD/month) and WhatsApp ($20 CAD/month).
Channel selection is followed by a separate Connect step for Discord, SMS, or WhatsApp. Email skips that step. Connect shows only the selected connection and offers matching paid checkout for phone channels. Phone fields and consent controls stay disabled and visually muted until the matching paid plan is eligible and enrollment is available, then validate international format and consent before requests, remove spaces/parentheses/hyphens, and convert an explicit 00 prefix to +. Country codes are required rather than guessed; extensions and letters are rejected. Server-side validation and proof from the recipient phone are still required. This checkout explicitly charges immediately instead of deferring to
the trial end, then returns to Delivery for phone consent and ownership verification;
it does not mark setup complete. Access waits for the confirmed live-paid billing
state. Existing subscribers use Account billing management to change plans.
First-run delivery uses horizontal radio cards that stack on small screens. Each card places its badge, channel name, price, and description on separate lines with consistent spacing. The phone plan is labeled SMS; Email and Discord remain included. Signup verification simply asks users to look for a code at their email address. The signup form omits explanatory paragraphs about provider account creation, password saving, and email-code fallback; buttons, field labels, and password-length guidance provide the necessary instructions. Feature-specific progress steps remain hidden before the Features page; selecting SMS or WhatsApp removes the Free trial step from both progress and the setup flow. Email shows the same 30-day free trial note as Discord. Email is selected by default; Discord is visually highlighted as Recommended with $10 CAD/month and a 30-day free trial. All cards clarify that Email and Discord are included with every plan. There is no automatic-delivery option in first-run setup; the page names the selected channel before saving. Refresh connection rechecks saved enrollment and paid eligibility without reloading setup, including after delayed payment confirmation. WhatsApp omits the repeated unpaid-plan status message. Connection failures show recovery guidance and a
Refresh connection action; disabled enrollment remains disabled across setup steps. After
an active paid MHM subscription is recorded, users can choose paid delivery channels; connecting SMS additionally requires the SMS tier
in first-run delivery or Account > Delivery. SMS requires explicit consent and a
phone ownership code sent from the recipient phone; disconnecting revokes the
connection. Complimentary, past-due, canceled, and trial accounts cannot use SMS.
The server checks plan access again on every send and incoming SMS command;
STOP/START remain available for an enrolled number after a downgrade.
The gateway exchanges the one-time
authorization code server-side, verifies the Discord identity, and stores only the Discord ID
and username in the existing MHM account. A Discord account already linked to another MHM
account is rejected. The bot's existing "Link account" flow remains available as a fallback.
Settings cover preferred name, birth date, identity and health-context lists,
time zone and linked delivery channel, natural-language phrase times, message
categories and reminder windows, task recurrence defaults, and check-in windows,
question selection, and counts. Each section saves to the same profile documents
used by the admin console, preserving other fields. Invalid input is rejected,
and edits made elsewhere require reloading the affected section.

Reminder-window validation is shared by the message, task, and check-in settings
sections. It stages updates without changing the loaded documents, preserves
category metadata and applicable reserved all-day windows, and requires an enabled
window before enabling a feature.

Social login and create-account requests SHALL explicitly identify their intent and SHALL resolve the selected provider identity independently of any existing browser session. An existing browser session SHALL only be used for connecting a sign-in from Integrations.

Social sign-in callbacks separately validate the linking browser session and
resolve new accounts. Expired or revoked sessions return users to sign-in;
identities belonging to another account return a connection conflict. New-account
creation rechecks ownership under the identity-link lock. Failures retain safe
redirects and log the failed stage without authorization codes or provider secrets.

Users can disconnect Discord or optional social sign-ins (while retaining at
least one sign-in method) and download a secret-scrubbed JSON data export,
including tasks and notebook entries. Email,
internal account identifiers, suspension, and other administrator controls still
cannot be changed here.

Tasks can be created from built-in templates, edited, linked to web resources,
completed, restored, deleted, snoozed, skipped, simplified, or broken into smaller
steps. The task list is
shown first; title-only creation is the default, and template, details, due date,
priority, recurrence, tags, and reminders stay behind **More options**. The notebook adds
pinned, inbox, and archived views alongside active entries, with tags for organization. Messages remains accessible in navigation when message delivery is off. The Messages page manages category selection and the overall message-delivery switch through the same revision-checked settings endpoint as Account, with a link to Account for reminder times. Enabling a category prepares its missing default library; disabling it preserves templates and edited content. Re-enabling never overwrites an existing library. Personalized categories generate their content rather than expose an editable default library. Category saves retain unsaved message drafts; conflicts offer Reload categories. The message library
supports editing default templates and adding, scheduling, pausing, and deleting messages.
Insights show recent check-in patterns and history. A mood trend compares the seven
most recent mood ratings with the previous seven; until 14 mood ratings exist, the
page shows the average and progress toward a trend instead of labelling sparse data
as stable. Check-ins without a mood answer do not count toward that total. Optional Google and Facebook sign-ins are connected or disconnected from Integrations. Google Health can be viewed,
paused, enabled, synced, or deleted from that same page; initial connection still uses the
existing callback configured by `GOOGLE_HEALTH_REDIRECT_URI` (the default local
callback works only when the browser can reach the MHM host). Check-ins can be
answered on the Check-in page. Home can still queue one to email or Discord.
Task reminders can be delayed with a typed time, such as "Friday 3pm" or
"in 20 minutes," as well as the one-hour, tonight, and next-week choices.
The scheduler restores saved snoozes and reminders for skipped occurrences
on startup and checks for missing jobs every five minutes. If a saved reminder
became due while the service was down, it can be delivered late after recovery.

## 2. Cloudflare Workers deployment

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

For the separate WhatsApp plan, create a $20 CAD/month recurring price and set `STRIPE_WHATSAPP_PRICE_ID`. WhatsApp connection is available in setup and Account > Delivery, with its own verified number and consent. Meta webhook and notification-template setup are in [WHATSAPP_GUIDE.md](../communication/communication_channels/whatsapp/WHATSAPP_GUIDE.md). The SMS plan does not unlock WhatsApp. This source change does not create or publish the live Stripe price.

To enable billing, create separate Stripe Products and monthly CAD Prices for Discord ($10) and SMS ($20). Set `STRIPE_SECRET_KEY`, `STRIPE_DISCORD_PRICE_ID`, `STRIPE_PHONE_PRICE_ID`, `STRIPE_PORTAL_CONFIGURATION_ID`, and `STRIPE_WEBHOOK_SECRET` on the Python gateway. Register `${WEB_PUBLIC_ORIGIN}/api/billing/webhook` as a snapshot-event
webhook for `checkout.session.completed`, `customer.subscription.created`,
`customer.subscription.updated`, `customer.subscription.deleted`, `invoice.paid`,
`invoice.payment_succeeded`, and `invoice.payment_failed`. Configure Stripe's
Customer Portal so subscribers can update payment details and cancel. The optional
`BILLING_GRACE_PERIOD_DAYS` defaults to 3. Existing accounts without billing fields
are treated as complimentary accounts; new accounts get the trial explicitly.

### 2.1. Live-mode cutover and rollback

Do the live cutover as one controlled change. Never mix test-mode and live-mode
Stripe objects.

1. In Stripe live mode, create the separate **Discord $10 CAD/month** and **SMS $20 CAD/month** products/prices. Configure a dedicated Customer Portal with both products, prorated upgrades, and period-end downgrades/cancellations.
2. Create a live snapshot-event webhook for the public URL and the seven events
   listed above. Keep the live signing secret with that endpoint.
3. Back up the current Stripe key, both price IDs, portal configuration ID, and webhook secret, then replace all five with the matching live-mode values in one maintenance window.
4. Restart the running MHM service. A configuration-file edit alone does not
   update the gateway or scheduler process.
5. Confirm the public webhook still rejects an invalid signature with HTTP 400.
   Then use one controlled customer account to complete Checkout, verify the
   Stripe event deliveries return HTTP 200, and confirm MHM shows the active
   subscription and opens the Customer Portal.
6. Cancel the canary subscription in the portal and confirm Stripe's deletion
   event changes MHM to canceled and prevents newly scheduled activity. Restore
   the canary only after this end-to-end check succeeds.

For rollback, restore the backed-up five test-mode values together (or disable Checkout by removing its secret key), restart MHM, and confirm the account page
no longer offers an unintended live Checkout. Rolling back credentials does not
cancel live Stripe subscriptions; manage those separately in Stripe.

Keep `global_fetch_strictly_public` enabled in `wrangler.jsonc`. The website and
gateway share the `jacfogel.com` zone; this flag makes gateway requests use the
public Cloudflare path, matching requests that successfully reach the tunnel
from a browser. See [Cloudflare's fetch routing documentation](https://developers.cloudflare.com/workers/configuration/compatibility-flags/#global-fetch-strictly-public).
After changing Wrangler configuration, commit and push to trigger the connected
Cloudflare build, or deploy from `website/` with an authenticated Wrangler CLI.

For social sign-in, configure any of the following credential groups on the gateway.
Buttons remain disabled until both the client ID and secret are present. A verified
Google or Facebook email creates an account when that address is new, and otherwise
links the one active account that already uses it. Facebook can only do this when
it shares an email address. After the first success, the stable
provider subject is used and OAuth access/refresh tokens are not stored.

- Google: `GOOGLE_OAUTH_CLIENT_ID`, `GOOGLE_OAUTH_CLIENT_SECRET`, and optionally
  `GOOGLE_OAUTH_REDIRECT_URI`.
- Facebook: `FACEBOOK_OAUTH_CLIENT_ID`, `FACEBOOK_OAUTH_CLIENT_SECRET`, and optionally
  `FACEBOOK_OAUTH_REDIRECT_URI`. MHM asks for the public profile and email. If
  Facebook does not return an email, account creation stops.

When a redirect setting is blank it defaults to
`${WEB_PUBLIC_ORIGIN}/api/auth/oauth/<provider>/callback`. Register the exact callback
with the provider.

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

## 3. Files
- `index.html` - page content
- `privacy.html`, `terms.html`, `data.html` - privacy policy, terms of use, and download/deletion steps
- `styles.css` - layout and visual design
- `mhm-logo.png` - supplied Discord bot logo, used throughout the site and as the favicon
- `script.js` - year stamp and compact navigation menu
- `wrangler.jsonc` - Cloudflare Workers configuration
- `login.html`, `auth.js` - password, email-code, and social login plus verified account creation and password recovery
- `home.html`, `home.js` - signed-in home with the next task, a link to answer a check-in, a check-in request, one-line notebook capture, and More like this or Not for me on a scheduled message in the chat
- `checkin.html`, `checkin.js` - answer, skip, or cancel the current check-in in the browser
- `setup.html`, `setup.js` - first run for name/time zone, feature choice, then categories, questions, a first task, and reminder windows for each feature left on
- `app.html`, `app.js` - connected account details, password/provider setup, and logout
- `tasks.html`, `tasks.js` - signed-in task list first, with optional create fields behind More options
- `notes.html`, `notes.js` - signed-in notebook for creating and editing notes, journals, and lists
- `messages.html`, `messages.js` - personal message-template library and schedules
- `insights.html`, `insights.js` - private check-in analytics
- `integrations.html`, `integrations.js` - Google Health controls, linked from Account settings
- `settings.js` - signed-in user settings forms
- `worker.mjs` - same-origin API proxy
- `../core/web_account_service.py` - account API and email verification
- `../core/web_user_settings.py` - validated settings and shared-data persistence
- `../core/web_gateway_runtime.py` - background service gateway lifecycle

## 4. Verification

Node.js 20 or newer is required for the browser-side tests. The standard
`run_tests.py` suite and `audit --full` execute these tests through pytest; use
the direct Node command below when iterating on the website alone.

```powershell
$websitePythonTests = Get-ChildItem tests/unit -Filter "test_web*.py" | Sort-Object Name | Select-Object -ExpandProperty FullName
python -m pytest $websitePythonTests -q
$websiteJavaScriptTests = Get-ChildItem website -Filter "*.test.mjs" | Sort-Object Name | Select-Object -ExpandProperty FullName
node --test $websiteJavaScriptTests
```

Tests inject isolated account and email adapters; they do not send real email or
write to production accounts.

## 5. Subscription tiers and entitlements

Trials last 30 days and can deliver through Email or Discord. Discord costs $10 CAD/month. The
SMS tier costs $20 CAD/month and includes Discord; SMS also requires a
verified, consenting phone. Complimentary status is not the phone tier. A trial
subscription to the phone price still cannot use SMS until billing becomes active.

Checkout accepts only a named plan; amounts and price IDs come from the server.
Signed webhook handling retrieves the current Stripe subscription and resolves
`subscription_plan` and `stripe_price_id` from its actual item price. Unknown or
multiple-item subscriptions do not grant SMS. Plan changes use the dedicated
Stripe portal: upgrades invoice the proration, and cheaper-plan changes take effect
at period end. Reconciliation follows the current item, not stale event metadata.

The two-tier catalog and portal were configured and checkout-verified in Stripe
test mode on 2026-11-20. No real payments or subscriptions were created by validation.
Public Checkout and Portal actions are disabled while test keys are configured,
and the website displays a test-mode notice. `billing_livemode` must be true before
a phone subscription can unlock real SMS. The live-mode cutover was completed on
2026-11-21: both live CAD prices, the dedicated portal, and the seven-event webhook
are configured, and MHM was restarted. Unpaid live Checkout sessions for both plans
were verified and expired; the public webhook rejected an invalid signature and
accepted a harmless probe signed with the live secret. No payment or subscription
was created. Customer payment, Stripe-origin event delivery, portal operation, and
cancellation reconciliation still need the controlled customer check above.
Existing subscriptions are not repriced automatically.
