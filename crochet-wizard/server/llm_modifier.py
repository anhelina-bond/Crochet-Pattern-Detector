import asyncio
import json
import math
import os
from statistics import median
from typing import Any, Optional

from pydantic import BaseModel, Field, ValidationError


VALID_STITCH_TYPES = {
    "sc_stitch",
    "dc_stitch",
    "hdc_stitch",
    "tr_stitch",
    "ch_stitch",
    "sl_st",
    "sc",
    "dc",
    "hdc",
    "tr",
    "ch",
}


class NodeModel(BaseModel):
    id: int
    x: float
    y: float
    w: float = 0.08
    h: float = 0.08
    type: str
    angle: float = 0.0


class EdgeModel(BaseModel):
    child_id: int
    parent_id: int
    connection_type: str = "standard"


class FullGraph(BaseModel):
    nodes: list[NodeModel] = Field(default_factory=list)
    edges: list[EdgeModel] = Field(default_factory=list)


class OperationPlan(BaseModel):
    operations: list[dict[str, Any]] = Field(default_factory=list)


OPERATION_SYSTEM_PROMPT = """\
You are a crochet graph editing planner. Convert the user's request into JSON edit operations.

Important:
- Do not return the final graph.
- Return ONLY valid JSON with this exact top-level shape: {"operations": [...]}.
- Use the graph context to choose selectors and placement, not raw guessing.
- Prefer high-level selectors instead of listing every id when possible.
- Use only these operation names:
  1. set_type
  2. add_relative_nodes
  3. delete_nodes
  4. move_nodes
  5. connect_nodes
  6. disconnect_edges

Selectors:
- {"scope":"all"}
- {"row":"top"} or {"row":"bottom"} or {"row":0}
- {"type":"sc_stitch"}
- {"ids":[0,1,2]}
- Selectors can combine row and type.

CRITICAL GEOMETRY RULES (Adding vs. Extending):
1. ROW ADDITION (Building Up/Down): To add a completely new row, select the ENTIRE existing row as the anchor (e.g., {"row": "top"}). Set "placement" to "above" or "below", and use "count": 1. 
2. ROW EXTENSION (Making a row wider): To make an existing row longer horizontally, DO NOT select the whole row. Select ONLY the single node at the edge (e.g., the rightmost or leftmost node ID from the context). Set "placement" to "right" or "left", set the "count" to however many stitches to add, and set "distribution" to "horizontal_spread".

Placement & Distribution parameters:
- placement: "above", "below", "left", or "right".
- distribution: "vertical_stack", "horizontal_spread", or "grid".
- "vertical_stack" keeps each new stitch on the same x-axis as its parent and places repeated stitches on distinct y rows.
- "horizontal_spread" keeps repeated stitches on one y row and separates them along the x-axis.
- spread is a multiplier of normal stitch width/height. Use 1.0 for standard spacing.
- connect_to_anchor defaults to true.

Operation examples:
- {"operation":"set_type","selector":{"scope":"all"},"stitch_type":"dc_stitch"}
- {"operation":"add_relative_nodes","selector":{"ids":[14]},"count":3,"stitch_type":"sc_stitch","placement":"right","distribution":"horizontal_spread","spread":1.0}
"""


def _model_validate(model_type: type[BaseModel], value: Any) -> BaseModel:
    if hasattr(model_type, "model_validate"):
        return model_type.model_validate(value)
    return model_type.parse_obj(value)


def _model_validate_json(model_type: type[BaseModel], value: str) -> BaseModel:
    if hasattr(model_type, "model_validate_json"):
        return model_type.model_validate_json(value)
    return model_type.parse_raw(value)


def _model_dump(model: BaseModel) -> dict[str, Any]:
    if hasattr(model, "model_dump"):
        return model.model_dump()
    return model.dict()


def _model_dump_json(model: BaseModel) -> str:
    if hasattr(model, "model_dump_json"):
        return model.model_dump_json()
    return model.json()


