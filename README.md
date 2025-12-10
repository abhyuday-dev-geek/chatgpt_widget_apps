# Huggies Apps SDK Example

[![MIT License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

This repository showcases Huggies-branded UI components built with the OpenAI Apps SDK. It demonstrates how to create interactive widgets for ChatGPT using the Model Context Protocol (MCP) and React components.

**Note:** If you are on Chrome and have recently updated to version 142, you will need to disable the [`local-network-access` flag](https://developer.chrome.com/release-notes/142#local_network_access_restrictions) to see the widget UI.

How to disable it:

1. Go to chrome://flags/
2. Find #local-network-access-check
3. Set it to Disabled

⚠️ **Note 🚨 Make sure to restart Chrome after changing this flag for the update to take effect.**

## MCP + Apps SDK Overview

The Model Context Protocol (MCP) is an open specification for connecting large language model clients to external tools, data, and user interfaces. An MCP server exposes tools that a model can call during a conversation and returns results according to the tool contracts. Those results can include extra metadata—such as inline HTML—that the Apps SDK uses to render rich UI components (widgets) alongside assistant messages.

Within the Apps SDK, MCP keeps the server, model, and UI in sync. By standardizing the wire format, authentication, and metadata, it lets ChatGPT reason about your connector the same way it reasons about built-in tools. A minimal MCP integration for Apps SDK implements three capabilities:

1. **List tools** – Your server advertises the tools it supports, including their JSON Schema input/output contracts and optional annotations (for example, `readOnlyHint`).
2. **Call tools** – When a model selects a tool, it issues a `call_tool` request with arguments that match the user intent. Your server executes the action and returns structured content the model can parse.
3. **Return widgets** – Alongside structured content, return embedded resources in the response metadata so the Apps SDK can render the interface inline in the Apps SDK client (ChatGPT).

Because the protocol is transport agnostic, you can host the server over Server-Sent Events or streaming HTTP—Apps SDK supports both.

The MCP server in this demo highlights how each tool can light up widgets by combining structured payloads with `_meta.openai/outputTemplate` metadata returned from the MCP server.

## Repository Structure

- `src/` – Source for each Huggies widget component:
  - `huggies-cards/` – FAQ cards widget displaying frequently asked questions
  - `huggies-size-calc/` – Diaper size calculator widget
  - `huggies-map/` – Store locator widget
  - `huggies-offers/` – Coupons and offers widget
  - `huggies-names/` – Baby name suggestions widget
  - `huggies-gender/` – Gender prediction widget
- `assets/` – Generated HTML, JS, and CSS bundles after running the build step
- `huggies_server_python/` – Python MCP server that returns the Huggies widgets
- `build-all.mts` – Vite build orchestrator that produces hashed bundles for every widget entrypoint

## Available Widgets

### 1. Huggies Cards (FAQ)
Displays frequently asked questions in a card-based layout. Each card shows a question, answer, and optional source link.

### 2. Huggies Size Calculator
Helps parents determine the correct diaper size based on their baby's weight (in pounds or kilograms).

### 3. Huggies Map (Store Locator)
Shows nearby retailers where Huggies products can be purchased. Displays location markers and distance information.

### 4. Huggies Offers
Displays current coupons, promotions, and special offers available for Huggies products.

### 5. Huggies Names
Suggests unique baby names based on user preferences and prefixes.

### 6. Huggies Gender
Provides playful gender prediction based on due date or conception date.

## Prerequisites

- Node.js 18+
- pnpm (recommended) or npm/yarn
- Python 3.10+ (for the Python MCP server)
- pre-commit for formatting (optional)

## Installation

Clone the repository and install the workspace dependencies:

```bash
pnpm install
pre-commit install
```

> Using npm or yarn? Install the root dependencies with your preferred client and adjust the commands below accordingly.

## Build the Components

The components are bundled into standalone assets that the MCP server serves as reusable UI resources.

```bash
pnpm run build
```

This command runs `build-all.mts`, producing versioned `.html`, `.js`, and `.css` files inside `assets/`. Each widget is wrapped with the CSS it needs so you can host the bundles directly or ship them with your own server.

To iterate on your components locally, you can also launch the Vite dev server:

```bash
pnpm run dev
```

## Serve the Static Assets

The MCP server expects the bundled HTML, JS, and CSS to be served from a local static file server. After every build, start the server before launching the MCP process:

```bash
pnpm run serve
```

The assets are exposed at [`http://localhost:4444`](http://localhost:4444) with CORS enabled so that local tooling (including MCP inspectors) can fetch them.

> **Note:** The Python Huggies server caches widget HTML with `functools.lru_cache`. If you rebuild or manually edit files in `assets/`, restart the MCP server so it picks up the updated markup.

## Run the MCP Server

The repository includes a Python MCP server that exposes Huggies widgets as tools.

### Huggies Python Server

```bash
cd huggies_server_python
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn huggies_server_python.main:app --port 8000
```

Or run directly:

```bash
python huggies_server_python/main.py
```

This boots a FastAPI app with uvicorn on `http://127.0.0.1:8000`. The server exposes:

- `GET /mcp` – SSE stream endpoint
- `POST /mcp/messages?sessionId=...` – Accepts follow-up messages for an active session
- `GET /widgets/{filename}` – Serves static HTML widgets

### Available Tools

The server exposes the following tools:

- **get_faq(query)** – Search FAQs and return results with widget cards
- **list_faqs()** – List all available FAQs
- **get_item_by_id(item_id)** – Get a specific FAQ item by ID
- **diaper_size_calc(weight_kg, weight_lb)** – Calculate recommended diaper size
- **map_widget(zip_code, location, limit)** – Find retailers near a location
- **coupons()** – Get current Huggies coupons and offers
- **suggest_names(prefix, count)** – Suggest unique baby names
- **predict_gender(due_date, conception_date)** – Playful gender prediction

## Testing in ChatGPT

To add this app to ChatGPT, enable [developer mode](https://platform.openai.com/docs/guides/developer-mode), and add your app in Settings > Connectors.

To add your local server without deploying it, you can use a tool like [ngrok](https://ngrok.com/) to expose your local server to the internet.

For example, once your MCP server is running, you can run:

```bash
ngrok http 8000
```

You will get a public URL that you can use to add your local server to ChatGPT in Settings > Connectors.

For example: `https://<custom_endpoint>.ngrok-free.app/mcp`

Once you add a connector, you can use it in ChatGPT conversations.

You can add your app to the conversation context by selecting it in the "More" options.

You can then invoke tools by asking something related. For example, you can ask:
- "What are some common questions about Huggies diapers?"
- "What size diaper should I get for a 15-pound baby?"
- "Find Huggies retailers near zip code 90210"
- "What coupons are available for Huggies?"
- "Suggest some baby names starting with 'A'"
- "Predict the gender for a baby due on December 25th"

## Next Steps

- **Customize the widget data**: Edit the handlers in `huggies_server_python/main.py` to fetch data from your systems or APIs.
- **Create your own components**: Add new widget entries to `src/` and they will be picked up automatically by the build script.
- **Connect to real data**: Replace the mock knowledge base with real database queries or API calls.

### Deploy Your MCP Server

You can use the cloud environment of your choice to deploy your MCP server.

Include this in the environment variables:

```
BASE_URL=https://your-server.com
```

This will be used to generate the HTML for the widgets so that they can serve static assets from this hosted URL.

## Contributing

You are welcome to open issues or submit PRs to improve this app, however, please note that we may not review all suggestions.

## License

This project is licensed under the MIT License. See [LICENSE](./LICENSE) for details.
