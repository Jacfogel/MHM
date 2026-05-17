# Behavior Spec Coverage Matrix

> **File**: `specs/SPEC_COVERAGE_MATRIX.md`  
> **Audience**: Developers, AI collaborators, and reviewers  
> **Purpose**: Map behavior-spec scenarios to current automated/manual coverage and known gaps  
> **Style**: Coverage reference for planning and review  
> **Last Updated**: 2026-05-16

This matrix is a lightweight test roadmap for the scenarios in the Discord behavior specs.

Status legend:

- **Automated** - covered by an existing automated test at the scenario or close behavioral level.
- **Partial** - lower-level behavior is tested, but at least one scenario detail still needs direct coverage.
- **Manual** - covered by manual Discord validation only.
- **Gap** - no clear automated or manual coverage identified; add tests or checklist coverage before relying on it.

## Discord Check-In Flow

Spec: [discord-checkin-flow.md](discord-checkin-flow.md)

| Scenario | Status | Evidence / next action |
|---|---|---|
| User starts a check-in from Discord | Automated | [tests/behavior/test_discord_automation_complete.py](../tests/behavior/test_discord_automation_complete.py), [tests/behavior/test_checkin_handler_behavior.py](../tests/behavior/test_checkin_handler_behavior.py) |
| User answers a check-in question | Automated | [tests/behavior/test_discord_bot_behavior.py](../tests/behavior/test_discord_bot_behavior.py), [tests/behavior/test_checkin_handler_behavior.py](../tests/behavior/test_checkin_handler_behavior.py) |
| Check-in view creation | Automated | [tests/unit/test_checkin_view.py](../tests/unit/test_checkin_view.py) |
| Cancel Check-in button | Automated | [tests/unit/test_checkin_view.py](../tests/unit/test_checkin_view.py) |
| Skip Question button | Automated | [tests/unit/test_checkin_view.py](../tests/unit/test_checkin_view.py) |
| More button | Automated | [tests/unit/test_checkin_view.py](../tests/unit/test_checkin_view.py) |
| Check-in button clicked by unlinked user | Automated | [tests/unit/test_checkin_view.py](../tests/unit/test_checkin_view.py) |
| Check-in prompt send succeeds | Automated | [tests/behavior/test_discord_checkin_retry_behavior.py](../tests/behavior/test_discord_checkin_retry_behavior.py) |
| Check-in prompt send fails | Automated | [tests/behavior/test_discord_checkin_retry_behavior.py](../tests/behavior/test_discord_checkin_retry_behavior.py) |
| Retry after reconnect | Automated | [tests/behavior/test_discord_checkin_retry_behavior.py](../tests/behavior/test_discord_checkin_retry_behavior.py), [tests/communication/test_retry_manager.py](../tests/communication/test_retry_manager.py) |
| Check-in state changes remain outside Discord view code | Partial | Button tests assert routing through `handle_user_message`; add a static/behavior guard if this adapter boundary becomes high-risk. |

## Discord Connection and Webhook Lifecycle

Spec: [discord-connection-and-webhook-lifecycle.md](discord-connection-and-webhook-lifecycle.md)

