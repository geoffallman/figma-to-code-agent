# Day 1 Findings: MCP Integration

## Challenge Discovered

When calling the Figma MCP server directly via HTTP from Python, we encounter initialization requirements that complicate the simple request pattern.

**Error encountered:**
```
{"jsonrpc":"2.0","error":{"code":-32000,"message":"Invalid request body for initialize request"},"id":null}
```

## Root Cause

The MCP protocol requires a session initialization handshake before calling tools. This is handled automatically by MCP clients (like Claude Code) but requires manual implementation when calling via raw HTTP.

## Solutions

### Option 1: Use Anthropic SDK with MCP Integration (RECOMMENDED)

For the production Python agent, we'll use the Anthropic Python SDK which handles MCP sessions properly:

```python
import anthropic

client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

# The SDK handles MCP tool calls automatically
response = client.messages.create(
    model="claude-sonnet-4-5",
    max_tokens=4096,
    tools=[{
        "name": "mcp__figma__get_screenshot",
        "description": "Get screenshot from Figma",
        # ... tool schema
    }],
    messages=[{
        "role": "user",
        "content": "Get screenshot for node 51:1216"
    }]
)

# Extract image from tool response
for block in response.content:
    if block.type == "tool_use":
        # Image data is in the tool result
        # Can be saved to disk
        pass
```

### Option 2: Use MCP Python Client Library

Use the official `mcp` Python package which handles the protocol:

```python
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

server_params = StdioServerParameters(
    command="figma-mcp-server",
    args=[]
)

async with stdio_client(server_params) as (read, write):
    async with ClientSession(read, write) as session:
        await session.initialize()

        result = await session.call_tool(
            "get_screenshot",
            arguments={"node_id": "51:1216"}
        )
```

### Option 3: Temporary Workaround for Phase 1

For Phase 1 PoC, we can:
1. Use Claude Code (this environment) to fetch screenshots
2. Manually save them for testing
3. Build the rest of the pipeline (rendering, pixel-diff, evaluation)
4. In Week 2-3, implement proper MCP integration using Option 1 or 2

## Decision for Phase 1

**Use Option 3 (Workaround) + Option 1 (Anthropic SDK)**

**Week 1 Plan:**
- Use Claude Code environment to validate the full pipeline
- Build rendering, pixel-diff, and evaluation components
- Test with manually saved Figma screenshots

**Week 2-3 Plan:**
- Implement proper Figma integration using Anthropic SDK
- The SDK will handle MCP calls when using Claude as the agent
- This is actually the production approach anyway

## Key Insight

This "limitation" actually points us to the correct architecture:
- **Don't call MCP directly via HTTP**
- **Use the Anthropic SDK with MCP-enabled tools**
- This is how production agents will work anyway

## Impact on Timeline

**No delay.** We proceed with:
1. Day 2-5: Build rendering, pixel-diff, baseline evaluation (works without MCP)
2. Week 2: Build evaluator and improver agents using Anthropic SDK
3. The SDK handles Figma MCP automatically when we call Claude

## Updated Day 1 Success Criteria

✅ **Original:** Fetch Figma screenshot via MCP and save to disk
✅ **Revised:** Understand MCP integration requirements and define production approach

**Status: Day 1 Complete - Proceed to Day 2**
