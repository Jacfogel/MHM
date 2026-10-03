"""Authenticated website task routes over the existing task service."""

import asyncio

from aiohttp import web

from core.error_handling import handle_errors


class WebTaskRoutes:
    """Handle the task route family using gateway infrastructure."""

    @handle_errors(
        "initializing website task routes",
        user_friendly=False,
        re_raise=True,
    )
    def __init__(self, gateway):
        """Keep the shared gateway services used by task endpoints."""
        self.gateway = gateway


    # ERROR_HANDLING_EXCLUDE: Pure serializer is called only by guarded website routes.
    @staticmethod
    def task_view(task):
        """Return the stable, browser-safe task shape used by the website."""
        due = task.get("due") if isinstance(task.get("due"), dict) else {}
        recurrence = task.get("recurrence") if isinstance(task.get("recurrence"), dict) else {}
        completion = task.get("completion") if isinstance(task.get("completion"), dict) else {}
        reminders = []
        for reminder in task.get("reminders") if isinstance(task.get("reminders"), list) else []:
            period = reminder.get("period") if isinstance(reminder, dict) else None
            if (
                isinstance(period, dict)
                and reminder.get("kind") == "scheduled"
                and isinstance(period.get("date"), str)
                and isinstance(period.get("start_time"), str)
                and (period.get("end_time") is None or isinstance(period.get("end_time"), str))
            ):
                reminders.append({
                    "kind": "scheduled",
                    "period": {
                        "date": period.get("date"),
                        "start_time": period.get("start_time"),
                        "end_time": period.get("end_time"),
                    },
                })
            elif (
                isinstance(reminder, dict)
                and reminder.get("kind") == "quick"
                and isinstance(reminder.get("value"), str)
            ):
                reminders.append({"kind": "quick", "value": reminder["value"]})
        return {
            "id": str(task.get("id") or ""),
            "short_id": str(task.get("short_id") or ""),
            "title": str(task.get("title") or ""),
            "description": str(task.get("description") or ""),
            "priority": str(task.get("priority") or "medium"),
            "status": str(task.get("status") or "active"),
            "due_date": due.get("date"),
            "due_time": due.get("time"),
            "recurrence": {
                "pattern": recurrence.get("pattern"),
                "interval": recurrence.get("interval", 1),
                "repeat_after_completion": recurrence.get("repeat_after_completion", True),
                "next_due_date": recurrence.get("next_due_date"),
            },
            "reminders": reminders,
            "completion": {
                "completed": bool(completion.get("completed")),
                "completed_at": completion.get("completed_at"),
                "notes": str(completion.get("notes") or ""),
            },
            "tags": task.get("tags") if isinstance(task.get("tags"), list) else [],
            "reminder_snooze_until": task.get("reminder_snooze_until") or None,
            "parent_id": task.get("parent_id") or None,
            "created_at": task.get("created_at"),
            "updated_at": task.get("updated_at"),
        }


    # ERROR_HANDLING_EXCLUDE: Route failures are translated by the gateway middleware.
    async def tasks_api(self, request):
        """Handle authenticated website task routes through the task service."""
        uid, _ = await self.gateway.authenticated_account(request)
        from core.time_utilities import parse_date_only, parse_time_only_minute
        from tasks.task_service import (
            complete_task,
            create_task,
            delete_task,
            get_tasks_due_soon,
            load_active_tasks,
            load_completed_tasks,
            restore_task,
            update_task,
        )
        from tasks.task_data_manager import get_task_by_id
        task_id = request.match_info.get("task_id")
        action = request.match_info.get("action")
        quick_reminder_values = {
            "5-10min", "30min-1hour", "1-2hour", "1-2day", "3-5day", "1-2week"
        }

        # ERROR_HANDLING_EXCLUDE: Lookup helper raises an intentional HTTP response.
        def find(identifier):
            """Resolve a task identifier or raise the route's not-found response."""
            task = get_task_by_id(uid, identifier)
            if not task:
                raise web.HTTPNotFound(text="That task could not be found.")
            return task

        # ERROR_HANDLING_EXCLUDE: Validation helper raises intentional HTTP responses.
        def clean_reminder_periods(value):
            """Validate and normalize scheduled reminder periods from the browser."""
            if value is None:
                return []
            if not isinstance(value, list) or len(value) > 20:
                raise web.HTTPBadRequest(text="Add at most 20 scheduled reminders.")
            cleaned = []
            for period in value:
                if (
                    not isinstance(period, dict)
                    or set(period) - {"date", "start_time", "end_time"}
                    or not {"date", "start_time"}.issubset(period)
                ):
                    raise web.HTTPBadRequest(text="Each reminder needs a date and time; end time is optional.")
                date = period["date"]
                start = period["start_time"]
                end = period.get("end_time") or None
                if (
                    not isinstance(date, str) or parse_date_only(date) is None
                    or not isinstance(start, str) or parse_time_only_minute(start) is None
                    or (end is not None and (not isinstance(end, str) or parse_time_only_minute(end) is None or start >= end))
                ):
                    raise web.HTTPBadRequest(text="Reminder dates and times must be valid, and an optional end must be after the reminder time.")
                cleaned.append({"date": date, "start_time": start, "end_time": end})
            return cleaned

        # ERROR_HANDLING_EXCLUDE: Validation helper raises intentional HTTP responses.
        def clean_quick_reminders(value):
            """Validate the canonical relative reminder choices."""
            if value is None:
                return []
            if (
                not isinstance(value, list)
                or len(value) > len(quick_reminder_values)
                or len(set(value)) != len(value)
                or any(item not in quick_reminder_values for item in value)
            ):
                raise web.HTTPBadRequest(text="Choose valid relative reminders.")
            return value

        # ERROR_HANDLING_EXCLUDE: Validation helper raises intentional HTTP responses.
        def clean_completion(value):
            """Validate optional completion date, time, and notes."""
            if value in (None, {}):
                return None
            if not isinstance(value, dict) or set(value) != {
                "completion_date", "completion_time", "completion_notes"
            }:
                raise web.HTTPBadRequest(text="Please submit valid completion details.")
            completion_date = value["completion_date"]
            completion_time = value["completion_time"]
            completion_notes = value["completion_notes"]
            if (
                not isinstance(completion_date, str)
                or parse_date_only(completion_date) is None
                or not isinstance(completion_time, str)
                or parse_time_only_minute(completion_time) is None
                or not isinstance(completion_notes, str)
                or len(completion_notes) > 5000
            ):
                raise web.HTTPBadRequest(text="Use a valid completion date, time, and notes.")
            return {
                "completion_date": completion_date,
                "completion_time": completion_time,
                "completion_notes": completion_notes,
            }

        if request.method == "GET":
            status = request.query.get("status", "active")
            if status not in {"active", "completed", "all"}:
                raise web.HTTPBadRequest(text="Choose active, completed, or all tasks.")
            active = await asyncio.to_thread(load_active_tasks, uid)
            completed = await asyncio.to_thread(load_completed_tasks, uid)
            due_soon = await asyncio.to_thread(get_tasks_due_soon, uid, days_ahead=7)
            from core.tags import get_user_tags

            saved_tags = await asyncio.to_thread(get_user_tags, uid)
            selected = active if status == "active" else completed if status == "completed" else active + completed
            tags = sorted(
                {
                    str(tag).strip()
                    for tag in [
                        *saved_tags,
                        *[
                            task_tag
                            for task in active + completed
                            for task_tag in (task.get("tags") or [])
                        ],
                    ]
                    if str(tag).strip()
                },
                key=str.casefold,
            )
            return web.json_response({
                "tasks": [self.task_view(task) for task in selected],
                "active_count": len(active),
                "completed_count": len(completed),
                "due_soon_count": len(due_soon),
                "tags": tags,
            })

        if request.method == "POST" and not task_id:
            data = await self.gateway.body(request)
            allowed = {
                "title", "description", "due_date", "due_time", "priority",
                "recurrence_pattern", "recurrence_interval", "repeat_after_completion",
                "tags", "reminder_periods", "quick_reminders",
            }
            if set(data) - allowed:
                raise web.HTTPBadRequest(text="Please submit only supported task fields.")
            title = data.get("title")
            if not isinstance(title, str) or not title.strip():
                raise web.HTTPBadRequest(text="Give your task a title.")
            description = data.get("description", "")
            if not isinstance(description, str) or len(description) > 10000:
                raise web.HTTPBadRequest(text="Task descriptions must be 10,000 characters or fewer.")
            tags = data.get("tags", [])
            if not isinstance(tags, list) or any(not isinstance(tag, str) for tag in tags):
                raise web.HTTPBadRequest(text="Tags must be a list of words.")
            from tasks.task_tag_helpers import sanitize_task_tags
            tags = sanitize_task_tags(tags)
            reminder_periods = clean_reminder_periods(data.get("reminder_periods", []))
            quick_reminders = clean_quick_reminders(data.get("quick_reminders", []))
            due_date = data.get("due_date")
            if due_date == "":
                due_date = None
            if due_date is not None and (not isinstance(due_date, str) or parse_date_only(due_date) is None):
                raise web.HTTPBadRequest(text="Due dates must use YYYY-MM-DD.")
            due_time = data.get("due_time")
            if due_time == "":
                due_time = None
            if due_time is not None and (not isinstance(due_time, str) or parse_time_only_minute(due_time) is None):
                raise web.HTTPBadRequest(text="Due times must use HH:MM.")
            if quick_reminders and not due_date:
                raise web.HTTPBadRequest(text="Relative reminders need a due date.")
            priority = data.get("priority", "medium")
            from tasks.task_schemas import VALID_PRIORITIES
            if not isinstance(priority, str) or priority.lower() not in VALID_PRIORITIES:
                raise web.HTTPBadRequest(text="Choose a valid priority.")
            pattern = data.get("recurrence_pattern") or None
            if pattern is not None and pattern not in {"daily", "weekly", "monthly", "yearly"}:
                raise web.HTTPBadRequest(text="Choose a valid repeat pattern.")
            interval = data.get("recurrence_interval", 1)
            if type(interval) is not int or not 1 <= interval <= 365:
                raise web.HTTPBadRequest(text="Repeat intervals must be between 1 and 365.")
            repeat_after = data.get("repeat_after_completion", True)
            if type(repeat_after) is not bool:
                raise web.HTTPBadRequest(text="Choose whether repeats count from completion.")
            created_id = await asyncio.to_thread(
                create_task,
                uid,
                title=title.strip(), description=description,
                due_date=due_date, due_time=due_time, priority=priority.lower(),
                recurrence_pattern=pattern, recurrence_interval=interval,
                repeat_after_completion=repeat_after,
                tags=tags, reminder_periods=reminder_periods,
                quick_reminders=quick_reminders,
            )
            if not created_id:
                raise web.HTTPServiceUnavailable(text="MHM could not create that task. Please try again.")
            return web.json_response({"task": self.task_view(find(created_id))}, status=201)

        if not task_id:
            raise web.HTTPBadRequest(text="A task ID is required.")
        action_message = ""
        if action == "complete" and request.method == "POST":
            completion_data = clean_completion(await self.gateway.body(request))
            if not await asyncio.to_thread(
                complete_task, uid, task_id, completion_data
            ):
                raise web.HTTPNotFound(text="That active task could not be completed.")
        elif action == "restore" and request.method == "POST":
            data = await self.gateway.body(request)
            if set(data) - {"restore_steps"} or (
                "restore_steps" in data and type(data["restore_steps"]) is not bool
            ):
                raise web.HTTPBadRequest(
                    text="Choose whether to bring the smaller steps back."
                )
            if not await asyncio.to_thread(
                restore_task, uid, task_id, data.get("restore_steps") is True
            ):
                raise web.HTTPNotFound(text="That completed task could not be restored.")
        elif action == "snooze" and request.method == "POST":
            data = await self.gateway.body(request)
            option = data.get("option")
            custom_when = data.get("custom_when")
            if (
                set(data) - {"option", "custom_when"}
                or option not in {"1_hour", "tonight", "next_week", "custom"}
                or (
                    custom_when is not None
                    and (not isinstance(custom_when, str) or len(custom_when) > 200)
                )
                or (option == "custom" and not str(custom_when or "").strip())
            ):
                raise web.HTTPBadRequest(
                    text="Choose one hour, tonight, next week, or enter a custom reminder time."
                )
            from tasks.task_reminder_snooze import snooze_task_reminder

            result = await asyncio.to_thread(
                snooze_task_reminder,
                uid,
                task_id,
                option,
                custom_when=str(custom_when or "").strip() or None,
            )
            if not result or not result.success:
                raise web.HTTPBadRequest(
                    text=(result.message if result else "That reminder could not be snoozed.")
                )
            action_message = result.message
        elif action == "skip" and request.method == "POST":
            if await self.gateway.body(request):
                raise web.HTTPBadRequest(text="Skipping this occurrence does not need any other details.")
            from tasks.task_occurrence_skip import skip_task_occurrence

            result = await asyncio.to_thread(skip_task_occurrence, uid, task_id)
            if not result or not result.success:
                raise web.HTTPBadRequest(
                    text=(result.message if result else "That task occurrence could not be skipped.")
                )
            action_message = result.message
        elif action == "breakdown" and request.method == "POST":
            if await self.gateway.body(request):
                raise web.HTTPBadRequest(text="Breaking a task down does not need any other details.")
            from tasks.task_breakdown import suggest_breakdown

            result = await asyncio.to_thread(suggest_breakdown, uid, task_id)
            if not result or result.unavailable:
                raise web.HTTPServiceUnavailable(
                    text=(
                        result.message
                        if result
                        else "MHM could not suggest smaller steps just now. Please try again."
                    )
                )
            if not result.success:
                raise web.HTTPBadRequest(text=result.message)
            return web.json_response({"steps": result.steps})
        elif action == "subtasks" and request.method == "POST":
            data = await self.gateway.body(request)
            titles = data.get("titles")
            if (
                set(data) != {"titles"}
                or not isinstance(titles, list)
                or not 1 <= len(titles) <= 5
                or any(
                    not isinstance(title, str) or not title.strip() or len(title.strip()) > 120
                    for title in titles
                )
            ):
                raise web.HTTPBadRequest(text="Choose between 1 and 5 smaller steps.")
            from tasks.task_breakdown import add_task_subtasks

            result = await asyncio.to_thread(add_task_subtasks, uid, task_id, titles)
            if not result or not result.success:
                raise web.HTTPBadRequest(
                    text=(result.message if result else "Those steps could not be added.")
                )
            action_message = result.message
        elif action == "detach" and request.method == "POST":
            if await self.gateway.body(request):
                raise web.HTTPBadRequest(
                    text="Making a step its own task does not need any other details."
                )
            from tasks.task_breakdown import detach_task_step

            result = await asyncio.to_thread(detach_task_step, uid, task_id)
            if not result or not result.success:
                raise web.HTTPBadRequest(
                    text=(result.message if result else "That step could not be separated.")
                )
            action_message = result.message
        elif action == "simplify" and request.method == "POST":
            data = await self.gateway.body(request)
            new_title = data.get("new_title")
            if (
                set(data) != {"new_title"}
                or not isinstance(new_title, str)
                or not new_title.strip()
                or len(new_title.strip()) > 500
            ):
                raise web.HTTPBadRequest(text="Enter a smaller next step for this task.")
            from tasks.task_simplify import simplify_task

            result = await asyncio.to_thread(
                simplify_task, uid, task_id, new_title.strip()
            )
            if not result or not result.success or result.needs_title:
                raise web.HTTPBadRequest(
                    text=(result.message if result else "That task could not be simplified.")
                )
            action_message = result.message
        elif action is None and request.method == "PATCH":
            data = await self.gateway.body(request)
            allowed = {"title", "description", "due_date", "due_time", "priority", "recurrence_pattern", "recurrence_interval", "repeat_after_completion", "tags", "reminder_periods", "quick_reminders"}
            if not data or set(data) - allowed:
                raise web.HTTPBadRequest(text="Please submit supported task changes.")
            if "title" in data and (not isinstance(data["title"], str) or not data["title"].strip()):
                raise web.HTTPBadRequest(text="Give your task a title.")
            if "description" in data and (not isinstance(data["description"], str) or len(data["description"]) > 10000):
                raise web.HTTPBadRequest(text="Task descriptions must be 10,000 characters or fewer.")
            if "tags" in data:
                if not isinstance(data["tags"], list) or any(not isinstance(tag, str) for tag in data["tags"]):
                    raise web.HTTPBadRequest(text="Tags must be a list of words.")
                from tasks.task_tag_helpers import sanitize_task_tags
                data["tags"] = sanitize_task_tags(data["tags"])
            if "reminder_periods" in data:
                data["reminder_periods"] = clean_reminder_periods(data["reminder_periods"])
            if "quick_reminders" in data:
                data["quick_reminders"] = clean_quick_reminders(data["quick_reminders"])
            for key, parser, message in (("due_date", parse_date_only, "Due dates must use YYYY-MM-DD."), ("due_time", parse_time_only_minute, "Due times must use HH:MM.")):
                if key in data and data[key] not in (None, "") and (not isinstance(data[key], str) or parser(data[key]) is None):
                    raise web.HTTPBadRequest(text=message)
                if key in data and data[key] == "":
                    data[key] = None
            current_task = find(task_id)
            resulting_due_date = data.get("due_date", (current_task.get("due") or {}).get("date"))
            if "quick_reminders" in data:
                resulting_quick = data["quick_reminders"]
            else:
                resulting_quick = [
                    reminder.get("value")
                    for reminder in current_task.get("reminders", [])
                    if isinstance(reminder, dict) and reminder.get("kind") == "quick"
                ]
            if resulting_quick and not resulting_due_date:
                raise web.HTTPBadRequest(text="Relative reminders need a due date.")
            if "priority" in data:
                from tasks.task_schemas import VALID_PRIORITIES
                if not isinstance(data["priority"], str) or data["priority"].lower() not in VALID_PRIORITIES:
                    raise web.HTTPBadRequest(text="Choose a valid priority.")
                data["priority"] = data["priority"].lower()
            if "recurrence_pattern" in data and data["recurrence_pattern"] not in (None, "", "daily", "weekly", "monthly", "yearly"):
                raise web.HTTPBadRequest(text="Choose a valid repeat pattern.")
            if "recurrence_interval" in data and (type(data["recurrence_interval"]) is not int or not 1 <= data["recurrence_interval"] <= 365):
                raise web.HTTPBadRequest(text="Repeat intervals must be between 1 and 365.")
            if "repeat_after_completion" in data and type(data["repeat_after_completion"]) is not bool:
                raise web.HTTPBadRequest(text="Choose whether repeats count from completion.")
            if not await asyncio.to_thread(update_task, uid, task_id, data):
                raise web.HTTPNotFound(text="That active task could not be updated.")
        elif action is None and request.method == "DELETE":
            if not await asyncio.to_thread(delete_task, uid, task_id):
                raise web.HTTPNotFound(text="That task could not be deleted.")
            return web.json_response({"ok": True})
        else:
            raise web.HTTPMethodNotAllowed(request.method, {"GET", "POST", "PATCH", "DELETE"})
        return web.json_response(
            {"task": self.task_view(find(task_id)), **({"message": action_message} if action_message else {})}
        )


    # ERROR_HANDLING_EXCLUDE: Route failures are translated by the gateway middleware.
    async def tasks_bulk(self, request):
        """Apply one task action to an explicit set of the signed-in user's tasks."""
        uid, _ = await self.gateway.authenticated_account(request)
        data = await self.gateway.body(request)
        action = request.match_info["action"]
        task_ids = data.get("task_ids")
        extra = set(data) - {"task_ids"}
        if extra and not (
            action == "restore"
            and extra == {"restore_steps"}
            and type(data.get("restore_steps")) is bool
        ):
            raise web.HTTPBadRequest(text="Choose between 1 and 100 unique tasks.")
        if (
            not isinstance(task_ids, list)
            or not 1 <= len(task_ids) <= 100
            or len(set(task_ids)) != len(task_ids)
            or any(
                not isinstance(task_id, str) or not 1 <= len(task_id) <= 100
                for task_id in task_ids
            )
        ):
            raise web.HTTPBadRequest(text="Choose between 1 and 100 unique tasks.")
        from functools import partial

        from tasks.task_service import complete_task, delete_task, restore_task

        restore_steps = data.get("restore_steps") is True
        operation = {
            "complete": complete_task,
            "restore": partial(restore_task, restore_steps=restore_steps),
            "delete": delete_task,
        }[action]

        @handle_errors(
            "applying bulk website task actions",
            user_friendly=False,
            re_raise=True,
        )
        def apply_actions():
            """Return the requested task identifiers successfully changed in bulk."""
            from tasks.task_data_handlers import load_active_tasks, load_completed_tasks

            known = {}
            for task in (load_active_tasks(uid) or []) + (load_completed_tasks(uid) or []):
                task_key = str(task.get("id") or "")
                if task_key:
                    known[task_key] = task
            selected = set(task_ids)

            @handle_errors(
                "ranking a bulk task before its parent",
                user_friendly=False,
                default_return=1,
            )
            def family_rank(task_id: str) -> int:
                """Finish steps before the task they belong to."""
                task = known.get(task_id)
                parent_id = str((task or {}).get("parent_id") or "")
                return 0 if parent_id and parent_id in selected else 1

            ordered = sorted(task_ids, key=family_rank)
            return [task_id for task_id in ordered if operation(uid, task_id)]

        self.gateway.throttle(("tasks-bulk", uid), 20, 60)
        changed = await asyncio.to_thread(apply_actions)
        if not changed:
            raise web.HTTPNotFound(text="None of those tasks could be updated.")
        return web.json_response(
            {
                "ok": True,
                "changed": changed,
                "failed": [task_id for task_id in task_ids if task_id not in changed],
            }
        )


    # ERROR_HANDLING_EXCLUDE: Route failures are translated by the gateway middleware.
    async def task_templates(self, request):
        """Return safe built-in task templates for quick website creation."""
        await self.gateway.authenticated_account(request)
        from tasks.task_service import list_task_templates

        templates = await asyncio.to_thread(list_task_templates)
        return web.json_response(
            {
                "templates": [
                    {
                        "id": template.template_id,
                        "name": template.display_name,
                        "title": template.title,
                        "description": template.description,
                        "priority": template.priority,
                        "tags": list(template.tags),
                        "due_time": template.default_due_time,
                        "recurrence_pattern": template.recurrence_pattern,
                        "recurrence_interval": template.recurrence_interval,
                    }
                    for template in templates
                ]
            }
        )

    # ERROR_HANDLING_EXCLUDE: Route failures are translated by the gateway middleware.
    async def task_effort_api(self, request):
        """Estimate how many minutes each active task is likely to take."""
        uid, _current = await self.gateway.authenticated_account(request)
        from tasks.task_effort import estimate_task_efforts
        from tasks.task_service import load_active_tasks

        active = await asyncio.to_thread(load_active_tasks, uid)
        estimates = await asyncio.to_thread(estimate_task_efforts, active)
        return web.json_response({"tasks": estimates})

# ERROR_HANDLING_EXCLUDE: Shared serializer also supports account exports.
def task_view(task):
    """Return the stable, browser-safe task shape used by the website."""
    return WebTaskRoutes.task_view(task)


@handle_errors(
    "registering website task routes",
    user_friendly=False,
    re_raise=True,
)
def register_task_routes(app, gateway):
    """Register all task endpoints on a gateway application."""
    routes = WebTaskRoutes(gateway)
    app.router.add_get("/api/tasks/effort", routes.task_effort_api)
    app.router.add_get("/api/tasks", routes.tasks_api)
    app.router.add_post("/api/tasks", routes.tasks_api)
    app.router.add_get("/api/task-templates", routes.task_templates)
    app.router.add_post(
        "/api/tasks/bulk/{action:complete|restore|delete}", routes.tasks_bulk
    )
    app.router.add_route("PATCH", "/api/tasks/{task_id}", routes.tasks_api)
    app.router.add_route("DELETE", "/api/tasks/{task_id}", routes.tasks_api)
    app.router.add_post(
        "/api/tasks/{task_id}/{action:complete|restore|snooze|skip|simplify|breakdown|subtasks|detach}",
        routes.tasks_api,
    )