| Scenario | Status | Evidence / next action |
|---|---|---|
| Valid token and network available | Automated | [tests/behavior/test_discord_bot_behavior.py](../tests/behavior/test_discord_bot_behavior.py) |
| Missing token | Automated | [tests/behavior/test_discord_bot_behavior.py](../tests/behavior/test_discord_bot_behavior.py) |
| DNS or network failure | Automated | [tests/behavior/test_discord_bot_behavior.py](../tests/behavior/test_discord_bot_behavior.py) |
| First ready event | Automated | [tests/behavior/test_discord_bot_behavior.py](../tests/behavior/test_discord_bot_behavior.py), [tests/unit/test_discord_event_handler.py](../tests/unit/test_discord_event_handler.py) |
| Duplicate ready event | Automated | [tests/behavior/test_discord_bot_behavior.py](../tests/behavior/test_discord_bot_behavior.py) |
| Events registered while bot is already ready | Partial | Ready/manual-trigger behavior is represented in bot tests; add a direct test for already-ready registration with unavailable loop if this regresses again. |
| Disconnect from ready state | Automated | [tests/unit/test_discord_event_handler.py](../tests/unit/test_discord_event_handler.py), [tests/behavior/test_discord_bot_behavior.py](../tests/behavior/test_discord_bot_behavior.py) |
| Connection-related error | Partial | Error hooks and network-health helpers are tested; add a direct `on_error` DNS/network classification test if needed. |
| Manual reconnect | Automated | [tests/behavior/test_discord_bot_behavior.py](../tests/behavior/test_discord_bot_behavior.py) |
| Bot is actually connected | Automated | [tests/behavior/test_discord_bot_behavior.py](../tests/behavior/test_discord_bot_behavior.py), [tests/unit/test_discord_bot_helpers.py](../tests/unit/test_discord_bot_helpers.py) |
| Bot is closed or unavailable | Automated | [tests/behavior/test_discord_bot_behavior.py](../tests/behavior/test_discord_bot_behavior.py), [tests/unit/test_discord_api_client.py](../tests/unit/test_discord_api_client.py) |
| Missing signature headers | Automated | [tests/behavior/test_webhook_server_behavior.py](../tests/behavior/test_webhook_server_behavior.py) |
| Signature public key configured | Automated | [tests/behavior/test_webhook_server_behavior.py](../tests/behavior/test_webhook_server_behavior.py) |
| Valid webhook event | Automated | [tests/behavior/test_webhook_server_behavior.py](../tests/behavior/test_webhook_server_behavior.py), [tests/behavior/test_webhook_handler_behavior.py](../tests/behavior/test_webhook_handler_behavior.py) |
| Unknown webhook event type | Automated | [tests/behavior/test_webhook_handler_behavior.py](../tests/behavior/test_webhook_handler_behavior.py) |
| Start webhook server | Automated | [tests/behavior/test_webhook_server_behavior.py](../tests/behavior/test_webhook_server_behavior.py) |
| Stop webhook server | Automated | [tests/behavior/test_webhook_server_behavior.py](../tests/behavior/test_webhook_server_behavior.py) |
| Bot joins a guild with suitable system channel | Manual | Covered by manual Discord validation; add automated `on_guild_join` tests for channel selection. |
| System channel unavailable but another text channel is sendable | Gap | Add automated `on_guild_join` fallback-channel coverage. |
| No sendable guild channel | Gap | Add automated `on_guild_join` no-channel coverage. |

## Discord Message and Command Routing

Spec: [discord-message-and-command-routing.md](discord-message-and-command-routing.md)