def _percentile(values: list[float], percentile: float) -> float:
    if not values:
        return 0.0

    ordered = sorted(values)
    index = min(len(ordered) - 1, max(0, round((len(ordered) - 1) * percentile)))
    return ordered[index]


def _safe_median(values: list[float], fallback: float) -> float:
    cleaned = [value for value in values if value > 0]
    return median(cleaned) if cleaned else fallback


def _clamp(value: float, min_value: float = 0.0, max_value: float = 1.0) -> float:
    return max(min_value, min(max_value, value))


def validate_graph(graph_data: dict[str, Any]) -> FullGraph:
    try:
        return _model_validate(FullGraph, graph_data)  # type: ignore[return-value]
    except ValidationError as exc:
        raise ValueError(f"Graph data does not match the required schema: {exc}") from exc


def analyze_graph(graph: FullGraph) -> dict[str, Any]:
    nodes = graph.nodes
    if not nodes:
        return {
            "node_count": 0,
            "edge_count": len(graph.edges),
            "rows": [],
            "metrics": {
                "median_width": 0.08,
                "median_height": 0.08,
                "horizontal_spacing": 0.08,
                "vertical_spacing": 0.1,
                "row_threshold": 0.05,
            },
            "types": [],
        }

    widths = [node.w for node in nodes]
    heights = [node.h for node in nodes]
    xs = sorted(node.x for node in nodes)
    ys = sorted(node.y for node in nodes)
    x_gaps = [right - left for left, right in zip(xs, xs[1:]) if right - left > 0.002]
    y_gaps = [bottom - top for top, bottom in zip(ys, ys[1:]) if bottom - top > 0.002]
    median_width = _safe_median(widths, 0.08)
    median_height = _safe_median(heights, 0.08)
    horizontal_spacing = max(median_width * 0.9, _safe_median(x_gaps, median_width))
    vertical_spacing = max(median_height * 1.05, _percentile(y_gaps, 0.85), 0.08)
    row_threshold = max(median_height * 0.7, min(vertical_spacing * 0.65, 0.12), 0.035)

    rows: list[list[NodeModel]] = []
    for node in sorted(nodes, key=lambda item: (item.y, item.x)):
        if not rows:
            rows.append([node])
            continue

        row_center = median([row_node.y for row_node in rows[-1]])
        if abs(node.y - row_center) <= row_threshold:
            rows[-1].append(node)
        else:
            rows.append([node])

    row_summaries = []
    for index, row_nodes in enumerate(rows):
        row_nodes = sorted(row_nodes, key=lambda item: item.x)
        row_summaries.append(
            {
                "index": index,
                "label": "top" if index == 0 else "bottom" if index == len(rows) - 1 else f"row_{index}",
                "ids": [node.id for node in row_nodes],
                "count": len(row_nodes),
                "min_x": round(min(node.x for node in row_nodes), 4),
                "max_x": round(max(node.x for node in row_nodes), 4),
                "center_y": round(median([node.y for node in row_nodes]), 4),
            }
        )

    return {
        "node_count": len(nodes),
        "edge_count": len(graph.edges),
        "rows": row_summaries,
        "metrics": {
            "median_width": round(median_width, 4),
            "median_height": round(median_height, 4),
            "horizontal_spacing": round(horizontal_spacing, 4),
            "vertical_spacing": round(vertical_spacing, 4),
            "row_threshold": round(row_threshold, 4),
        },
        "types": sorted({node.type for node in nodes}),
    }


def normalize_graph_for_mobile(graph: FullGraph) -> FullGraph:
    return repair_graph(graph)


