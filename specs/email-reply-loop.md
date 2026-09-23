# Email reply loop

> **File**: `specs/email-reply-loop.md`  
> **Audience**: Developers, AI collaborators, and reviewers  
> **Purpose**: Behavior requirements for two-way email replies, threading, and check-in or task routing  
> **Style**: Behavior requirements and scenarios (see [SPECS_GUIDE.md](SPECS_GUIDE.md))  
> **Last Updated**: 2026-09-23  
> **Implementation**: `communication/communication_channels/email/bot.py`, `communication/communication_channels/email/inbound_processor.py`, `communication/communication_channels/email/quote_strip.py`, `communication/communication_channels/email/reply_context.py`, `communication/message_processing/email_reply_routing.py`, `communication/reminders/checkin_prompt_dispatcher.py`, `communication/reminders/reminder_dispatcher.py`  
> **Related**: [COMMUNICATION_GUIDE.md](../communication/COMMUNICATION_GUIDE.md), [discord-checkin-flow.md](discord-checkin-flow.md), [discord-task-reminder-flow.md](discord-task-reminder-flow.md)  
> **Automated tests**: `tests/unit/test_email_reply_loop.py`, `tests/unit/test_email_bot_gap_coverage.py`, `tests/communication/test_message_processing_scenarios.py`  
> **Coverage matrix**: [SPEC_COVERAGE_MATRIX.md](SPEC_COVERAGE_MATRIX.md#email-reply-loop)

## 1. Purpose

Email replies SHALL continue the message the user answered. The new text is separated from quoted history, the reply stays in the same thread, and a reply to a check-in or task reminder is applied to that check-in or task.

## 2. Requirements

### 2.1. Requirement: Quoted history is not treated as the new message

Inbound mail SHALL use the new reply text. Quoted originals, standard signatures, and common reply headers SHALL be removed before routing.

#### Scenario: User replies above a quoted check-in

- **GIVEN** MHM sent a check-in email  
- **WHEN** the user replies with an answer and the mail client includes the original message below it  
- **THEN** only the new answer is routed  
- **AND** the quoted original is not sent to the check-in or chat handler  

#### Scenario: Reply contains no new text

- **GIVEN** an inbound email whose body is only quoted history  
- **WHEN** the message is processed  
- **THEN** MHM asks for the answer above the quote  
- **AND** the quoted history is not treated as the user's message  

### 2.2. Requirement: Replies stay in the same thread

Outbound email SHALL set `Message-ID`. A response to an inbound email SHALL set `In-Reply-To` and `References`, and SHALL keep a single `Re:` subject prefix.

#### Scenario: User replies to an MHM email

- **GIVEN** MHM sent an email with a `Message-ID`  
- **WHEN** MHM answers the user's reply  
- **THEN** the answer includes that reply's `Message-ID` in `In-Reply-To` and `References`  
- **AND** the subject starts with one `Re:` prefix  

### 2.3. Requirement: Mail is marked read after it is handled

IMAP fetch SHALL use `BODY.PEEK` so unread mail stays unread. MHM SHALL mark the message `\Seen` only after handling succeeds.

#### Scenario: Reply is sent

- **GIVEN** an unread email from a registered user  
- **WHEN** MHM sends a response  
- **THEN** the inbox message is marked read  

#### Scenario: Sending the response fails

- **GIVEN** an unread email from a registered user  
- **WHEN** the response is not sent  
- **THEN** the inbox message stays unread  
- **AND** a later poll can try again  

### 2.4. Requirement: A reply maps back to the check-in or task it answers

MHM SHALL remember the outbound `Message-ID` for check-ins and task reminders. An inbound `In-Reply-To` or `References` match SHALL route that reply to the matching check-in or task.

#### Scenario: Reply to an open check-in

- **GIVEN** the user has an active check-in  
- **AND** they reply to that check-in email  
- **WHEN** the reply is processed  
- **THEN** the new text is answered as that check-in  
- **AND** another open flow is not used instead  

#### Scenario: Reply to a check-in that is no longer active

- **GIVEN** the check-in email's flow is no longer active  
- **WHEN** the user replies to that email  
- **THEN** the text is handled as a normal message  

#### Scenario: Reply to a task reminder

- **GIVEN** MHM sent a task reminder email for one task  
- **WHEN** the user replies `done`, `later`, `skip`, `simplify to ...`, `1 hour`, `tonight`, `next week`, or `until <when>`  
- **THEN** that action is applied to that task  
- **AND** an open check-in does not consume the reply  

#### Scenario: Task reply is not one of those actions

- **GIVEN** the user replies to a task reminder with other text  
- **WHEN** the reply is processed  
- **THEN** MHM explains the reply words it can apply to that task  

## 3. Out of scope

- Discord button behavior
- HTML-only clients that flatten the whole reply into one line before a quote marker
- Live mailbox delivery, which stays on the manual email checklist

## 4. Manual test checklist

- Reply to a check-in and confirm the answer is the new text, in the same thread.
- Reply `done` to a task reminder and confirm that task is completed.
- Interrupt sending and confirm the inbound mail stays unread.

## 5. Related documentation

- [COMMUNICATION_GUIDE.md](../communication/COMMUNICATION_GUIDE.md)
- [USER_DATA_MODEL.md](../core/USER_DATA_MODEL.md)
- [MANUAL_TESTING_GUIDE.md](../tests/MANUAL_TESTING_GUIDE.md)
