# Huggies MCP server (Python)

This directory packages a Python implementation of the Huggies demo server using the `FastMCP` helper from the official Model Context Protocol SDK. It exposes multiple tools for Huggies-related queries, including FAQ lookup, diaper size calculator, store locator, coupons, baby name suggestions, and gender prediction.

## Prerequisites

- Python 3.10+
- A virtual environment (recommended)

## Installation

```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

> **Heads up:** There is a similarly named package named `modelcontextprotocol`
> on PyPI that is unrelated to the official MCP SDK. The requirements file
> installs the official `mcp` distribution with its FastAPI extra so that the
> `mcp.server.fastmcp` module is available. If you previously installed the
> other project, run `pip uninstall modelcontextprotocol` before reinstalling
> the requirements.

## Run the server

```bash
python main.py
```

Or with uvicorn directly:

```bash
uvicorn huggies_server_python.main:app --port 8000
```

This boots a FastAPI app with uvicorn on `http://127.0.0.1:8000`. The endpoints mirror the standard MCP pattern:

- `GET /mcp` exposes the SSE stream.
- `POST /mcp/messages?sessionId=...` accepts follow-up messages for an active session.
- `GET /widgets/{filename}` serves static HTML widgets.

## Available Tools

- **get_faq(query)**: Search FAQs and return results with widget cards
- **list_faqs()**: List all available FAQs
- **get_item_by_id(item_id)**: Get a specific FAQ item by ID
- **diaper_size_calc(weight_kg, weight_lb)**: Calculate recommended diaper size
- **map_widget(zip_code, location, limit)**: Find retailers near a location
- **coupons()**: Get current Huggies coupons and offers
- **suggest_names(prefix, count)**: Suggest unique baby names
- **predict_gender(due_date, conception_date)**: Playful gender prediction

## Widgets

The server supports two types of widgets:

1. **Static HTML widgets** in `ui/widgets/` - Simple HTML files with vanilla JavaScript
2. **Built React widgets** in `assets/` - React components built with `pnpm run build`

The server will first try to load widgets from `assets/` (built React widgets), then fall back to `ui/widgets/` (static HTML).

## Environment Variables

- `MCP_PORT`: Port to run the server on (default: 8000)
- `BASE_URL`: Base URL for serving widgets (default: http://localhost:4444)

## Next steps

Use these handlers as a starting point when wiring in real data, authentication, or localization support. The structure demonstrates how to:

1. Register reusable UI resources that load static HTML bundles or built React widgets.
2. Associate tools with those widgets via `_meta.openai/outputTemplate`.
3. Ship structured JSON alongside human-readable confirmation text.
