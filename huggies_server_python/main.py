"""Huggies demo MCP server implemented with the Python FastMCP helper.

The server exposes widget-backed tools that render the Huggies UI bundle.
Each handler returns the HTML shell via an MCP resource and echoes structured
content so the ChatGPT client can hydrate the widget.
"""

from __future__ import annotations

import json
import random
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Optional

import mcp.types as types
from mcp.server.fastmcp import FastMCP
from mcp.server.transport_security import TransportSecuritySettings


@dataclass(frozen=True)
class HuggiesWidget:
    identifier: str
    title: str
    template_uri: str
    invoking: str
    invoked: str
    html: str
    response_text: str


ASSETS_DIR = Path(__file__).resolve().parent.parent / "assets"
MOCK_KNOWLEDGE_FILE = Path(__file__).resolve().parent / "mock_knowledge.json"

# Load knowledge base
if not MOCK_KNOWLEDGE_FILE.exists():
    raise FileNotFoundError(f"Mock knowledge file not found at: {MOCK_KNOWLEDGE_FILE}")

with MOCK_KNOWLEDGE_FILE.open("r", encoding="utf-8") as f:
    KNOWLEDGE: List[Dict[str, Any]] = json.load(f)


def find_by_id(item_id: str) -> Optional[Dict[str, Any]]:
    """Find a knowledge item by ID."""
    for item in KNOWLEDGE:
        if item.get("id") == item_id:
            return item
    return None


def keyword_search(query: str, top_n: int = 3) -> List[Dict[str, Any]]:
    """Search knowledge base by keywords."""
    q = query.lower()
    hits: List[tuple[int, Dict[str, Any]]] = []
    for item in KNOWLEDGE:
        score = 0
        if q in item.get("title", "").lower():
            score += 5
        if q in item.get("question", "").lower():
            score += 4
        for tag in item.get("tags", []):
            if tag.lower() in q:
                score += 3
        ans = item.get("answer", "").lower()
        for w in q.split():
            if w and w in ans:
                score += 1
        if score > 0:
            hits.append((score, item))

    hits.sort(key=lambda x: x[0], reverse=True)
    return [h[1] for h in hits][:top_n]


@lru_cache(maxsize=None)
def _load_widget_html(component_name: str) -> str:
    html_path = ASSETS_DIR / f"{component_name}.html"
    if html_path.exists():
        return html_path.read_text(encoding="utf8")

    fallback_candidates = sorted(ASSETS_DIR.glob(f"{component_name}-*.html"))
    if fallback_candidates:
        return fallback_candidates[-1].read_text(encoding="utf8")

    raise FileNotFoundError(
        f'Widget HTML for "{component_name}" not found in {ASSETS_DIR}. '
        "Run `pnpm run build` to generate the assets before starting the server."
    )


# NOTE: assuming a single Huggies HTML shell called "huggies.html".
# If your built file has a different name, change "huggies" below.
widgets: List[HuggiesWidget] = [
    HuggiesWidget(
        identifier="huggies-cards",
        title="Show FAQ Cards",
        template_uri="ui://widget/huggies-cards.html",
        invoking="Searching FAQs",
        invoked="Found FAQ results",
        html=_load_widget_html("huggies-cards"),
        response_text="Displayed FAQ cards!",
    ),
    HuggiesWidget(
        identifier="huggies-size-calc",
        title="Diaper Size Calculator",
        template_uri="ui://widget/huggies-size-calc.html",
        invoking="Calculating diaper size",
        invoked="Size recommendation ready",
        html=_load_widget_html("huggies-size-calc"),
        response_text="Calculated diaper size!",
    ),
    HuggiesWidget(
        identifier="huggies-map",
        title="Store Locator Map",
        template_uri="ui://widget/huggies-map.html",
        invoking="Finding nearby stores",
        invoked="Store locations found",
        html=_load_widget_html("huggies-map"),
        response_text="Displayed store map!",
    ),
    HuggiesWidget(
        identifier="huggies-offers",
        title="Coupons & Offers",
        template_uri="ui://widget/huggies-offers.html",
        invoking="Loading current offers",
        invoked="Offers displayed",
        html=_load_widget_html("huggies-offers"),
        response_text="Showed available offers!",
    ),
    HuggiesWidget(
        identifier="huggies-names",
        title="Baby Name Suggestions",
        template_uri="ui://widget/huggies-names.html",
        invoking="Generating name suggestions",
        invoked="Name suggestions ready",
        html=_load_widget_html("huggies-names"),
        response_text="Displayed name suggestions!",
    ),
    HuggiesWidget(
        identifier="huggies-gender",
        title="Gender Predictor",
        template_uri="ui://widget/huggies-gender.html",
        invoking="Predicting gender",
        invoked="Prediction complete",
        html=_load_widget_html("huggies-gender"),
        response_text="Showed gender prediction!",
    ),
]