def repair_graph(graph: FullGraph) -> FullGraph:
    nodes = [_model_dump(node) for node in graph.nodes]
    edges = [_model_dump(edge) for edge in graph.edges]

    for node in nodes:
        node["x"] = float(node.get("x", 0.5))
        node["y"] = float(node.get("y", 0.5))
        node["w"] = max(0.01, min(1.0, float(node.get("w", 0.08))))
        node["h"] = max(0.01, min(1.0, float(node.get("h", 0.08))))
        node["angle"] = float(node.get("angle", 0.0) or 0.0)

    _fit_axis(nodes, "x")
    _fit_axis(nodes, "y")
    _nudge_overlapping_nodes(nodes)
    _fit_axis(nodes, "x")
    _fit_axis(nodes, "y")
    _nudge_overlapping_nodes(nodes)

    id_map = {node["id"]: index for index, node in enumerate(nodes)}
    for index, node in enumerate(nodes):
        node["id"] = index

    seen_edges = set()
    normalized_edges = []
    for edge in edges:
        child_id = edge.get("child_id")
        parent_id = edge.get("parent_id")
        if child_id not in id_map or parent_id not in id_map:
            continue

        child_index = id_map[child_id]
        parent_index = id_map[parent_id]
        edge_key = (child_index, parent_index)
        if child_index == parent_index or edge_key in seen_edges:
            continue

        seen_edges.add(edge_key)
        normalized_edges.append(
            {
                "child_id": child_index,
                "parent_id": parent_index,
                "connection_type": edge.get("connection_type") or "standard",
            }
        )

    _recalculate_angles(nodes, normalized_edges)
    return validate_graph({"nodes": nodes, "edges": normalized_edges})


def execute_operations(graph: FullGraph, operations: list[dict[str, Any]]) -> FullGraph:
    working_graph = repair_graph(graph)
    analysis = analyze_graph(working_graph)
    nodes = [_model_dump(node) for node in working_graph.nodes]
    edges = [_model_dump(edge) for edge in working_graph.edges]

    for operation in operations:
        op_name = str(operation.get("operation", "")).strip().lower()
        selector = operation.get("selector") or {"scope": "all"}

        if op_name == "set_type":
            stitch_type = _normalize_stitch_type(
                operation.get("stitch_type") or operation.get("node_type") or operation.get("type")
            )
            for node_id in _select_node_ids(nodes, selector, analysis):
                nodes[node_id]["type"] = stitch_type

        elif op_name == "add_relative_nodes":
            anchors = _select_node_ids(nodes, selector, analysis)
            _add_relative_nodes(nodes, edges, anchors, operation, analysis)

        elif op_name == "delete_nodes":
            delete_ids = set(_select_node_ids(nodes, selector, analysis))
            nodes = [node for node in nodes if node["id"] not in delete_ids]
            edges = [
                edge
                for edge in edges
                if edge.get("child_id") not in delete_ids and edge.get("parent_id") not in delete_ids
            ]

        elif op_name == "move_nodes":
            dx = float(operation.get("dx") or 0.0)
            dy = float(operation.get("dy") or 0.0)
            for node_id in _select_node_ids(nodes, selector, analysis):
                nodes[node_id]["x"] += dx
                nodes[node_id]["y"] += dy

        elif op_name == "connect_nodes":
            _connect_nodes(nodes, edges, operation, analysis)

        elif op_name == "disconnect_edges":
            edges = _disconnect_edges(nodes, edges, operation, analysis)

        repaired_graph = repair_graph(validate_graph({"nodes": nodes, "edges": edges}))
        nodes = [_model_dump(node) for node in repaired_graph.nodes]
        edges = [_model_dump(edge) for edge in repaired_graph.edges]
        analysis = analyze_graph(repaired_graph)

    return repair_graph(validate_graph({"nodes": nodes, "edges": edges}))


def _fit_axis(nodes: list[dict[str, Any]], axis: str) -> None:
    if not nodes:
        return

    margin = 0.03
    values = [node[axis] for node in nodes]
    min_value = min(values)
    max_value = max(values)
    span = max_value - min_value

    if span > 1.0 - (margin * 2):
        scale = (1.0 - (margin * 2)) / span
        for node in nodes:
            node[axis] = margin + ((node[axis] - min_value) * scale)
    else:
        shift = 0.0
        if min_value < margin:
            shift = margin - min_value
        if max_value + shift > 1.0 - margin:
            shift = (1.0 - margin) - max_value
        for node in nodes:
            node[axis] = _clamp(node[axis] + shift, margin, 1.0 - margin)


