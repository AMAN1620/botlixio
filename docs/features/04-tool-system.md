# Tool System

## Overview

The Tool System enables LLM agents to call external functions during conversations using the OpenAI-compatible function calling format. Tools include web search, weather lookup, and automatic lead capture.

---

## Architecture

```
Chat Engine → Tool Registry → Tool Implementation → External API
                                    ↓
                              Result → LLM (next iteration)
```

### Tool Interface

```python
# app/services/tools/base.py

class BaseTool(ABC):
    slug: str          # "web_search"
    name: str          # "Web Search"
    description: str   # For LLM function description

    @abstractmethod
    def get_schema(self) -> dict:
        """Return OpenAI function calling schema."""

    @abstractmethod
    async def execute(self, **kwargs) -> str:
        """Execute the tool and return result as string."""
```

### Tool Registry

```python
# app/services/tools/registry.py

class ToolRegistry:
    def register(self, tool: BaseTool) -> None
    def get_tool(self, slug: str) -> BaseTool | None
    def get_schemas(self, slugs: list[str]) -> list[dict]  # For LLM
    async def dispatch(self, slug: str, **kwargs) -> str
```

---

## Built-in Tools

### 1. Web Search (`web_search`)

**Purpose**: Search the internet and fetch webpage content for real-time information.

```python
# Schema
{
    "type": "function",
    "function": {
        "name": "web_search",
        "description": "Search the internet for current information on any topic",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The search query"
                }
            },
            "required": ["query"]
        }
    }
}
```

**Implementation**:
1. Search via DuckDuckGo API (no API key required) — top 5 results
2. For each result: fetch page content via httpx (timeout 10s)
3. Extract main text via BeautifulSoup
4. Truncate each result to 2000 chars
5. Format as: `[Title](URL)\n{content summary}`

### 2. Weather (`weather`)

**Purpose**: Get current weather for any location.

```python
# Schema
{
    "type": "function",
    "function": {
        "name": "weather",
        "description": "Get current weather conditions for a city or location",
        "parameters": {
            "type": "object",
            "properties": {
                "location": {
                    "type": "string",
                    "description": "City name or location"
                }
            },
            "required": ["location"]
        }
    }
}
```

**Implementation**: Call wttr.in API (free, no key) → parse JSON → format as human-readable text.

### 3. Lead Catcher (`lead_catcher`)

**Purpose**: Automatically capture contact details mentioned in conversations.

This tool is unique — it doesn't call external APIs. Instead, it instructs the LLM to extract and format contact details.

```python
# Schema
{
    "type": "function",
    "function": {
        "name": "capture_lead",
        "description": "Save a lead's contact information when they share it during conversation",
        "parameters": {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Lead's name"},
                "email": {"type": "string", "description": "Lead's email"},
                "phone": {"type": "string", "description": "Lead's phone number"},
                "company": {"type": "string", "description": "Lead's company"}
            },
            "required": []
        }
    }
}
```

**Implementation**: Save lead to database → return confirmation string.

---

## Tool Calling Flow (in Chat Engine)

```
1. LLM response includes tool_calls array
2. For each tool call:
   a. Get tool from registry by function name
   b. Parse arguments from function call
   c. Execute tool with arguments
   d. Create tool result message:
      {role: "tool", tool_call_id: "...", content: "result text"}
3. Add all tool results to message history
4. Call LLM again with updated history
5. If LLM returns more tool calls → go to step 2
6. Max 5 iterations → return last response
```

---

## Tool Access by Plan

| Tool | Free | Starter | Growth | Business |
|------|------|---------|--------|----------|
| Web Search | ✅ | ✅ | ✅ | ✅ |
| Weather | ❌ | ✅ | ✅ | ✅ |
| Lead Catcher | ❌ | ✅ | ✅ | ✅ |

---

## Error Handling

| Error | Handling |
|-------|---------|
| Tool not found | Return error to LLM: "Tool {name} not found" |
| Tool execution timeout (30s) | Return error to LLM: "Tool timed out" |
| Tool API error | Return error to LLM: "Tool error: {message}" |
| Invalid tool arguments | Return error to LLM: "Invalid arguments for tool" |

All errors are passed to the LLM as tool results so it can respond gracefully to the user. Tool errors are **never exposed directly** to end users.

---

## Business Rules

1. **Tool validation**: Agent can only use tools that are active in `tool_configs` AND in the user's plan
2. **Max iterations**: 5 tool call iterations per message to prevent infinite loops
3. **Timeout**: 30 seconds per tool execution
4. **Lead storage**: Leads are linked to agent_id + session_id for attribution
5. **Admin management**: Platform admin can enable/disable tools globally via `tool_configs` table

---

## API Endpoints

Tools don't have their own endpoints. They are:
- **Configured** on agents via the Agent Builder
- **Managed** by admin via `/api/v1/admin/tools`
- **Executed** internally by the Chat Engine during message processing