MIME_TYPE = "text/html+skybridge"

WIDGETS_BY_ID: Dict[str, HuggiesWidget] = {
    widget.identifier: widget for widget in widgets
}
WIDGETS_BY_URI: Dict[str, HuggiesWidget] = {
    widget.template_uri: widget for widget in widgets
}

mcp = FastMCP(
    name="huggies-python",
    stateless_http=True,
    transport_security=TransportSecuritySettings(
        enable_dns_rebinding_protection=False,  # dev only
    ),
)


def _resource_description(widget: HuggiesWidget) -> str:
    return f"{widget.title} widget markup"


def _tool_meta(widget: HuggiesWidget) -> Dict[str, Any]:
    return {
        "openai/outputTemplate": widget.template_uri,
        "openai/toolInvocation/invoking": widget.invoking,
        "openai/toolInvocation/invoked": widget.invoked,
        "openai/widgetAccessible": True,
        "openai/resultCanProduceWidget": True,
    }


def _tool_invocation_meta(widget: HuggiesWidget) -> Dict[str, Any]:
    return {
        "openai/toolInvocation/invoking": widget.invoking,
        "openai/toolInvocation/invoked": widget.invoked,
    }


# Map tool names to their functions (populated after function definitions)
_TOOL_FUNCTIONS: Dict[str, Any] = {
    "get_faq": None,
    "list_faqs": None,
    "get_item_by_id": None,
    "diaper_size_calc": None,
    "map_widget": None,
    "coupons": None,
    "suggest_names": None,
    "predict_gender": None,
}


def _build_tool_schema(func) -> Dict[str, Any]:
    """Build input schema from function signature."""
    import inspect

    sig = inspect.signature(func)
    properties: Dict[str, Any] = {}
    required: List[str] = []

    for param_name, param in sig.parameters.items():
        param_type = "string"
        if param.annotation != inspect.Parameter.empty:
            ann_str = str(param.annotation)
            if "int" in ann_str or "float" in ann_str:
                param_type = "number"
            elif "bool" in ann_str:
                param_type = "boolean"

        properties[param_name] = {
            "type": param_type,
            "description": param_name,
        }

        if param.default == inspect.Parameter.empty:
            required.append(param_name)

    return {
        "type": "object",
        "properties": properties,
        "required": required,
        "additionalProperties": False,
    }


@mcp._mcp_server.list_tools()
async def _list_tools() -> List[types.Tool]:
    # Map tools to their corresponding widgets
    tool_to_widget = {
        "get_faq": "huggies-cards",
        "list_faqs": "huggies-cards",
        "get_item_by_id": "huggies-cards",
        "diaper_size_calc": "huggies-size-calc",
        "map_widget": "huggies-map",
        "coupons": "huggies-offers",
        "suggest_names": "huggies-names",
        "predict_gender": "huggies-gender",
    }

    tools: List[types.Tool] = []

    for tool_name, tool_func in _TOOL_FUNCTIONS.items():
        if tool_func is None:
            continue

        widget_id = tool_to_widget.get(tool_name)
        widget = WIDGETS_BY_ID.get(widget_id) if widget_id else widgets[0]

        doc = tool_func.__doc__ or tool_name
        title = doc.split("\n")[0].strip() if doc else tool_name

        tools.append(
            types.Tool(
                name=tool_name,
                title=title,
                description=doc,
                inputSchema=_build_tool_schema(tool_func),
                _meta=_tool_meta(widget),
                annotations={
                    "destructiveHint": False,
                    "openWorldHint": False,
                    "readOnlyHint": True,
                },
            )
        )

    return tools


@mcp._mcp_server.list_resources()
async def _list_resources() -> List[types.Resource]:
    return [
        types.Resource(
            name=widget.title,
            title=widget.title,
            uri=widget.template_uri,
            description=_resource_description(widget),
            mimeType=MIME_TYPE,
            _meta=_tool_meta(widget),
        )
        for widget in widgets
    ]


@mcp._mcp_server.list_resource_templates()
async def _list_resource_templates() -> List[types.ResourceTemplate]:
    return [
        types.ResourceTemplate(
            name=widget.title,
            title=widget.title,
            uriTemplate=widget.template_uri,
            description=_resource_description(widget),
            mimeType=MIME_TYPE,
            _meta=_tool_meta(widget),
        )
        for widget in widgets
    ]


