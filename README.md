---
title: Zhihuiya Drug Intel MCP
emoji: 💊
colorFrom: blue
colorTo: green
sdk: docker
pinned: false
license: mit
short_description: MCP Server for Zhihuiya drug pipeline intelligence (B049 + B007)
---

# Zhihuiya Drug Intel MCP Server

A [Model Context Protocol (MCP)](https://modelcontextprotocol.io) server that wraps Zhihuiya (智慧芽) Synapse API, providing drug type autocomplete and drug pipeline search capabilities.

## Tools

### `zhihuiya_drug_type_autocomplete`
Query drug type IDs by keyword prefix (e.g. "CAR-NK", "ADC", "siRNA").

**Input:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `prefix` | string | ✅ | Drug type keyword, e.g. "CAR-NK" |
| `limit` | integer | ❌ | Max results, default 10 |

**Output:** List of `{ drug_type_id, name_en, name_cn }`

---

### `zhihuiya_drug_search`
Search global drug pipeline by drug type, disease, development phase, etc.

**Input:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `drug_type_ids` | list[string] | ❌ | Drug type ID list from B049 |
| `disease_ids` | list[string] | ❌ | Disease ID list |
| `highest_phases` | list[string] | ❌ | e.g. `["phase_1", "phase_2", "approved"]` |
| `limit` | integer | ❌ | Page size, default 20, max 100 |
| `offset` | integer | ❌ | Pagination offset, default 0 |

**Output:** `{ total, items: [{ drug_id, name, highest_phase, targets, diseases, organizations }] }`

## Authentication

Each user provides their own Zhihuiya API Key via **Bearer Token**.

In Eureka Desktop (or any MCP client), register as:

```
Transport:    streamable_http
URL:          https://<your-space-url>.hf.space/mcp
Bearer Token: <your Zhihuiya API Key>
```

The server extracts the key from `Authorization: Bearer <key>` header on every request. No keys are stored server-side.

## Typical Usage

```
# Step 1: Find drug type IDs
zhihuiya_drug_type_autocomplete(prefix="CAR-NK")
→ [{ "drug_type_id": "8554bd28...", "name_en": "CAR-NK" }, ...]

# Step 2: Search drug pipeline
zhihuiya_drug_search(
    drug_type_ids=["8554bd28...", "4b7f9750...", "ef0ebc75..."],
    limit=100,
    offset=0
)
→ { "total": 480, "items": [...] }
```

## Deployment

This Space runs via Docker SDK. Required files:

```
server.py        # MCP server core
app.py           # HF Spaces entrypoint
Dockerfile       # Docker build config
requirements.txt # Python dependencies
```

No environment variables required on the server side — API keys are passed per-request by each user.

## Dependencies

- [fastmcp](https://github.com/jlowin/fastmcp) >= 2.0.0
- [httpx](https://www.python-httpx.org/) >= 0.27.0
- [uvicorn](https://www.uvicorn.org/) >= 0.30.0
