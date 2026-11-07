# Google Health Integration Guide

> **File**: `integrations/google_health/GOOGLE_HEALTH_GUIDE.md`  
> **Audience**: Developers  
> **Purpose**: OAuth setup, automated sync, safety constraints, and troubleshooting

## Overview

MHM reads **wellness data only** from the [Google Health API](https://developers.google.com/health/migration) (not the legacy Fitbit Web API). Data is normalized into daily summaries and derived **message guidance** tokens. AI prompts may receive **rounded sleep hours, step counts, and active minutes**, categorical bands, and **multi-day streak phrases**; resting HR / HRV stay band-only (no bpm/ms), and other raw metrics are never sent.

After a **one-time OAuth connect**, sync runs automatically via the scheduler (default 06:30 and 18:00). No daily manual steps are required.

## Google Cloud setup

1. Create a project in [Google Cloud Console](https://console.cloud.google.com).
2. Enable **Google Health API**.
3. Configure the **OAuth consent screen**:
   - User type: **External** (or Internal if using Google Workspace for yourself only).
   - Publishing status: **Testing** is fine for personal use (up to 100 test users).
   - Under **Test users**, click **Add users** and add every Google account that will connect (e.g. `jacfogel@gmail.com`). This step is **required** while the app is in Testing mode.
4. Create OAuth 2.0 credentials (**Web application**).
5. Add authorized redirect URI: `http://127.0.0.1:8765/oauth/google-health/callback` (must match `GOOGLE_HEALTH_REDIRECT_URI` in `.env` exactly).

**Important:** If you see *“Access blocked: MHM has not completed the Google verification process”* / **Error 403: access_denied**, your Google account is not on the test-user list (or you are signed into a different Google account in the browser than the one you added).

## Environment variables

Use section 7.1. "Google Health (read-only wellness integration)" in [CONFIGURATION_REFERENCE.md](../../CONFIGURATION_REFERENCE.md#71-google-health-read-only-wellness-integration) and the matching `.env.example` entries. Enable the integration and configure its client credentials there before connecting. Configuration definitions and defaults belong to that reference.

## OAuth scopes (read-only V0)

- `googlehealth.sleep.readonly`
- `googlehealth.activity_and_fitness.readonly`
- `googlehealth.health_metrics_and_measurements.readonly`

**Do not** pass `include_granted_scopes=true` — mixed legacy `fitness.*` scopes break the data plane.

## User flow

1. User runs `connect google health` (Discord) or opens admin UI → **Google Health** for the selected user.
2. MHM starts a local callback server on `127.0.0.1:8765`.
3. User approves Google consent in the browser.
4. MHM calls the authenticated `users/me/identity` endpoint, validates `healthUserId`, then saves it as `google_user_id` with tokens in `data/users/{user_id}/health/google_health_auth.json`. Token response fields and the legacy Fitbit ID are never used as Google identity. An identity failure leaves saved credentials unchanged; reconnect and retry. Existing documents with no ID still load and acquire one at the next connect/reconnect.
5. First sync runs immediately; `features.google_health` set to `enabled`.
6. Scheduler syncs 1–2× daily with automatic token refresh. Sync times (`GOOGLE_HEALTH_SYNC_TIMES`, default `06:30,18:00`) use the user's **account timezone**, checked every 30 minutes.

### Desktop manual sync

For a selected user, open **Google Health** and choose **Sync Now**. Sync runs in the background; the panel stays responsive and disables its account actions until it finishes. Repeated clicks do not start another sync. Wait for completion before closing the panel. Success refreshes the saved status. A connection failure prompts a retry; a paused/disabled account needs **Enable** first. If saved credentials were revoked, **Connect** becomes available and the panel asks you to reconnect before retrying. A missing connection also offers **Connect**.

The desktop calls the same sync operation as `sync health`; it does not change the schedule or bypass the account's enabled/paused state. Manual sync can update error state and trigger the existing automatic pause/reconnect-notice behavior.

### Personalization preferences

In the selected user's **Google Health** panel, choose **Use health data in scheduled messages** and **Use health data in chat**, then **Save Personalization**. Both default on to preserve existing behavior. Either can be disabled independently; sync continues while the account feature is enabled. **Pause** stops both sync and personalization regardless of these choices. Saved preferences apply to new requests, including fallback replies; a request already being generated may finish with its previous context.

## Commands (optional — not required daily)

| Command | Purpose |
|---------|---------|
| `connect google health` | One-time OAuth connect |
| `health status` | Connection and last sync |
| `pause health` | Stop sync and personalization |
| `enable health` | Resume after pause |
| `delete health data` | Wipe local health files |
| `sync health` | Debug manual sync only |

## Safety

- No diagnosis, treatment, or emergency detection.
- AI receives coarse guidance phrases plus rounded sleep/steps/active minutes and multi-day streaks when available (`core/health_context_builder.py`); never exact HR/HRV numbers or device names.
- API failures: log internally, fall back to normal messages.
- After repeated auth failures, feature auto-pauses (`GOOGLE_HEALTH_SYNC_FAILURE_PAUSE_THRESHOLD`).
- When token refresh failures auto-pause sync, MHM saves a pending reconnect warning before attempting delivery. Each scheduled health poll retries incomplete warnings for paused accounts without fetching health data. Primary-channel delivery (`sync_state.reconnect_notice_sent`) and the independent website copy (`reconnect_notice_website_sent`) are tracked separately and reset after a successful sync. Notice retries use this persisted state instead of the in-memory message retry queue. Disabled accounts and pauses caused by non-auth errors do not receive reconnect warnings.

## Derived signals (used for personalization)

Built by `signal_builder.py` from daily summaries. Baselines use only the prior calendar days configured by `GOOGLE_HEALTH_BASELINE_WINDOW_DAYS` (see configuration section 7.1), excluding the target day and future data. The default window is 14 days, bounded to 7–90. Sparse histories remain sparse: fewer than 7 baseline days means low confidence and empty guidance; 7–13 gives medium, 14 or more high. Missing metric values remain unknown or use existing absolute bands; no history is fabricated. Re-sync rebuilds affected dates using the current window.

Pagination follows every `nextPageToken`, including when a page is short or empty. Sleep requests stay capped at 25 records; other supported list endpoints default to 1,000, below Google's 10,000 cap. Daily rollup limits remain separate. Each sync logs attempted page counts by endpoint (including fallback/retry calls), without tokens or record contents. A deterministic 1,440-record fixture needs 58 pages at 25 versus 2 pages at 1,000; this measures request count, not live API latency. Provider contracts: [list](https://developers.google.com/health/reference/rest/v4/users.dataTypes.dataPoints/list), [endpoint-specific limits](https://developers.google.com/health/endpoints), and [identity](https://developers.google.com/health/reference/rest/v4/users/getIdentity).

Most fields are categorical; AI pattern text may also use rounded `sleep_hours`, `steps`, and `active_minutes`, plus streak phrases derived across recent signal days.

When today's signal is unavailable, health message pressure may use a non-low-confidence signal from the previous two calendar days. Future dates and older dates are excluded from this fallback. Corrected guidance and health personalization opt-out apply to the next pressure decision. Health guidance has no extra recovery timer; the 30-minute low-energy recovery hold belongs to explicit check-in answers and remains independent of health opt-out.

| Field | Source metrics | Purpose |
|-------|----------------|---------|
| `sleep_recovery` | sleep duration | Short / typical / fuller night |
| `sleep_hours` | sleep duration / 60 | Rounded (~nearest 0.5h) in AI pattern text |
| `sleep_vs_baseline` | sleep duration vs median | Below / near / above usual amount |
| `sleep_quality` | sleep efficiency + deep/REM share | Sleep quality band (more cautious of the two inputs) |
| `steps` | daily steps | Rounded (~nearest 100) in AI pattern text |
| `activity_level` | steps | Step-based activity band |
| `active_minutes` | active zone minutes | Rounded (~nearest 5) in AI pattern text |
| `active_intensity` | active zone minutes | Workout / effort intensity (can reinforce even when steps are low) |
| `resting_hr_signal` | resting HR vs median | Elevated readiness caution (band only; never bpm) |
| `hrv_signal` | HRV vs median | Lower readiness caution (band only; never ms) |
| `message_guidance` | personalization rules | Tone tokens for scheduled messages and chat |

Streak phrases (from `core/health_context_builder.py`, >=2 consecutive calendar days): shorter sleep, lighter activity, or higher activity.

Synced but not yet used for signals: calories (not fetched).

## Token encryption (optional)

Set `GOOGLE_HEALTH_TOKEN_ENCRYPTION_KEY` to a [Fernet](https://cryptography.io/en/latest/fernet/) key to encrypt `access_token` and `refresh_token` in `google_health_auth.json`:

```powershell
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

Add the output to `.env`. Existing plaintext tokens migrate automatically on the next save (connect, token refresh, or sync). **Keep the key backed up** — losing it requires running `connect google health` again.

## Troubleshooting

| Symptom | Action |
|---------|--------|
| **403 access_denied** — “has not completed the Google verification process” / “only accessed by developer-approved testers” | In [Google Cloud Console](https://console.cloud.google.com) → **APIs & Services** → **OAuth consent screen** → **Test users** → **Add users** → add the exact Gmail you use in the browser (e.g. `jacfogel@gmail.com`). Wait ~1 minute, then run `connect google health` again. Use the same Google account in Chrome that you added. |
| 403 on data reads (after connect) | Reconnect; ensure no `include_granted_scopes`; request only `googlehealth.*` scopes |
| Token refresh fails with HTTP 400 / `invalid_grant` | The refresh token is dead or revoked. `logs/google_health.log` will say **refresh token is invalid or revoked** (includes Google's `error=` code, never the token). Run `connect google health` once. After `GOOGLE_HEALTH_SYNC_FAILURE_PAUSE_THRESHOLD` failures, sync auto-pauses and you get one reconnect notice. |
| Token refresh fails with HTTP 5xx | Treated as transient; next scheduled sync retries. Persistent failures still auto-pause. |
| **HTTP 401 on data reads** | Access token was rejected. MHM force-refreshes once and retries. If that still 401s, the sync is a **failure** (not an empty success) so the slot can retry. Check `logs/google_health.log` for `authentication failed` then `refreshing access token and retrying once`. Reconnect only if refresh itself fails (`invalid_grant`). |
| Evening sync 401s after a morning refresh | Fixed: `expires_at` is stored in **local** time (same clock as the refresh check). A UTC vs local mix used to treat a 1-hour token as valid for ~7 hours in UTC-6. |
| No personalization | Check `health status`, the selected user's message/chat checkboxes, the enabled account feature, and at least 7 valid days inside the baseline window. Save preferences, sync, then start a new request; expect guidance only when sufficient recent data exists. |
| **Sync succeeds but `daily_summaries.json` is empty** | Restart MHM after updating (`python run_headless_service.py restart`), then run `sync health`. Check `logs/google_health.log` for lines like `listed N data point(s) for sleep`. If N is 0 for all types, confirm Fitbit has synced into Google Health (Fitbit app open + device synced). If N > 0 but summaries still empty, report — date parsing may need adjustment for your device payload. |
| **Steps/active minutes missing** | Google `dailyRollUp` rejects requests when `window_size_days * page_size > 90` (`INVALID_ROLLUP_QUERY_DURATION`). MHM clamps page size to 90 and chunks civil ranges to **14 days**. If rollup still fails, sync falls back to chunked `dataPoints` list. Restart after updates, then `sync health`. |
| “Could not start Google Health connect” | Restart MHM service after code/config changes; confirm `GOOGLE_HEALTH_*` in `.env` |

### Personal use vs public app

For a **single-user MHM install**, keep the OAuth app in **Testing** mode and add yourself as a test user. Full Google verification + CASA security assessment is only needed if you share the app with more than 100 users or publish it publicly.

## Post-ship monitoring

V0/V1 shipped; the implementation plan is archived. When reviewing live behavior, confirm:

- After 7–14 days of sync history, `confidence` rises to `medium`/`high` and `message_guidance` populates.
- `resting_hr_signal` / `hrv_signal` leave `unknown` once enough baseline days exist.
- Scheduled sends use guidance tone in logs (no raw metrics to the user).
- Auth refresh failure triggers auto-pause and one reconnect notice on the primary channel.
- Morning/evening sync entries appear in `logs/google_health.log` at the user's local `GOOGLE_HEALTH_SYNC_TIMES` (30-min poll).

**Ops tip:** Temporarily raise `GOOGLE_HEALTH_SYNC_LOOKBACK_DAYS` (default `3`) to backfill history for baselines faster.

Personalization preferences, authenticated identity, pagination diagnostics, and the bounded baseline window are implemented. Historical plan: [HEALTH_INTEGRATION_PLAN.md](../../archive/HEALTH_INTEGRATION_PLAN.md).

## Module map

All paths relative to project root.

- `integrations/google_health/testing.py` — shared `MHM_TESTING` guard for live OAuth/API skips
- `integrations/google_health/auth.py` — OAuth and token refresh
- `integrations/google_health/token_crypto.py` — optional Fernet encryption for auth tokens at rest
- `integrations/google_health/client.py` — API fetch + normalize
- `integrations/google_health/sync_manager.py` — per-user sync orchestration
- `integrations/google_health/user_settings.py` — shared connect/status/pause/enable/delete/sync (Discord + admin UI)
- `integrations/google_health/notifications.py` — one-time reconnect notice on auth auto-pause
- `integrations/google_health/signal_builder.py` — baselines and derived signals
- `integrations/google_health/personalization_rules.py` — deterministic guidance tokens
- `integrations/google_health/data_handlers.py` — on-disk I/O via `storage/user_item_storage`
- `scheduler/health_sync_schedule.py` — per-user local slot due logic
- `scheduler/health_sync_jobs.py` — 30-minute poll registration
- `ui/dialogs/google_health_settings_dialog.py` — admin connect panel