async def _handle_read_resource(req: types.ReadResourceRequest) -> types.ServerResult:
    widget = WIDGETS_BY_URI.get(str(req.params.uri))
    if widget is None:
        return types.ServerResult(
            types.ReadResourceResult(
                contents=[],
                _meta={"error": f"Unknown resource: {req.params.uri}"},
            )
        )

    contents = [
        types.TextResourceContents(
            uri=widget.template_uri,
            mimeType=MIME_TYPE,
            text=widget.html,
            _meta=_tool_meta(widget),
        )
    ]

    return types.ServerResult(types.ReadResourceResult(contents=contents))


# ----------------------
# Tool implementations
# ----------------------


@mcp.tool()
def get_faq(query: str) -> types.CallToolResult:
    """Search FAQs and return results with widget cards."""
    widget = WIDGETS_BY_ID["huggies-cards"]
    q = (query or "").strip()
    if not q:
        text = "Query is required"
        meta = _tool_invocation_meta(widget)
        return types.CallToolResult(
            content=[types.TextContent(type="text", text=text)],
            structuredContent={
                "text": text,
                "results": [],
                "widget": {
                    "widget_type": "cards",
                    "cards": [],
                },
            },
            _meta=meta,
        )

    try:
        matches = keyword_search(q, top_n=3)
    except Exception:
        matches = []

    if not matches:
        matches = KNOWLEDGE[:3]

    results: List[Dict[str, Any]] = [
        {
            "id": m.get("id"),
            "title": m.get("title"),
            "answer": m.get("answer"),
            "source_url": m.get("source_url"),
            "type": m.get("type"),
            "tags": m.get("tags", []),
        }
        for m in matches
    ]

    if results:
        top = results[0]
        text = f"{top['title']}: {top['answer']}"
    else:
        text = f'No matching FAQ found for "{q}".'

    cards = [
        {
            "type": "card",
            "title": r.get("title", ""),
            "text": r.get("answer", ""),
            "meta": {"id": r.get("id", ""), "source_url": r.get("source_url", "")},
        }
        for r in results
    ]

    meta = _tool_invocation_meta(widget)

    return types.CallToolResult(
        content=[types.TextContent(type="text", text=text)],
        structuredContent={
            "text": text,
            "results": results,
            "widget": {
                "widget_type": "cards",
                "cards": cards,
            },
        },
        _meta=meta,
    )


@mcp.tool()
def list_faqs() -> types.CallToolResult:
    """List all available FAQs."""
    widget = WIDGETS_BY_ID["huggies-cards"]
    items = [
        {"id": it.get("id"), "title": it.get("title"), "type": it.get("type")}
        for it in KNOWLEDGE
    ]
    text = f"{len(items)} FAQs available."
    meta = _tool_invocation_meta(widget)
    return types.CallToolResult(
        content=[types.TextContent(type="text", text=text)],
        structuredContent={"text": text, "results": items},
        _meta=meta,
    )


@mcp.tool()
def get_item_by_id(item_id: str) -> types.CallToolResult:
    """Get a specific FAQ item by ID."""
    widget = WIDGETS_BY_ID["huggies-cards"]
    item = find_by_id(item_id)
    if not item:
        text = f"Item with id={item_id} not found"
        meta = _tool_invocation_meta(widget)
        return types.CallToolResult(
            content=[types.TextContent(type="text", text=text)],
            structuredContent={"text": text, "error": text},
            isError=True,
            _meta=meta,
        )

    text = f"{item.get('title')}: {item.get('answer', '')[:300]}..."
    meta = _tool_invocation_meta(widget)
    return types.CallToolResult(
        content=[types.TextContent(type="text", text=text)],
        structuredContent={"text": text, "item": item},
        _meta=meta,
    )


