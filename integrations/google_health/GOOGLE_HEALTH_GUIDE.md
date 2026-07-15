# Google Health Integration Guide

> **File**: `integrations/google_health/GOOGLE_HEALTH_GUIDE.md`  
> **Audience**: Developers  
> **Purpose**: OAuth setup, automated sync, safety constraints, and troubleshooting

## Overview

MHM reads **wellness data only** from the [Google Health API](https://developers.google.com/health/migration) (not the legacy Fitbit Web API). Data is normalized into daily summaries and derived **message guidance** tokens — raw metrics are never sent to the AI.

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

See `.env.example` and `CONFIGURATION_REFERENCE.md`. Minimum:

- `GOOGLE_HEALTH_ENABLED=true`
- `GOOGLE_HEALTH_CLIENT_ID`
- `GOOGLE_HEALTH_CLIENT_SECRET`

## OAuth scopes (read-only V0)

- `googlehealth.sleep.readonly`
- `googlehealth.activity_and_fitness.readonly`
- `googlehealth.health_metrics_and_measurements.readonly`

**Do not** pass `include_granted_scopes=true` — mixed legacy `fitness.*` scopes break the data plane.

## User flow

1. User runs `connect google health` (Discord) or opens admin UI → **Google Health** for the selected user.
2. MHM starts a local callback server on `127.0.0.1:8765`.
3. User approves Google consent in the browser.
4. Tokens saved to `data/users/{user_id}/health/google_health_auth.json`.
5. First sync runs immediately; `features.google_health` set to `enabled`.
6. Scheduler syncs 1–2× daily with automatic token refresh. Sync times (`GOOGLE_HEALTH_SYNC_TIMES`, default `06:30,18:00`) use the user's **account timezone**, checked every 30 minutes.

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
- AI receives coarse guidance phrases only (`core/health_context_builder.py`).
- API failures: log internally, fall back to normal messages.
- After repeated auth failures, feature auto-pauses (`GOOGLE_HEALTH_SYNC_FAILURE_PAUSE_THRESHOLD`).
- When auto-pause is triggered by token refresh failure, MHM sends **one** low-key reconnect message on the user's primary channel (`sync_state.reconnect_notice_sent` prevents repeats until the next successful sync).

## Derived signals (used for personalization)

Built by `signal_builder.py` from daily summaries — categorical only; raw minutes/% never go to the AI.

| Field | Source metrics | Purpose |
|-------|----------------|---------|
| `sleep_recovery` | sleep duration | Short / typical / fuller night |
| `sleep_vs_baseline` | sleep duration vs median | Below / near / above usual amount |
| `sleep_quality` | sleep efficiency + deep/REM share | Sleep quality band (more cautious of the two inputs) |
| `activity_level` | steps | Step-based activity band |
| `active_intensity` | active zone minutes | Workout / effort intensity (can reinforce even when steps are low) |
| `resting_hr_signal` | resting HR vs median | Elevated readiness caution |
| `hrv_signal` | HRV vs median | Lower readiness caution |
| `message_guidance` | personalization rules | Tone tokens for scheduled messages and chat |

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
| Token refresh fails | Run `connect google health` once; check refresh token in auth file. You should also receive a one-time reconnect notice on Discord/email when sync auto-pauses. |
| No personalization | Check `health status`, signal confidence, and `features.google_health` |
| **Sync succeeds but `daily_summaries.json` is empty** | Restart MHM after updating (`python run_headless_service.py restart`), then run `sync health`. Check `logs/google_health.log` for lines like `listed N data point(s) for sleep`. If N is 0 for all types, confirm Fitbit has synced into Google Health (Fitbit app open + device synced). If N > 0 but summaries still empty, report — date parsing may need adjustment for your device payload. |
| **Steps/active minutes missing after long lookback** | Google `dailyRollUp` allows **max 14 civil days** per request (`INVALID_ROLLUP_QUERY_DURATION` if exceeded). MHM chunks rollups automatically; set `GOOGLE_HEALTH_SYNC_LOOKBACK_DAYS` up to 14 per sync, or rely on accumulated history across daily syncs. Restart after updates, then `sync health`. |
| “Could not start Google Health connect” | Restart MHM service after code/config changes; confirm `GOOGLE_HEALTH_*` in `.env` |

### Personal use vs public app

For a **single-user MHM install**, keep the OAuth app in **Testing** mode and add yourself as a test user. Full Google verification + CASA security assessment is only needed if you share the app with more than 100 users or publish it publicly.

## Module map

All paths relative to project root.

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
