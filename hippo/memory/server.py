"""MCP server exposing the semantic memory tools to the Claude Agent SDK."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from claude_agent_sdk import create_sdk_mcp_server, tool

from hippo.memory.semantic import ObsidianSemanticStore
from hippo.memory.types import Entity, Relation

# Module-level store, set by create_memory_server()
_store: ObsidianSemanticStore | None = None


def _get_store() -> ObsidianSemanticStore:
    if _store is None:
        msg = "Memory server not initialized — call create_memory_server() first"
        raise RuntimeError(msg)
    return _store


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


def create_memory_server(vault_path: Path) -> Any:
    """Create and return the MCP server with all memory tools wired up."""
    global _store
    _store = ObsidianSemanticStore(vault_path)

    return create_sdk_mcp_server(
        name="hippo-memory",
        version="0.1.0",
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
        ],
    )
