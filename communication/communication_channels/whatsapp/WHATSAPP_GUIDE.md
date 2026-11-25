# WhatsApp: direct Meta Cloud API

> **File**: `communication/communication_channels/whatsapp/WHATSAPP_GUIDE.md`
> **Audience**: Developers and operators
> **Purpose**: Configure direct WhatsApp delivery, enrollment, and recovery

## 1. Account plan

WhatsApp has its own **$20 CAD/month** plan (`whatsapp`). It is separate from the
Discord + SMS plan; neither phone channel grants access to the other. A live-mode,
active WhatsApp subscription, an active MHM account, verified number, and explicit
WhatsApp consent are required for business commands and delivery. Trial,
complimentary, test-payment, past-due, and canceled accounts cannot use WhatsApp.
Existing paid-plan Discord/email access is unchanged.

Create a separate recurring CAD Stripe price for WhatsApp and configure
`STRIPE_WHATSAPP_PRICE_ID`. Enable that product in the Customer Portal if users
should switch plans there. Checkout and signed subscription reconciliation use
the configured price ID; metadata or a saved preference cannot unlock access.
Adding source configuration does not create a live Stripe product or price.

### 1.1. Activation progress (2026-11-21)

- Created live-mode product `prod_VfjYLTAiU58tk7` and recurring price
  `price_1UeO5pCZhRb9FSyUyrSZxh3U` (2,000 CAD cents/month). Both remain inactive
  pending Meta activation. The price ID is saved in the private `.env`.
- Added `https://sms.jacfogel.com/whatsapp/webhook` to the existing remotely
  managed Cloudflare tunnel, routing that exact path to loopback port 8083 before
  the general SMS rule. Read-back confirmed the website, SMS, and fallback rules
  were preserved. The previous tunnel configuration is backed up privately.
- Prepared the private settings and generated the webhook verify secret without
  displaying it. `WHATSAPP_ENABLED=false`; Meta app credentials and sender IDs
  are still missing. The existing service was confirmed running and was not restarted.
- Meta sign-in completed. The original MHM Facebook Login app
  (`1793246681803575`) cannot add WhatsApp. With owner authorization, created
  the `MHM Messaging` business portfolio (`980720881349434`) and WhatsApp app
  (`915694991538137`). Meta rejected the shorter portfolio name `MHM`.
  The portfolio is unverified; the app is unpublished. The app-creation Platform
  Terms and Developer Policies were accepted with explicit authorization.
- The separate WhatsApp Business Platform and Cloud API terms were accepted
  with explicit owner authorization. Production setup is available. Meta states
  the app must be published to receive real inbound messages, including from
  administrators; unpublished apps receive only dashboard test webhooks.
  Meta provisioned test number `+15551899979`, phone ID `1489685834226019`,
  and messaging account ID `1016292861525851`. With owner authorization, generated
  the dashboard access token and saved it privately in `.env`; a read-only Graph
  API check returned HTTP 200 and confirmed the test sender is `CONNECTED` on
  `CLOUD_API`. Token expiry has not yet been verified; production credentials
  still need review. A later read-only check rejected this saved dashboard token
  with HTTP 401 / Meta code 190; replace it before further testing. Do not treat
  the earlier successful check as current credential readiness. The owner selected the existing Twilio SMS business number
  as the intended production sender; it has not been registered with Meta.
- Saved the app privacy, terms, and data-deletion URLs to the existing MHM website,
  with category Utility and productivity. App-secret retrieval requires the
  owner to re-enter the Meta password; the secret is not yet stored.
- Meta WhatsApp Manager displays Account restricted and requires business
  verification before messaging. The owner confirmed MHM is not a registered
  business. Meta's official [document requirements](https://www.facebook.com/business/help/159334372093366)
  require official documents establishing the registered business name. No
  verification details or documents were submitted; the empty flow was exited.
  The Meta portfolio is an administrative container, not legal registration.
  No production sender has been registered, template submitted, subscription changed,
  customer charged, or live message sent. The portfolio ID is not a WhatsApp
  Business Account ID and must not be used for `WHATSAPP_BUSINESS_ACCOUNT_ID`.

Continue WhatsApp onboarding in the created app and configure its
WhatsApp app and business sender, and complete any required owner verification.
Store the authorized access token, app secret, business account ID, phone ID, and
international sending number privately. Obtain approval for the parameterless
`mhm_message_ready` template in `en_US`, with this proposed body:

> You have a new message from MHM. Reply OPEN to read it. Reply STOP to stop MHM WhatsApp messages.

The local website privacy/data pages now describe WhatsApp provider sharing,
waiting message bodies, separate transport records, disconnection, and retention.
These updates have not been deployed.

Before enabling purchases, verify provider eligibility, template approval, signed
webhook events, and live delivery. Then activate the Stripe product/price, add it
to the existing Customer Portal plan choices, deploy the website changes, restart
MHM once, and validate the separate plan's Checkout and subscription reconciliation.
Keep user preferences on their existing channel until an eligible account explicitly
connects WhatsApp and selects it.

## 2. Operator setup

Use a Meta developer app with WhatsApp, a WhatsApp Business Account, a registered
business phone, and an access token authorized to send WhatsApp messages. Store
credentials privately in `.env`; never put them in website source.

