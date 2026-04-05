"""MCP server exposing the semantic memory tools to the Claude Agent SDK."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from claude_agent_sdk import create_sdk_mcp_server, tool

from hippo.memory.buffer import ObsidianBufferStore
from hippo.memory.episodic import ObsidianEpisodicStore
from hippo.memory.mailbox import ObsidianMailboxStore, load_bot_registry
from hippo.memory.scheduled import ObsidianScheduledStore
from hippo.memory.semantic import ObsidianSemanticStore
from hippo.memory.types import BufferEntry, Entity, Relation

# Module-level stores, set by create_memory_server()
_store: ObsidianSemanticStore | None = None
_episodic_store: ObsidianEpisodicStore | None = None
_scheduled_store: ObsidianScheduledStore | None = None
_buffer_store: ObsidianBufferStore | None = None
_mailbox_store: ObsidianMailboxStore | None = None
_bot_name: str = "alice"


def _get_store() -> ObsidianSemanticStore:
    if _store is None:
        msg = "Memory server not initialized — call create_memory_server() first"
        raise RuntimeError(msg)
    return _store


def _get_episodic_store() -> ObsidianEpisodicStore:
    if _episodic_store is None:
        msg = "Episodic store not initialized — call create_memory_server() first"
        raise RuntimeError(msg)
    return _episodic_store


def _get_scheduled_store() -> ObsidianScheduledStore:
    if _scheduled_store is None:
        msg = "Scheduled store not initialized — call create_memory_server() first"
        raise RuntimeError(msg)
    return _scheduled_store


def _get_buffer_store() -> ObsidianBufferStore:
    if _buffer_store is None:
        msg = "Buffer store not initialized — call create_memory_server() first"
        raise RuntimeError(msg)
    return _buffer_store


def _get_mailbox_store() -> ObsidianMailboxStore:
    if _mailbox_store is None:
        msg = "Mailbox store not initialized — call create_memory_server() first"
        raise RuntimeError(msg)
    return _mailbox_store


def _text(content: str) -> dict[str, Any]:
    return {"content": [{"type": "text", "text": content}]}


def _json_result(data: Any) -> dict[str, Any]:
    return _text(json.dumps(data, ensure_ascii=False, indent=2))


# ---------------------------------------------------------------------------
# Tool definitions
# ---------------------------------------------------------------------------


@tool(
    "create_entities",
    "Create new entities in the knowledge graph. Skips entities that already exist.",
    {
        "entities": list,  # [{name, entityType, observations[]}]
    },
)
async def create_entities(args: dict[str, Any]) -> dict[str, Any]:
    raw_entities = args["entities"]
    entities = [
        Entity(
            name=e["name"],
            entity_type=e["entityType"],
            observations=tuple(e.get("observations", [])),
        )
        for e in raw_entities
    ]
    created = await _get_store().create_entities(entities)
    names = [e.name for e in created]
    return _text(f"Created {len(created)} entities: {names}")


@tool(
    "create_relations",
    "Create relations between entities. Skips duplicates.",
    {
        "relations": list,  # [{from, to, relationType}]
    },
)
async def create_relations(args: dict[str, Any]) -> dict[str, Any]:
    raw = args["relations"]
    relations = [
        Relation(
            from_entity=r["from"],
            to_entity=r["to"],
            relation_type=r["relationType"],
        )
        for r in raw
    ]
    created = await _get_store().create_relations(relations)
    return _text(f"Created {len(created)} relations.")


@tool(
    "add_observations",
    "Add observations to an existing entity. Skips duplicates.",
    {
        "observations": list,  # [{entityName, contents[]}]
    },
)
async def add_observations(args: dict[str, Any]) -> dict[str, Any]:
    results = []
    for item in args["observations"]:
        entity_name = item["entityName"]
        contents = item["contents"]
        added = await _get_store().add_observations(entity_name, contents)
        results.append({"entityName": entity_name, "addedObservations": added})
    return _json_result(results)


@tool(
    "delete_entities",
    "Delete entities from the knowledge graph and clean up their relations.",
    {
        "entityNames": list,  # [string]
    },
)
async def delete_entities(args: dict[str, Any]) -> dict[str, Any]:
    names = args["entityNames"]
    await _get_store().delete_entities(names)
    return _text(f"Deleted entities: {names}")


@tool(
    "delete_observations",
    "Remove specific observations from entities.",
    {
        "deletions": list,  # [{entityName, observations[]}]
    },
)
async def delete_observations(args: dict[str, Any]) -> dict[str, Any]:
    for item in args["deletions"]:
        await _get_store().delete_observations(item["entityName"], item["observations"])
    return _text("Observations deleted.")


@tool(
    "delete_relations",
    "Remove specific relations from the knowledge graph.",
    {
        "relations": list,  # [{from, to, relationType}]
    },
)
async def delete_relations(args: dict[str, Any]) -> dict[str, Any]:
    relations = [
        Relation(
            from_entity=r["from"],
            to_entity=r["to"],
            relation_type=r["relationType"],
        )
        for r in args["relations"]
    ]
    await _get_store().delete_relations(relations)
    return _text("Relations deleted.")


@tool(
    "read_graph",
    "Load and return the entire knowledge graph (all entities and relations).",
    {},
)
async def read_graph(args: dict[str, Any]) -> dict[str, Any]:
    graph = await _get_store().read_graph()
    return _json_result(_graph_to_dict(graph))


@tool(
    "search_nodes",
    "Search the knowledge graph by name, type, or observation content.",
    {
        "query": str,
    },
)
async def search_nodes(args: dict[str, Any]) -> dict[str, Any]:
    graph = await _get_store().search_nodes(args["query"])
    return _json_result(_graph_to_dict(graph))


@tool(
    "open_nodes",
    "Load specific entities by name with their inter-relations.",
    {
        "names": list,  # [string]
    },
)
async def open_nodes(args: dict[str, Any]) -> dict[str, Any]:
    graph = await _get_store().open_nodes(args["names"])
    return _json_result(_graph_to_dict(graph))


# ---------------------------------------------------------------------------
# Episodic tools
# ---------------------------------------------------------------------------


@tool(
    "log_episode",
    "Log a timestamped episode to today's daily note. Use after every meaningful exchange.",
    {
        "title": str,
        "content": str,
        "tags": list,
    },
)
async def log_episode(args: dict[str, Any]) -> dict[str, Any]:
    episode = await _get_episodic_store().log_episode(
        title=args["title"],
        content=args["content"],
        tags=args.get("tags"),
    )
    return _text(f"Episode logged: {episode.date} {episode.time} — {episode.title}")


@tool(
    "recall_episodes",
    "Recall past episodes from the daily journal. Supports date range and text search.",
    {
        "start_date": str,
        "end_date": str,
        "query": str,
    },
)
async def recall_episodes(args: dict[str, Any]) -> dict[str, Any]:
    episodes = await _get_episodic_store().recall_episodes(
        start_date=args.get("start_date") or None,
        end_date=args.get("end_date") or None,
        query=args.get("query") or None,
    )
    if not episodes:
        return _text("No episodes found.")
    data = [
        {
            "date": ep.date,
            "time": ep.time,
            "title": ep.title,
            "content": ep.content,
            "tags": list(ep.tags),
        }
        for ep in episodes
    ]
    return _json_result(data)


# ---------------------------------------------------------------------------
# Scheduler tools
# ---------------------------------------------------------------------------


@tool(
    "schedule_task",
    "Schedule a task. Provide 'time' (ISO datetime) for one-shot or 'cron' for recurring.",
    {
        "description": str,
        "time": str,
        "cron": str,
    },
)
async def schedule_task(args: dict[str, Any]) -> dict[str, Any]:
    task = await _get_scheduled_store().create_task(
        description=args["description"],
        time=args.get("time") or None,
        cron_expr=args.get("cron") or None,
    )
    kind = "recurring" if task.recurring else "one-shot"
    return _text(f"Scheduled {kind} task {task.id}: {task.description}")


@tool(
    "list_scheduled_tasks",
    "List all pending and active scheduled tasks.",
    {},
)
async def list_scheduled_tasks(args: dict[str, Any]) -> dict[str, Any]:
    tasks = await _get_scheduled_store().list_tasks()
    if not tasks:
        return _text("No scheduled tasks.")
    data = [
        {
            "id": t.id,
            "description": t.description,
            "time": t.time,
            "recurring": t.recurring,
            "cron": t.cron,
            "status": t.status,
            "created": t.created,
            "lastRun": t.last_run,
        }
        for t in tasks
    ]
    return _json_result(data)


@tool(
    "cancel_scheduled_task",
    "Cancel and remove a scheduled task by its ID.",
    {
        "task_id": str,
    },
)
async def cancel_scheduled_task(args: dict[str, Any]) -> dict[str, Any]:
    found = await _get_scheduled_store().cancel_task(args["task_id"])
    if found:
        return _text(f"Task {args['task_id']} cancelled.")
    return _text(f"Task {args['task_id']} not found.")


# ---------------------------------------------------------------------------
# Short-term buffer tools
# ---------------------------------------------------------------------------


@tool(
    "remember",
    "Quickly note something for later. Appends a raw entry to the short-term buffer "
    "without any structure. Use liberally — the dream cycle will classify it later.",
    {
        "content": str,
        "tags": list,
    },
)
async def remember(args: dict[str, Any]) -> dict[str, Any]:
    ts = datetime.now(UTC).isoformat()
    entry = BufferEntry(
        ts=ts,
        session=f"tg-{_bot_name}",
        content=args["content"],
        tags=tuple(args.get("tags") or []),
    )
    await _get_buffer_store().append(entry)
    return _text(f"Remembered: {entry.content[:80]}")


# ---------------------------------------------------------------------------
# Inter-bot mailbox tools
# ---------------------------------------------------------------------------


@tool(
    "send_message",
    "Send a message to another bot's inbox. The message will be processed during "
    "that bot's next dream cycle.",
    {
        "bot_name": str,
        "subject": str,
        "content": str,
    },
)
async def send_message(args: dict[str, Any]) -> dict[str, Any]:
    target_name = args["bot_name"]
    registry = load_bot_registry(Path.cwd())
    if target_name not in registry:
        return _text(
            f"Bot '{target_name}' not found in bots.yaml. Available: {list(registry.keys())}"
        )
    target_vault = registry[target_name]
    ts = datetime.now(UTC).isoformat()
    await _get_mailbox_store().send_message(
        target_vault=target_vault,
        from_bot=_bot_name,
        subject=args["subject"],
        content=args["content"],
        ts=ts,
    )
    return _text(f"Message sent to {target_name}: {args['subject']}")


@tool(
    "read_inbox",
    "Read all messages in this bot's inbox.",
    {},
)
async def read_inbox(args: dict[str, Any]) -> dict[str, Any]:
    messages = await _get_mailbox_store().read_inbox()
    if not messages:
        return _text("Inbox is empty.")
    data = [
        {
            "from": m.from_bot,
            "ts": m.ts,
            "subject": m.subject,
            "content": m.content,
        }
        for m in messages
    ]
    return _json_result(data)


# ---------------------------------------------------------------------------
# Serialisation helper
# ---------------------------------------------------------------------------


def _graph_to_dict(graph: Any) -> dict[str, Any]:
    return {
        "entities": [
            {
                "name": e.name,
                "entityType": e.entity_type,
                "observations": list(e.observations),
            }
            for e in graph.entities
        ],
        "relations": [
            {
                "from": r.from_entity,
                "to": r.to_entity,
                "relationType": r.relation_type,
            }
            for r in graph.relations
        ],
    }


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------


def create_memory_server(
    vault_path: Path,
    timezone: str = "UTC",
    bot_name: str = "alice",
) -> tuple[Any, ObsidianScheduledStore, ObsidianBufferStore]:
    """Create the MCP server and return it with the scheduled and buffer stores."""
    global _store, _episodic_store, _scheduled_store, _buffer_store, _mailbox_store, _bot_name
    _bot_name = bot_name
    _store = ObsidianSemanticStore(vault_path)
    _episodic_store = ObsidianEpisodicStore(vault_path)
    _scheduled_store = ObsidianScheduledStore(vault_path, timezone)
    _buffer_store = ObsidianBufferStore(vault_path)
    _mailbox_store = ObsidianMailboxStore(vault_path, bot_name)

    server = create_sdk_mcp_server(
        name="hippo-memory",
        version="0.4.0",
        tools=[
            create_entities,
            create_relations,
            add_observations,
            delete_entities,
            delete_observations,
            delete_relations,
            read_graph,
            search_nodes,
            open_nodes,
            log_episode,
            recall_episodes,
            schedule_task,
            list_scheduled_tasks,
            cancel_scheduled_task,
            remember,
            send_message,
            read_inbox,
        ],
    )
    return server, _scheduled_store, _buffer_store


def create_dream_server() -> Any:
    """Create a subset MCP server for the dream sub-agent.

    Requires create_memory_server() to have been called first.
    Exposes only semantic, episodic, and read_inbox tools — not
    the scheduler, remember, or send_message tools.
    """
    return create_sdk_mcp_server(
        name="hippo-dream",
        version="0.4.0",
        tools=[
            create_entities,
            create_relations,
            add_observations,
            delete_entities,
            delete_observations,
            delete_relations,
            read_graph,
            search_nodes,
            open_nodes,
            log_episode,
            recall_episodes,
            read_inbox,
        ],
    )