@mcp.tool()
def diaper_size_calc(
    weight_kg: Optional[float] = None,
    weight_lb: Optional[float] = None,
) -> types.CallToolResult:
    """Calculate recommended diaper size based on baby's weight."""
    widget = WIDGETS_BY_ID["huggies-size-calc"]
    if weight_kg is None and weight_lb is None:
        text = "Please provide weight_kg or weight_lb."
        meta = _tool_invocation_meta(widget)
        return types.CallToolResult(
            content=[types.TextContent(type="text", text=text)],
            structuredContent={"text": text, "error": text},
            isError=True,
            _meta=meta,
        )

    if weight_lb is None and weight_kg is not None:
        weight_lb = float(weight_kg) * 2.2046226218

    w = float(weight_lb)

    if w <= 10:
        size, range_desc = "N (Newborn)", "up to 10 lbs"
    elif 8 <= w <= 14:
        size, range_desc = "1", "8–14 lbs"
    elif 12 <= w <= 18:
        size, range_desc = "2", "12–18 lbs"
    elif 16 <= w <= 28:
        size, range_desc = "3", "16–28 lbs"
    elif 22 <= w <= 37:
        size, range_desc = "4", "22–37 lbs"
    elif 27 <= w <= 40:
        size, range_desc = "5", "27+ lbs (varies by product)"
    else:
        size, range_desc = "6", "35+ lbs"

    advice = (
        "If you see red marks around the legs, frequent leaks, or difficulty "
        "closing tabs, consider sizing up."
    )
    text = f"For approx {round(w, 2)} lbs, recommended size: {size} ({range_desc}). {advice}"

    backend = {
        "weight_lb": round(w, 2),
        "recommended_size": size,
        "weight_range_description": range_desc,
        "advice": advice,
    }
    meta = _tool_invocation_meta(widget)

    return types.CallToolResult(
        content=[types.TextContent(type="text", text=text)],
        structuredContent={
            "text": text,
            "backend": backend,
            "widget": {
                "widget_type": "info_card",
                "data": backend,
            },
        },
        _meta=meta,
    )


@mcp.tool()
def map_widget(
    zip_code: Optional[str] = None,
    location: Optional[str] = None,
    limit: int = 5,
) -> types.CallToolResult:
    """Find retailers near a location and display on a map."""
    widget = WIDGETS_BY_ID["huggies-map"]
    base_lat, base_lon = 28.65195, 77.23149
    example_retailers = [
        {"name": "Target", "address": "123 Main St", "distance_miles": 1.2},
        {"name": "Walmart", "address": "456 Market Ave", "distance_miles": 2.1},
        {
            "name": "Amazon Pickup Point",
            "address": "789 Commerce Rd",
            "distance_miles": 3.8,
        },
        {"name": "Local Pharmacy", "address": "12 Pharmacy Ln", "distance_miles": 0.6},
        {"name": "Costco", "address": "55 Warehouse Dr", "distance_miles": 4.5},
    ]

    results: List[Dict[str, Any]] = []
    for i, r in enumerate(example_retailers[:limit]):
        lat = base_lat + (random.random() - 0.5) * 0.02 * (i + 1)
        lon = base_lon + (random.random() - 0.5) * 0.02 * (i + 1)
        results.append(
            {
                "name": r["name"],
                "address": r["address"],
                "zip": zip_code or "00000",
                "distance_miles": r["distance_miles"],
                "lat": round(lat, 6),
                "lon": round(lon, 6),
                "phone": "1800-555-0123",
            }
        )

    place = zip_code or location or "your area"
    text = f"Found {len(results)} retailers near {place}."

    backend = {"results": results}
    meta = _tool_invocation_meta(widget)

    return types.CallToolResult(
        content=[types.TextContent(type="text", text=text)],
        structuredContent={
            "text": text,
            "backend": backend,
            "widget": {
                "widget_type": "map",
                "markers": results,
            },
        },
        _meta=meta,
    )


@mcp.tool()
def coupons() -> types.CallToolResult:
    """Get current Huggies coupons and offers."""
    widget = WIDGETS_BY_ID["huggies-offers"]
    offers = [
        {
            "id": "offer-001",
            "title": "Save $2 on Huggies Special Delivery",
            "type": "manufacturer_coupon",
            "expires": "2026-01-31",
            "source_url": "https://www.huggies.com/en-us/offers",
        },
        {
            "id": "offer-002",
            "title": "Subscribe & Save 10% on monthly diaper delivery",
            "type": "subscribe",
            "expires": None,
            "source_url": "https://www.retailer.example/subscribe",
        },
    ]
    text = f"{len(offers)} current offers available."
    backend = {"offers": offers}
    meta = _tool_invocation_meta(widget)

    return types.CallToolResult(
        content=[types.TextContent(type="text", text=text)],
        structuredContent={
            "text": text,
            "backend": backend,
            "widget": {
                "widget_type": "offers_list",
                "offers": offers,
            },
        },
        _meta=meta,
    )