- `WHATSAPP_ENABLED=true` (default false)
- `WHATSAPP_ACCESS_TOKEN`: authorized system-user access token
- `WHATSAPP_APP_SECRET`: app secret for raw webhook signature verification
- `WHATSAPP_VERIFY_TOKEN`: independently generated secret for webhook subscription
- `WHATSAPP_BUSINESS_ACCOUNT_ID`: numeric business account ID
- `WHATSAPP_PHONE_NUMBER_ID`: numeric sending phone ID
- `WHATSAPP_PHONE_NUMBER`: displayed international sending number, including `+`
- `WHATSAPP_API_VERSION=v27.0`: supported versioned Graph API endpoint
- `WHATSAPP_WEBHOOK_PORT=8083`: loopback listener, separate from SMS and website
- `WHATSAPP_NOTIFICATION_TEMPLATE`: approved, parameterless notification template
- `WHATSAPP_TEMPLATE_LANGUAGE=en_US`: exact approved language

Publish **GET and POST `/whatsapp/webhook`** through a public HTTPS tunnel to
`http://127.0.0.1:8083/whatsapp/webhook`. Register this URL and the verify token in
Meta's app configuration; subscribe the app to the business account's `messages`
webhook field. The existing website Worker exposes authenticated enrollment routes;
the provider webhook goes directly to its own listener through the tunnel.
Restart MHM after configuration changes. Do not start a second service instance.

Meta's [webhook verification documentation](https://developers.facebook.com/docs/graph-api/webhooks/getting-started/)
describes the challenge and `X-Hub-Signature-256` signature. MHM validates the raw
body before parsing, checks both business account and receiving phone ID, ignores
unsupported media, and never logs webhook bodies or access tokens.

## 3. Connect and use WhatsApp

In website first-run delivery, Account > Delivery, or desktop Channel Settings:

1. Have an active paid WhatsApp plan.
2. Enter the WhatsApp number with country code and explicitly consent.
3. Request a connection code. From that number, send **LINK followed by the code**
   in WhatsApp to the displayed MHM number.
4. Verify the connection and choose WhatsApp delivery, then save.

Codes expire after 15 minutes and can be requested once per minute. They are hashed,
single-use, phone-bound, and account-bound. SMS verification does not count.
Website verification connects immediately; desktop verification stages until Save.
New desktop accounts start on Discord and can connect WhatsApp afterward.

Use `whatsapp status`, `help`, task commands, and check-in commands through the shared
message pipeline. Short replies such as `done` require exactly one linked prompt;
otherwise name the task or use `checkin <answer>`. Send **STOP** to opt out and
**START** to resume. These controls work after paid access ends. MHM saves the
control without sending a confirmation message; disconnection revokes consent.
Reconnection does not erase an opt-out. SMS and WhatsApp stop histories are separate.

## 4. Scheduled notifications and reply windows

Within 24 hours of a signed inbound WhatsApp message, MHM submits plain text up to
4,096 characters. Outside that window, MHM sends the configured, approved notification
template, saves the original message, and waits for **OPEN** before sending that
text. A suitable template requests OPEN to read a new MHM message without exposing
task or health details in the notification. Submit it for the appropriate Meta
category and language; approval and availability are controlled by Meta.

Templates have no arbitrary body placeholder. Missing template configuration blocks
out-of-window sends before contacting Meta. A template rejection discards its unsent
pending message. Unknown acceptance preserves pending text and suppresses automatic
resending. A task/check-in reply context attaches when the saved text is submitted,
not when the generic notification is sent. Existing check-in lifetime rules still
apply; if a check-in has expired, send `start checkin` to start an eligible one.

The website inbox remains available for the original messages. Do not infer handset
delivery from API acceptance; signed callbacks track sent, delivered, read, and
failed states without regression. MHM does not fetch prices or calculate Meta fees.

## 5. Recovery, persistence, and validation

`BASE_DATA_DIR/whatsapp_state.sqlite3` keeps independent enrollment, stop flags,
inbound receipts, delivery status, reply windows, contexts, and **pending message
bodies**. Protect it as user data and include it with application-data backups.
It reuses transactional phone-channel storage methods from `storage/sms_state.py`
but never shares the SMS database. Disconnecting clears pending text and contexts
while retaining receipt and opt-out history. Pending bodies expire after 24 hours before retrieval/export and during activity/maintenance. Terminal delivery details and completed inbound account attribution expire after 90 days; unresolved records remain for review. Website exports include attributed records. Account deletion clears pending bodies, sessions, enrollment and account associations, retaining only unlinked inbound IDs and stopped-number suppression digests. Do not delete the database to repair a connection.

Inbound IDs are claimed before commands run. After a crash, processing error, or
unconfirmed submission, check the task/check-in and website inbox before retrying.
Pending text is removed before OPEN submission to avoid replaying an uncertain send;
a crash there can require reading the message in the website inbox. `needs_review`
and `reply_unconfirmed` receipts require manual inspection. Check `logs/errors.log`,
then `logs/communication_manager.log`; channel lifecycle uses that same component.
Provider errors expose safe HTTP status only, without raw error bodies.

Tests use isolated SQLite and fake Meta HTTP calls. They do not establish live
delivery, template approval, business eligibility, or a live Stripe checkout.
Before regular use, verify Meta's challenge, LINK enrollment, a delivered message,
task completion, a full check-in, STOP/START, callbacks, and an expired-window
notification followed by OPEN. See [the behavior spec](../../../specs/whatsapp-meta-channel.md).

```powershell
python -m pytest tests/behavior/test_whatsapp.py -q
```