| Scenario | Status | Evidence / next action |
|---|---|---|
| Recognized Discord message | Automated | [tests/behavior/test_discord_bot_behavior.py](../tests/behavior/test_discord_bot_behavior.py), [tests/unit/test_discord_event_handler.py](../tests/unit/test_discord_event_handler.py) |
| Unrecognized Discord message | Partial | Account lookup and welcome paths are tested separately; add direct `on_message` unlinked-user coverage. |
| Bot-authored message is ignored | Automated | [tests/unit/test_discord_event_handler.py](../tests/unit/test_discord_event_handler.py) |
| Slash command registration | Automated | [tests/behavior/test_discord_bot_behavior.py](../tests/behavior/test_discord_bot_behavior.py) |
| Slash command from linked user | Automated | [tests/behavior/test_discord_bot_behavior.py](../tests/behavior/test_discord_bot_behavior.py), [tests/behavior/test_discord_automation_complete.py](../tests/behavior/test_discord_automation_complete.py) |
| Slash command from unlinked user | Partial | User lookup and welcome/account guidance are tested separately; add direct generated-slash unlinked coverage. |
| Classic command from linked user | Automated | [tests/behavior/test_discord_bot_behavior.py](../tests/behavior/test_discord_bot_behavior.py), [tests/behavior/test_discord_automation_complete.py](../tests/behavior/test_discord_automation_complete.py) |
| Classic command from unlinked user | Gap | Add direct dynamic classic command unlinked-user coverage. |
| Help command duplication avoided | Automated | [tests/behavior/test_discord_bot_behavior.py](../tests/behavior/test_discord_bot_behavior.py) |
| Suggestion button with structured payload | Partial | Payload storage/rendering is tested in [tests/behavior/test_discord_bot_behavior.py](../tests/behavior/test_discord_bot_behavior.py) and [tests/unit/test_discord_bot_helpers.py](../tests/unit/test_discord_bot_helpers.py); add click-dispatch coverage. |
| Suggestion button without structured payload | Gap | Add click-dispatch coverage for label/string fallback. |
| Suggestion button cannot be resolved | Gap | Add click-dispatch error-path coverage. |
| Pagination metadata is present | Automated | [tests/behavior/test_discord_bot_behavior.py](../tests/behavior/test_discord_bot_behavior.py), [tests/unit/test_discord_bot_helpers.py](../tests/unit/test_discord_bot_helpers.py) |
| Too many buttons are available | Automated | [tests/unit/test_discord_bot_helpers.py](../tests/unit/test_discord_bot_helpers.py) |
| Interaction manager raises during message processing | Partial | Discord error resilience is tested broadly; add direct `on_message` interaction-manager exception coverage. |

## Discord Message Delivery and Rich Responses

Spec: [discord-message-delivery-and-rich-responses.md](discord-message-delivery-and-rich-responses.md)

| Scenario | Status | Evidence / next action |
|---|---|---|
| Missing or invalid recipient | Automated | [tests/behavior/test_discord_bot_behavior.py](../tests/behavior/test_discord_bot_behavior.py), [tests/unit/test_discord_bot_helpers.py](../tests/unit/test_discord_bot_helpers.py) |
| Missing or invalid message | Automated | [tests/behavior/test_discord_bot_behavior.py](../tests/behavior/test_discord_bot_behavior.py), [tests/unit/test_discord_bot_helpers.py](../tests/unit/test_discord_bot_helpers.py) |
| Bot not ready | Partial | Send errors and readiness helpers are tested; add a direct public `send_message` not-ready assertion. |
| Delivery result timeout | Gap | Add a direct public `send_message` timeout test around queued command result handling. |
| Send to linked internal user's Discord DM | Partial | Recipient construction and DM helpers are tested; add direct `_send_message_internal("discord_user:<id>")` coverage. |
| Internal user has no linked Discord ID | Partial | Recipient failure paths are tested lower-level; add direct internal-user-without-Discord coverage. |
| Direct Discord DM | Automated | [tests/behavior/test_discord_bot_behavior.py](../tests/behavior/test_discord_bot_behavior.py), [tests/unit/test_discord_api_client.py](../tests/unit/test_discord_api_client.py) |
| Channel send | Automated | [tests/behavior/test_discord_bot_behavior.py](../tests/behavior/test_discord_bot_behavior.py), [tests/unit/test_discord_bot_helpers.py](../tests/unit/test_discord_bot_helpers.py) |
| Recipient cannot be resolved | Automated | [tests/behavior/test_discord_bot_behavior.py](../tests/behavior/test_discord_bot_behavior.py), [tests/unit/test_discord_api_client.py](../tests/unit/test_discord_api_client.py) |
| Rich data contains display fields | Automated | [tests/behavior/test_discord_bot_behavior.py](../tests/behavior/test_discord_bot_behavior.py), [tests/unit/test_discord_bot_helpers.py](../tests/unit/test_discord_bot_helpers.py), [tests/unit/test_rich_formatter.py](../tests/unit/test_rich_formatter.py) |
| Rich data contains only button metadata | Automated | [tests/behavior/test_discord_bot_behavior.py](../tests/behavior/test_discord_bot_behavior.py), [tests/unit/test_discord_bot_helpers.py](../tests/unit/test_discord_bot_helpers.py) |
| Rich data or message validation fails | Automated | [tests/behavior/test_discord_bot_behavior.py](../tests/behavior/test_discord_bot_behavior.py), [tests/unit/test_discord_bot_helpers.py](../tests/unit/test_discord_bot_helpers.py) |
| Suggestions present | Automated | [tests/behavior/test_discord_bot_behavior.py](../tests/behavior/test_discord_bot_behavior.py), [tests/unit/test_discord_bot_helpers.py](../tests/unit/test_discord_bot_helpers.py) |
| Pagination actions present | Automated | [tests/behavior/test_discord_bot_behavior.py](../tests/behavior/test_discord_bot_behavior.py), [tests/unit/test_discord_bot_helpers.py](../tests/unit/test_discord_bot_helpers.py) |
| Stored suggestion payload cache grows too large | Automated | [tests/unit/test_discord_bot_helpers.py](../tests/unit/test_discord_bot_helpers.py) |
| Custom view provided | Automated | [tests/unit/test_discord_bot_helpers.py](../tests/unit/test_discord_bot_helpers.py), [tests/behavior/test_discord_bot_behavior.py](../tests/behavior/test_discord_bot_behavior.py) |
| Custom view factory provided | Partial | Custom view attachment is tested; add direct callable factory success/failure coverage. |
| API client send message with options | Automated | [tests/unit/test_discord_api_client.py](../tests/unit/test_discord_api_client.py) |
| API client handles Discord permission errors | Automated | [tests/unit/test_discord_api_client.py](../tests/unit/test_discord_api_client.py) |