@mcp.tool()
def suggest_names(
    prefix: Optional[str] = None, count: int = 10
) -> types.CallToolResult:
    """Suggest unique baby names."""
    widget = WIDGETS_BY_ID["huggies-names"]
    base_names = [
        "Aria",
        "Elowen",
        "Kaia",
        "Soren",
        "Zavian",
        "Lumi",
        "Aerin",
        "Mylo",
        "Renley",
        "Zephyr",
        "Mira",
        "Caspian",
        "Nova",
        "Orin",
        "Junia",
    ]
    filtered = [
        n for n in base_names if not prefix or n.lower().startswith(prefix.lower())
    ][:count]
    text = f"Here are {len(filtered)} name suggestions."
    backend = {"names": filtered, "prefix": prefix, "count": count}
    meta = _tool_invocation_meta(widget)

    return types.CallToolResult(
        content=[types.TextContent(type="text", text=text)],
        structuredContent={
            "text": text,
            "backend": backend,
            "widget": {
                "widget_type": "names_list",
                "names": filtered,
            },
        },
        _meta=meta,
    )


@mcp.tool()
def predict_gender(
    due_date: Optional[str] = None,
    conception_date: Optional[str] = None,
) -> types.CallToolResult:
    """Playful gender prediction (not medical)."""
    widget = WIDGETS_BY_ID["huggies-gender"]
    prediction = "unknown"
    if due_date:
        try:
            day = int(due_date.split("-")[-1])
            prediction = "boy" if day % 2 == 1 else "girl"
        except Exception:
            prediction = "unknown"

    text = f"Playful prediction: {prediction} (not medical)."
    backend = {
        "prediction": prediction,
        "due_date": due_date,
        "conception_date": conception_date,
    }
    meta = _tool_invocation_meta(widget)

    return types.CallToolResult(
        content=[types.TextContent(type="text", text=text)],
        structuredContent={
            "text": text,
            "backend": backend,
            "widget": {
                "widget_type": "gender_predictor",
                "prediction": prediction,
            },
        },
        _meta=meta,
    )


# Register all tool functions in the map (after they're all defined)
_TOOL_FUNCTIONS.update(
    {
        "get_faq": get_faq,
        "list_faqs": list_faqs,
        "get_item_by_id": get_item_by_id,
        "diaper_size_calc": diaper_size_calc,
        "map_widget": map_widget,
        "coupons": coupons,
        "suggest_names": suggest_names,
        "predict_gender": predict_gender,
    }
)


# Override the default tool handler to use our widget structure
async def _call_tool_request(req: types.CallToolRequest) -> types.ServerResult:
    tool_func = _TOOL_FUNCTIONS.get(req.params.name)

    if tool_func is None:
        return types.ServerResult(
            types.CallToolResult(
                content=[
                    types.TextContent(
                        type="text",
                        text=f"Unknown tool: {req.params.name}",
                    )
                ],
                isError=True,
            )
        )

    import inspect

    try:
        if inspect.iscoroutinefunction(tool_func):
            result = await tool_func(**(req.params.arguments or {}))
        else:
            result = tool_func(**(req.params.arguments or {}))
    except Exception as e:
        return types.ServerResult(
            types.CallToolResult(
                content=[
                    types.TextContent(
                        type="text",
                        text=f"Tool execution error: {str(e)}",
                    )
                ],
                isError=True,
            )
        )

    if isinstance(result, types.CallToolResult):
        if not hasattr(result, "_meta") or result._meta is None:
            tool_to_widget = {
                "get_faq": "huggies-cards",
                "list_faqs": "huggies-cards",
                "get_item_by_id": "huggies-cards",
                "diaper_size_calc": "huggies-size-calc",
                "map_widget": "huggies-map",
                "coupons": "huggies-offers",
                "suggest_names": "huggies-names",
                "predict_gender": "huggies-gender",
            }
            widget_id = tool_to_widget.get(req.params.name)
            widget = WIDGETS_BY_ID.get(widget_id) if widget_id else widgets[0]
            result._meta = _tool_invocation_meta(widget)
        return types.ServerResult(result)
    else:
        widget = WIDGETS_BY_ID.get("huggies-cards", widgets[0])
        meta = _tool_invocation_meta(widget)
        return types.ServerResult(
            types.CallToolResult(
                content=[types.TextContent(type="text", text=str(result))],
                _meta=meta,
            )
        )


mcp._mcp_server.request_handlers[types.CallToolRequest] = _call_tool_request
mcp._mcp_server.request_handlers[types.ReadResourceRequest] = _handle_read_resource

app = mcp.streamable_http_app()

try:
    from starlette.middleware.cors import CORSMiddleware

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
        allow_credentials=False,
    )
except Exception:
    pass


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        forwarded_allow_ips="*",
    )
