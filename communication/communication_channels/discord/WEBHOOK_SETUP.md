# Discord Webhook Implementation


> **File**: `communication/communication_channels/discord/WEBHOOK_SETUP.md`
**Purpose**: Automatic welcome messages when users authorize the MHM Discord app  
**Date**: 2025-11-12

---

## What We've Implemented

The MHM bot now automatically detects when users authorize the app via Discord's webhook events and sends them a welcome DM with setup instructions. **No user interaction required** - the welcome message is sent immediately upon authorization.

---

## How It Works

### 1. Webhook Server

**File**: `communication/communication_channels/discord/webhook_server.py`

- **HTTP server** that listens on port 8080 (configurable via `DISCORD_WEBHOOK_PORT`)
- **Receives POST requests** from Discord when webhook events occur
- **Validates security headers** (`X-Signature-Ed25519` and `X-Signature-Timestamp`) using ed25519 cryptography
- **Handles PING events** (Discord's validation) by responding with `204 No Content`
- **Processes APPLICATION_AUTHORIZED events** to trigger welcome messages

**Key Features**:
- Starts automatically when the Discord bot initializes (`on_ready` event)
- Runs in a separate daemon thread (non-blocking)
- Validates all incoming requests using Discord's public key
- Responds with `401 Unauthorized` if signature validation fails

### 2. Webhook Event Handler

**File**: `communication/communication_channels/discord/webhook_handler.py`

- **Parses webhook events** from Discord's JSON payload
- **Handles APPLICATION_AUTHORIZED events**:
  - Extracts user's Discord ID from event data
  - Checks if user already has an MHM account
  - Checks if user has already been welcomed
  - Sends welcome DM via the bot instance
  - Marks user as welcomed to prevent duplicates

### 3. Welcome Message System

**File**: `communication/communication_channels/discord/welcome_handler.py`

- **Tracks welcomed users** in `data/discord_welcome_tracking.json`
- **Generates personalized welcome messages** with:
  - User's Discord ID (for account linking)
  - Instructions for creating/linking MHM account
  - Quick command examples
- **Different messages** for app authorization vs. server messages

### 4. Integration Points

**File**: `communication/communication_channels/discord/bot.py`

- **Webhook server startup**: Starts automatically in `on_ready` event
- **Interaction detection**: Also detects new users via slash commands and DMs as fallback
- **Welcome message sending**: Uses bot's event loop to send DMs asynchronously

---

## Security Implementation

### Signature Verification

Discord requires all webhook requests to be validated using ed25519 cryptography:

1. **Extracts headers**: `X-Signature-Ed25519` and `X-Signature-Timestamp`
2. **Verifies signature**: Uses PyNaCl library to verify Discord signed `timestamp + body`
3. **Rejects invalid requests**: Responds with `401 Unauthorized` if signature doesn't match

**Required**:
- `PyNaCl>=1.5.0` Python package
- `DISCORD_PUBLIC_KEY` environment variable (from Discord Developer Portal)

### PING Event Handling

Discord sends PING events (`type: 0`) to validate endpoints:
- **Response**: `204 No Content` with `Content-Type: application/json` header
- **Required** for Discord to accept the webhook URL

---

## Configuration

### Environment Variables

- `DISCORD_WEBHOOK_PORT` - Port for webhook server (default: 8080)
- `DISCORD_PUBLIC_KEY` - Your app's public key from Discord Developer Portal (required for signature verification)
- `DISCORD_AUTO_NGROK` - Auto-launch ngrok tunnel when bot starts (default: false). Set to `true` to enable automatic ngrok startup.

### Required Packages

- `PyNaCl>=1.5.0` - For ed25519 signature verification

### Auto-Launch ngrok (Optional)

If `DISCORD_AUTO_NGROK=true` is set in your `.env` file, the bot will automatically start an ngrok tunnel when it initializes. This is useful for development:

1. **Install ngrok**: Make sure ngrok is installed and available in your PATH
2. **Enable auto-launch**: Add `DISCORD_AUTO_NGROK=true` to your `.env` file
3. **Start bot**: When the bot starts, it will automatically launch `ngrok http 8080`
4. **Get URL**: Check the ngrok web interface at `http://127.0.0.1:4040` for the public URL
5. **Configure Discord**: Copy the ngrok HTTPS URL to Discord Developer Portal webhook settings

**Note**: The ngrok tunnel will automatically stop when the bot shuts down.

---

## Event Flow

```
User Authorizes App in Discord
    ↓
Discord sends APPLICATION_AUTHORIZED webhook event
    ↓
Webhook server receives POST request
    ↓
Validates security headers (ed25519 signature)
    ↓
Parses event data → extracts Discord user ID
    ↓
Checks if user already has MHM account
    ↓
Checks if user already welcomed
    ↓
Bot sends welcome DM automatically
    ↓
User receives welcome message with setup instructions
```

---

## Fallback Detection Methods

In addition to webhook events, the system also detects new users via:

1. **Slash Commands**: When a user first uses any slash command (e.g., `/help`, `/start`)
2. **Direct Messages**: When a user sends their first DM to the bot
3. **Server Messages**: When a user sends their first message in a server

These methods ensure users get welcomed even if webhook events aren't available.

---

## Files Modified/Created

**New Files**:
- `communication/communication_channels/discord/webhook_server.py` - HTTP server for webhook events
- `communication/communication_channels/discord/webhook_handler.py` - Event parsing and handling
- `communication/communication_channels/discord/welcome_handler.py` - Welcome message management

**Modified Files**:
- `communication/communication_channels/discord/bot.py` - Added webhook server startup and interaction detection
- `communication/message_processing/interaction_manager.py` - Added `/start` command
- `core/config.py` - Added `DISCORD_PUBLIC_KEY` and `DISCORD_WEBHOOK_PORT` configuration
- `requirements.txt` - Added `PyNaCl>=1.5.0`

---

## Testing

To test the webhook implementation:

1. **Start bot**: `python run_headless_service.py start`
2. **Start ngrok**: `ngrok http 8080` (or use auto-launch feature)
3. **Configure webhook** in Discord Developer Portal with ngrok URL
4. **Authorize app** with test Discord account
5. **Check logs** for:
   ```
   Received webhook event: APPLICATION_AUTHORIZED
   User authorized app: Discord ID [id]
   Sent welcome DM to newly authorized user: [id]
   ```

---

## Notes

- **Development Mode**: If `DISCORD_PUBLIC_KEY` is not configured, signature verification is skipped (logs warning)
- **Production**: Proper signature verification is required for Discord's automated security checks
- **ngrok URLs**: Free ngrok URLs change on restart; update Discord webhook URL when ngrok restarts
- **Welcome Tracking**: Users are tracked to prevent duplicate welcome messages

---

**Implementation Complete** ✅