def _nudge_overlapping_nodes(nodes: list[dict[str, Any]]) -> None:
    if not nodes:
        return

    median_height = _safe_median([node.get("h", 0.08) for node in nodes], 0.08)
    vertical_step = max(median_height * 1.1, 0.035)
    occupied: dict[tuple[int, int], int] = {}
    for node in nodes:
        key = (round(node["x"] / 0.012), round(node["y"] / 0.012))
        collision_index = occupied.get(key, 0)
        if collision_index:
            direction = -1 if node["y"] >= 0.5 else 1
            node["y"] += direction * vertical_step * collision_index
        occupied[key] = collision_index + 1


def _recalculate_angles(nodes: list[dict[str, Any]], edges: list[dict[str, Any]]) -> None:
    parent_by_child: dict[int, int] = {}
    for edge in edges:
        parent_by_child.setdefault(edge["child_id"], edge["parent_id"])

    for child_id, parent_id in parent_by_child.items():
        child = nodes[child_id]
        parent = nodes[parent_id]
        dx = child["x"] - parent["x"]
        dy = child["y"] - parent["y"]
        if abs(dy) < 0.03:
            child["angle"] = 0.0
            continue

        child["angle"] = round(math.degrees(math.atan2(dy, dx)) + 90, 2)


def _normalize_stitch_type(stitch_type: Any) -> str:
    value = str(stitch_type or "sc_stitch").strip().lower()
    aliases = {"sc": "sc_stitch", "dc": "dc_stitch", "hdc": "hdc_stitch", "tr": "tr_stitch", "ch": "ch_stitch"}
    value = aliases.get(value, value)
    if value not in VALID_STITCH_TYPES:
        raise ValueError(f"Unsupported stitch type: {stitch_type}")
    return value


def _select_node_ids(nodes: list[dict[str, Any]], selector: dict[str, Any], analysis: dict[str, Any]) -> list[int]:
    if not selector or selector.get("scope") == "all" or selector.get("all") is True:
        selected = {node["id"] for node in nodes}
    elif selector.get("ids") is not None:
        selected = {int(node_id) for node_id in selector.get("ids", [])}
    else:
        selected = {node["id"] for node in nodes}

    if selector.get("row") is not None:
        row_value = selector.get("row")
        row_ids: set[int] = set()
        rows = analysis.get("rows", [])
        if isinstance(row_value, str):
            normalized_row = row_value.strip().lower()
            if normalized_row == "top" and rows:
                row_ids = set(rows[0]["ids"])
            elif normalized_row == "bottom" and rows:
                row_ids = set(rows[-1]["ids"])
            elif normalized_row.startswith("row_"):
                row_index = int(normalized_row.replace("row_", ""))
                row_ids = set(rows[row_index]["ids"]) if 0 <= row_index < len(rows) else set()
            elif normalized_row.isdigit():
                row_index = int(normalized_row)
                row_ids = set(rows[row_index]["ids"]) if 0 <= row_index < len(rows) else set()
        else:
            row_index = int(row_value)
            row_ids = set(rows[row_index]["ids"]) if 0 <= row_index < len(rows) else set()
        selected &= row_ids

    if selector.get("type") is not None:
        stitch_type = _normalize_stitch_type(selector.get("type"))
        selected &= {node["id"] for node in nodes if node.get("type") == stitch_type}

    return sorted(node_id for node_id in selected if 0 <= node_id < len(nodes))