## Discord Task Reminder Flow

Spec: [discord-task-reminder-flow.md](discord-task-reminder-flow.md)

| Scenario | Status | Evidence / next action |
|---|---|---|
| Active task with due reminder | Automated | [tests/integration/test_task_reminder_integration.py](../tests/integration/test_task_reminder_integration.py), [tests/unit/test_channel_orchestrator.py](../tests/unit/test_channel_orchestrator.py) |
| Completed task is skipped | Automated | [tests/integration/test_task_reminder_integration.py](../tests/integration/test_task_reminder_integration.py), [tests/unit/test_channel_orchestrator.py](../tests/unit/test_channel_orchestrator.py) |
| Deleted task reminder cleanup | Automated | [tests/integration/test_task_reminder_integration.py](../tests/integration/test_task_reminder_integration.py), [tests/integration/test_orphaned_reminder_cleanup.py](../tests/integration/test_orphaned_reminder_cleanup.py) |
| Updated reminder schedule | Automated | [tests/integration/test_task_reminder_integration.py](../tests/integration/test_task_reminder_integration.py) |
| Scheduler marks reminder attempted after dispatch handoff | Partial | Current behavior is documented; add direct scheduler-level assertion that `reminder_sent` does not depend on `MessageSendResult`. |
| Task reminder view creation | Partial | Custom view attachment is tested; add direct `communication/communication_channels/discord/task_reminder_view.py` button-shape coverage. |
| Complete Task button | Partial | Completion by Discord reminder and task command behavior are tested; add direct button callback coverage. |
| Complete Task button from unlinked user | Gap | Add direct button callback coverage for unmapped Discord user. |
| Remind Me Later button | Gap | Add direct button callback coverage for acknowledgement-only behavior. |
| More button | Gap | Add direct button callback coverage for help text. |
| Complete by task ID from reminder | Automated | [tests/behavior/test_discord_bot_behavior.py](../tests/behavior/test_discord_bot_behavior.py), [tests/integration/test_task_reminder_integration.py](../tests/integration/test_task_reminder_integration.py) |
| Complete by typed title after reminder | Automated | [tests/behavior/test_discord_bot_behavior.py](../tests/behavior/test_discord_bot_behavior.py) |
| Recurring task is completed from Discord reminder | Automated | [tests/integration/test_task_reminder_integration.py](../tests/integration/test_task_reminder_integration.py) |

