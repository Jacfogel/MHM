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

1. User runs `connect google health` (Discord or future admin UI).
2. MHM starts a local callback server on `127.0.0.1:8765`.
3. User approves Google consent in the browser.
4. Tokens saved to `data/users/{user_id}/health/google_health_auth.json`.
5. First sync runs immediately; `features.google_health` set to `enabled`.
6. Scheduler syncs 1–2× daily with automatic token refresh.

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

## Troubleshooting

| Symptom | Action |
|---------|--------|
| **403 access_denied** — “has not completed the Google verification process” / “only accessed by developer-approved testers” | In [Google Cloud Console](https://console.cloud.google.com) → **APIs & Services** → **OAuth consent screen** → **Test users** → **Add users** → add the exact Gmail you use in the browser (e.g. `jacfogel@gmail.com`). Wait ~1 minute, then run `connect google health` again. Use the same Google account in Chrome that you added. |
| 403 on data reads (after connect) | Reconnect; ensure no `include_granted_scopes`; request only `googlehealth.*` scopes |
| Token refresh fails | Run `connect google health` once; check refresh token in auth file |
| No personalization | Check `health status`, signal confidence, and `features.google_health` |
| **Sync succeeds but `daily_summaries.json` is empty** | Restart MHM after updating (`python run_headless_service.py restart`), then run `sync health`. Check `logs/google_health.log` for lines like `listed N data point(s) for sleep`. If N is 0 for all types, confirm Fitbit has synced into Google Health (Fitbit app open + device synced). If N > 0 but summaries still empty, report — date parsing may need adjustment for your device payload. |
| **Steps/active minutes missing after long lookback** | Google `dailyRollUp` allows **max 14 civil days** per request (`INVALID_ROLLUP_QUERY_DURATION` if exceeded). MHM chunks rollups automatically; set `GOOGLE_HEALTH_SYNC_LOOKBACK_DAYS` up to 14 per sync, or rely on accumulated history across daily syncs. Restart after updates, then `sync health`. |
| “Could not start Google Health connect” | Restart MHM service after code/config changes; confirm `GOOGLE_HEALTH_*` in `.env` |

### Personal use vs public app

For a **single-user MHM install**, keep the OAuth app in **Testing** mode and add yourself as a test user. Full Google verification + CASA security assessment is only needed if you share the app with more than 100 users or publish it publicly.

## Module map

- `auth.py` — OAuth and token refresh
- `client.py` — API fetch + normalize
- `sync_manager.py` — per-user sync orchestration
- `signal_builder.py` — baselines and derived signals
- `personalization_rules.py` — deterministic guidance tokens
- `data_handlers.py` — on-disk I/O via `storage/user_item_storage`