def _add_relative_nodes(
    nodes: list[dict[str, Any]],
    edges: list[dict[str, Any]],
    anchors: list[int],
    operation: dict[str, Any],
    analysis: dict[str, Any],
) -> None:
    metrics = analysis["metrics"]
    count = max(1, int(operation.get("count") or operation.get("count_per_anchor") or 1))
    stitch_type = _normalize_stitch_type(operation.get("stitch_type") or operation.get("node_type") or "sc_stitch")
    placement = str(operation.get("placement") or "above").strip().lower()
    connect_to_anchor = operation.get("connect_to_anchor", True) is not False
    distribution = _infer_distribution(operation, placement)
    width = float(operation.get("w") or metrics["median_width"])
    height = float(operation.get("h") or metrics["median_height"])
    base_dx = float(operation.get("dx") or 0.0)
    base_dy = float(operation.get("dy") or 0.0)
    spread_multiplier = float(operation.get("spread") or (1.0 if count > 1 else 0.0))
    spread_step = max(metrics["horizontal_spacing"], width * 1.1) * spread_multiplier
    vertical_step = max(metrics["vertical_spacing"], height * 1.25)
    horizontal_step = max(metrics["horizontal_spacing"], width * 1.25)

    for anchor_id in anchors:
        anchor = nodes[anchor_id]
        offsets = _placement_offsets(count, placement, distribution, spread_step, vertical_step)
        for x_offset, y_offset in offsets:
            x = anchor["x"] + base_dx
            y = anchor["y"] + base_dy
            if placement == "above":
                x += x_offset
                y -= vertical_step + y_offset
            elif placement == "below":
                x += x_offset
                y += vertical_step + y_offset
            elif placement == "left":
                x -= horizontal_step
                y += y_offset
            elif placement == "right":
                x += horizontal_step
                y += y_offset
            else:
                x += x_offset
                y -= vertical_step + y_offset

            new_id = len(nodes)
            nodes.append(
                {
                    "id": new_id,
                    "x": x,
                    "y": y,
                    "w": width,
                    "h": height,
                    "type": stitch_type,
                    "angle": 0.0,
                }
            )
            if connect_to_anchor:
                edges.append({"child_id": new_id, "parent_id": anchor_id, "connection_type": "standard"})


def _centered_offsets(count: int, step: float) -> list[float]:
    if count <= 1:
        return [0.0]
    center = (count - 1) / 2
    return [(index - center) * step for index in range(count)]


def _infer_distribution(operation: dict[str, Any], placement: str) -> str:
    requested = str(operation.get("distribution") or "").strip().lower()
    if requested in {"vertical_stack", "horizontal_spread", "grid"}:
        return requested

    if operation.get("horizontal_spread") is True or operation.get("fan_out") is True:
        return "horizontal_spread"

    if placement in {"above", "below"}:
        return "vertical_stack"

    return "horizontal_spread"


def _placement_offsets(
    count: int,
    placement: str,
    distribution: str,
    horizontal_step: float,
    vertical_step: float,
) -> list[tuple[float, float]]:
    if count <= 1:
        return [(0.0, 0.0)]

    if distribution == "horizontal_spread":
        return [(offset, 0.0) for offset in _centered_offsets(count, horizontal_step)]

    if distribution == "grid":
        columns = max(2, math.ceil(math.sqrt(count)))
        rows = math.ceil(count / columns)
        offsets = []
        for index in range(count):
            column = index % columns
            row = index // columns
            x_offset = (column - ((columns - 1) / 2)) * horizontal_step
            y_offset = row * vertical_step
            offsets.append((x_offset, y_offset))
        if rows > 1 and placement in {"left", "right"}:
            return [(y_offset, x_offset) for x_offset, y_offset in offsets]
        return offsets

    if placement in {"above", "below"}:
        return [(0.0, index * vertical_step) for index in range(count)]

    return [(0.0, offset) for offset in _centered_offsets(count, vertical_step)]


def _connect_nodes(
    nodes: list[dict[str, Any]],
    edges: list[dict[str, Any]],
    operation: dict[str, Any],
    analysis: dict[str, Any],
) -> None:
    child_ids = operation.get("child_ids")
    parent_ids = operation.get("parent_ids")
    if child_ids is None:
        child_ids = _select_node_ids(nodes, operation.get("child_selector") or operation.get("selector") or {}, analysis)
    if parent_ids is None:
        if operation.get("parent_selector") is None:
            return
        parent_ids = _select_node_ids(nodes, operation.get("parent_selector") or {}, analysis)

    for child_id in child_ids:
        for parent_id in parent_ids:
            if child_id != parent_id:
                edges.append(
                    {
                        "child_id": int(child_id),
                        "parent_id": int(parent_id),
                        "connection_type": operation.get("connection_type") or "standard",
                    }
                )


