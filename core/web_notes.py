"""Authenticated website routes for notebook entries."""

import asyncio

from aiohttp import web

from core.error_handling import handle_errors


# ERROR_HANDLING_EXCLUDE: Pure serializer is called only by guarded website routes.
def note_view(entry):
    """Return the stable, browser-safe representation of a notebook entry."""
    items = []
    for item in getattr(entry, "items", None) or []:
        items.append(
            {
                "id": str(item.id),
                "text": str(item.text),
                "done": bool(item.done),
                "order": int(item.order),
            }
        )
    return {
        "id": str(entry.id),
        "short_id": str(entry.short_id or ""),
        "kind": str(entry.kind),
        "title": str(entry.title or ""),
        "description": str(entry.description or ""),
        "items": items,
        "tags": [str(tag) for tag in (entry.tags or [])],
        "pinned": bool(entry.pinned) if str(entry.status) == "active" else False,
        "status": str(entry.status),
        "created_at": entry.created_at,
        "updated_at": entry.updated_at,
        "submitted_at": getattr(entry, "submitted_at", None),
        "source": str(
            (getattr(entry, "metadata", None) or {}).get("source") or ""
        ),
    }


class WebNotesRoutes:
    """Handle the notebook route family using shared gateway infrastructure."""

    @handle_errors(
        "initializing website notebook routes",
        user_friendly=False,
        re_raise=True,
    )
    def __init__(self, gateway):
        self.gateway = gateway

    # ERROR_HANDLING_EXCLUDE: Route failures are translated by gateway middleware.
    async def notes_api(self, request):
        """Handle authenticated website note routes through the notebook service."""
        uid, _ = await self.gateway.authenticated_account(request)
        from core.tags import normalize_tags
        from notebook import notebook_data_manager as notes

        note_id = request.match_info.get("note_id")
        action = request.match_info.get("action")

        # ERROR_HANDLING_EXCLUDE: Lookup helper raises an intentional HTTP response.
        def find(identifier, include_archived=True):
            """Resolve a notebook entry identifier or raise a not-found response."""
            entries = notes.list_recent(
                uid, n=1000, include_archived=include_archived
            )
            for entry in entries:
                if str(entry.id) == identifier or str(
                    entry.short_id or ""
                ).casefold() == identifier.casefold():
                    return entry
            raise web.HTTPNotFound(text="That note could not be found.")

        # ERROR_HANDLING_EXCLUDE: Validation helper raises intentional HTTP responses.
        def clean_list_items(value):
            """Validate and normalize list item edits from the browser."""
            if not isinstance(value, list) or not 1 <= len(value) <= 50:
                raise web.HTTPBadRequest(
                    text="Lists need between 1 and 50 items."
                )
            cleaned = []
            for item in value:
                if (
                    not isinstance(item, dict)
                    or set(item) != {"text", "done"}
                    or not isinstance(item["text"], str)
                    or not item["text"].strip()
                    or len(item["text"]) > 500
                    or type(item["done"]) is not bool
                ):
                    raise web.HTTPBadRequest(
                        text=(
                            "Each list item needs text and a valid completion state."
                        )
                    )
                cleaned.append(
                    {"text": item["text"].strip(), "done": item["done"]}
                )
            return cleaned

        if request.method == "GET":
            status = request.query.get("status", "active")
            if status not in {"active", "pinned", "inbox", "archived", "all"}:
                raise web.HTTPBadRequest(
                    text="Choose active, pinned, inbox, archived, or all notes."
                )
            query = request.query.get("q", "").strip()
            tag_filter = request.query.get("tag", "").strip()
            if len(query) > 500 or len(tag_filter) > 100:
                raise web.HTTPBadRequest(text="Keep notebook filters brief.")
            if query:
                entries = notes.search_entries(uid, query, limit=100)
            elif status == "pinned":
                entries = notes.list_pinned(uid, limit=100)
            elif status == "inbox":
                entries = notes.list_inbox(uid, limit=100)
            else:
                entries = notes.list_recent(
                    uid, n=100, include_archived=status != "active"
                )
            if status not in {"all", "pinned", "inbox"}:
                entries = [entry for entry in entries if entry.status == status]
            if tag_filter:
                entries = [
                    entry
                    for entry in entries
                    if tag_filter.casefold()
                    in {str(tag).casefold() for tag in (entry.tags or [])}
                ]
            all_entries = notes.list_recent(
                uid, n=1000, include_archived=True
            )
            from core.tags import get_user_tags

            saved_tags = await asyncio.to_thread(get_user_tags, uid)
            tags = sorted(
                {
                    str(tag).strip()
                    for tag in [
                        *saved_tags,
                        *[
                            tag
                            for entry in all_entries
                            for tag in (entry.tags or [])
                        ],
                    ]
                    if str(tag).strip()
                },
                key=str.casefold,
            )
            return web.json_response(
                {
                    "notes": [note_view(entry) for entry in entries],
                    "count": len(entries),
                    "tags": tags,
                }
            )

        if request.method == "POST" and not note_id:
            data = await self.gateway.body(request)
            allowed = {"kind", "title", "description", "items", "tags"}
            if set(data) - allowed:
                raise web.HTTPBadRequest(
                    text="Please submit only supported note fields."
                )
            kind = data.get("kind", "note")
            if kind not in {"note", "journal_entry", "list"}:
                raise web.HTTPBadRequest(text="Choose note, journal, or list.")
            title = data.get("title")
            description = data.get("description", "")
            if not isinstance(title, str) or not title.strip():
                raise web.HTTPBadRequest(text="Give your entry a title.")
            if len(title.strip()) > 200:
                raise web.HTTPBadRequest(
                    text="Entry titles must be 200 characters or fewer."
                )
            if not isinstance(description, str) or len(description) > 10000:
                raise web.HTTPBadRequest(
                    text="Entry text must be 10,000 characters or fewer."
                )
            tags = data.get("tags", [])
            if not isinstance(tags, list) or any(
                not isinstance(tag, str) for tag in tags
            ):
                raise web.HTTPBadRequest(text="Tags must be a list of words.")
            tags = normalize_tags(tags)
            if kind == "list":
                items = clean_list_items(data.get("items"))
                entry = await asyncio.to_thread(
                    notes.create_list,
                    uid,
                    title=title.strip(),
                    items=[item["text"] for item in items],
                    tags=tags,
                )
                if entry and any(item["done"] for item in items):
                    entry = await asyncio.to_thread(
                        notes.set_list_items, uid, str(entry.id), items
                    )
            elif kind == "journal_entry":
                entry = await asyncio.to_thread(
                    notes.create_journal,
                    uid,
                    title=title.strip(),
                    description=description,
                    tags=tags,
                )
            else:
                entry = await asyncio.to_thread(
                    notes.create_note,
                    uid,
                    title=title.strip(),
                    description=description,
                    tags=tags,
                )
            if not entry:
                raise web.HTTPBadRequest(
                    text="MHM could not create that entry."
                )
            return web.json_response({"note": note_view(entry)}, status=201)

        if not note_id:
            raise web.HTTPBadRequest(text="A note ID is required.")
        if action in {"archive", "restore"} and request.method == "POST":
            find(note_id, include_archived=True)
            if not await asyncio.to_thread(
                notes.archive_entry, uid, note_id, action == "archive"
            ):
                raise web.HTTPNotFound(text="That note could not be updated.")
            return web.json_response(
                {"note": note_view(find(note_id, include_archived=True))}
            )
        if action is None and request.method == "PATCH":
            data = await self.gateway.body(request)
            allowed = {"title", "description", "items", "tags", "pinned"}
            if not data or set(data) - allowed:
                raise web.HTTPBadRequest(
                    text="Please submit supported note changes."
                )
            if "title" in data and (
                not isinstance(data["title"], str)
                or not data["title"].strip()
                or len(data["title"].strip()) > 200
            ):
                raise web.HTTPBadRequest(
                    text="Entry titles must be between 1 and 200 characters."
                )
            if "description" in data and (
                not isinstance(data["description"], str)
                or len(data["description"]) > 10000
            ):
                raise web.HTTPBadRequest(
                    text="Entry text must be 10,000 characters or fewer."
                )
            if "tags" in data and (
                not isinstance(data["tags"], list)
                or any(not isinstance(tag, str) for tag in data["tags"])
            ):
                raise web.HTTPBadRequest(text="Tags must be a list of words.")
            if "tags" in data:
                data["tags"] = normalize_tags(data["tags"])
            current_entry = find(note_id, include_archived=False)
            if "items" in data:
                data["items"] = clean_list_items(data["items"])
                if current_entry.kind != "list":
                    raise web.HTTPBadRequest(
                        text="Only list entries can have list items."
                    )
            if "description" in data and current_entry.kind == "list":
                raise web.HTTPBadRequest(
                    text="List entries are edited through their list items."
                )
            if "title" in data and not await asyncio.to_thread(
                notes.set_entry_title, uid, note_id, data["title"]
            ):
                raise web.HTTPNotFound(
                    text="That entry could not be updated."
                )
            if "description" in data and not await asyncio.to_thread(
                notes.set_entry_body, uid, note_id, data["description"]
            ):
                raise web.HTTPNotFound(text="That note could not be updated.")
            if "items" in data and not await asyncio.to_thread(
                notes.set_list_items, uid, note_id, data["items"]
            ):
                raise web.HTTPNotFound(text="That list could not be updated.")
            if "tags" in data:
                current = find(note_id, include_archived=False)
                await asyncio.to_thread(
                    notes.remove_tags, uid, note_id, list(current.tags)
                )
                if data["tags"] and not await asyncio.to_thread(
                    notes.add_tags, uid, note_id, data["tags"]
                ):
                    raise web.HTTPNotFound(
                        text="That note could not be updated."
                    )
            if "pinned" in data and type(data["pinned"]) is not bool:
                raise web.HTTPBadRequest(
                    text="Choose whether the entry is pinned."
                )
            if "pinned" in data and not await asyncio.to_thread(
                notes.pin_entry, uid, note_id, data["pinned"]
            ):
                raise web.HTTPNotFound(text="That note could not be updated.")
            return web.json_response(
                {"note": note_view(find(note_id, include_archived=False))}
            )
        raise web.HTTPMethodNotAllowed(request.method, {"GET", "POST", "PATCH"})


@handle_errors(
    "registering website notebook routes",
    user_friendly=False,
    re_raise=True,
)
def register_notes_routes(app, gateway):
    """Register all notebook endpoints on a website gateway application."""
    routes = WebNotesRoutes(gateway)
    app.router.add_get("/api/notes", routes.notes_api)
    app.router.add_post("/api/notes", routes.notes_api)
    app.router.add_route("PATCH", "/api/notes/{note_id}", routes.notes_api)
    app.router.add_post(
        "/api/notes/{note_id}/{action:archive|restore}", routes.notes_api
    )