## Discord Welcome and Onboarding

Spec: [discord-welcome-and-onboarding.md](discord-welcome-and-onboarding.md)

| Scenario | Status | Evidence / next action |
|---|---|---|
| Primary welcome on app authorization (webhook) | Automated | [tests/behavior/test_webhook_handler_behavior.py](../tests/behavior/test_webhook_handler_behavior.py), [tests/unit/test_webhook_handler_gap_coverage.py](../tests/unit/test_webhook_handler_gap_coverage.py) |
| Already welcomed on authorization | Automated | [tests/behavior/test_webhook_handler_behavior.py](../tests/behavior/test_webhook_handler_behavior.py) |
| Deauthorize clears welcomed flag | Automated | [tests/behavior/test_webhook_handler_behavior.py](../tests/behavior/test_webhook_handler_behavior.py), [tests/behavior/test_welcome_manager_behavior.py](../tests/behavior/test_welcome_manager_behavior.py) |
| Welcome scheduling failure still marks welcomed | Automated | [tests/behavior/test_webhook_handler_behavior.py](../tests/behavior/test_webhook_handler_behavior.py), [tests/unit/test_webhook_handler_gap_coverage.py](../tests/unit/test_webhook_handler_gap_coverage.py) |
| `/start` without linked account | Manual | Covered by manual Discord validation; add direct slash `/start` handler coverage if this path changes. |
| DMs disabled on `/start` | Manual | Covered by manual Discord validation; add direct `discord.Forbidden` slash `/start` coverage. |
| First slash command without account | Partial | Webhook and welcome helpers are tested; add direct generated-slash unlinked/welcome-DM coverage. |
| Authorization copy | Automated | [tests/behavior/test_welcome_manager_behavior.py](../tests/behavior/test_welcome_manager_behavior.py), [tests/behavior/test_welcome_handler_behavior.py](../tests/behavior/test_welcome_handler_behavior.py) |
| Create account button | Partial | Welcome view creation and account handler creation logic are tested; add direct button-to-flow callback coverage. |
| Link account button | Partial | Welcome view creation and account handler link logic are tested; add direct button-to-flow callback coverage. |
| Persistent welcome buttons | Automated | [tests/behavior/test_welcome_handler_behavior.py](../tests/behavior/test_welcome_handler_behavior.py) |
| User already has an account | Automated | [tests/behavior/test_account_handler_behavior.py](../tests/behavior/test_account_handler_behavior.py) |
| Username modal and validation | Partial | Business validation is automated; Discord modal UI branch needs direct coverage if changed. |
| Feature selection defaults | Partial | Account feature creation is automated; Discord `FeatureSelectionView` defaults need direct UI coverage. |
| Feature selection timeout | Gap | Add direct `FeatureSelectionView.on_timeout` coverage. |
| Successful account creation | Automated | [tests/behavior/test_account_handler_behavior.py](../tests/behavior/test_account_handler_behavior.py) |
| Link by username then confirmation-code instructions | Partial | Account handler confirmation-code behavior is automated; current Discord instruction/follow-up path needs direct coverage. |

## Priority Automation Gaps

Good next tests to add:

1. `on_guild_join` channel-selection branches.
2. Suggestion-button click dispatch for structured payload, label fallback, and unresolved buttons.
3. Task-reminder button callbacks in `communication/communication_channels/discord/task_reminder_view.py`.
4. Public Discord `send_message` timeout/not-ready behavior.
5. Discord account-flow UI callbacks for welcome buttons, feature timeout, and confirmation-code instructions.