def _disconnect_edges(
    nodes: list[dict[str, Any]],
    edges: list[dict[str, Any]],
    operation: dict[str, Any],
    analysis: dict[str, Any],
) -> list[dict[str, Any]]:
    child_ids = operation.get("child_ids")
    parent_ids = operation.get("parent_ids")
    if child_ids is None and operation.get("selector") is not None:
        child_ids = _select_node_ids(nodes, operation.get("selector"), analysis)

    child_set = {int(node_id) for node_id in child_ids} if child_ids is not None else None
    parent_set = {int(node_id) for node_id in parent_ids} if parent_ids is not None else None

    filtered_edges = []
    for edge in edges:
        child_matches = child_set is None or edge.get("child_id") in child_set
        parent_matches = parent_set is None or edge.get("parent_id") in parent_set
        if child_matches and parent_matches:
            continue
        filtered_edges.append(edge)
    return filtered_edges


async def apply_generative_modification(
    clean_graph: FullGraph,
    user_modification_prompt: str,
) -> FullGraph:
    api_key = os.getenv("OPENAI_API_KEY", "")
    model = os.getenv("OPENAI_MODEL", "gpt-4o")
    max_retries = int(os.getenv("LLM_MAX_RETRIES", "3"))

    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not configured.")

    try:
        from openai import AsyncOpenAI, OpenAIError
    except ImportError as exc:
        raise RuntimeError("OpenAI Python package is not installed.") from exc

    openai_client = AsyncOpenAI(api_key=api_key)
    base_graph = repair_graph(clean_graph)
    graph_context = analyze_graph(base_graph)
    graph_payload = _model_dump_json(base_graph)
    last_exc: Optional[Exception] = None
    diagnostics = ""

    for attempt in range(1, max_retries + 1):
        try:
            plan = await _request_operation_plan(
                openai_client,
                model,
                graph_context,
                graph_payload,
                user_modification_prompt,
                diagnostics,
            )
            return execute_operations(base_graph, plan.operations)
        except OpenAIError as exc:
            last_exc = exc
        except (ValidationError, json.JSONDecodeError, ValueError, KeyError, TypeError) as exc:
            last_exc = exc
            diagnostics = f"Previous operation plan failed: {exc}. Return corrected operations only."

        await asyncio.sleep(1.5 * attempt)

    try:
        return await _request_direct_graph_fallback(openai_client, model, base_graph, user_modification_prompt)
    except Exception as exc:
        raise RuntimeError(f"Generative modifier failed. Last operation error: {last_exc}. Fallback error: {exc}") from exc


async def _request_operation_plan(
    openai_client: Any,
    model: str,
    graph_context: dict[str, Any],
    graph_payload: str,
    user_modification_prompt: str,
    diagnostics: str,
) -> OperationPlan:
    user_message = (
        f"Graph context:\n{json.dumps(graph_context, indent=2)}\n\n"
        f"Graph JSON:\n{graph_payload}\n\n"
        f"Modification instruction: {user_modification_prompt}\n\n"
        f"{diagnostics}"
    )
    completion = await openai_client.chat.completions.create(
        model=model,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": OPERATION_SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
        ],
        temperature=0.1,
    )
    raw_text = completion.choices[0].message.content or ""
    return _model_validate_json(OperationPlan, raw_text)  # type: ignore[return-value]


async def _request_direct_graph_fallback(
    openai_client: Any,
    model: str,
    graph: FullGraph,
    user_modification_prompt: str,
) -> FullGraph:
    user_message = f"Graph JSON:\n{_model_dump_json(graph)}\n\nModification instruction: {user_modification_prompt}"
    completion = await openai_client.chat.completions.create(
        model=model,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": DIRECT_GRAPH_SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
        ],
        temperature=0.1,
    )
    raw_text = completion.choices[0].message.content or ""
    modified_graph = _model_validate_json(FullGraph, raw_text)
    return repair_graph(modified_graph)  # type: ignore[arg-type]
