from typing import Any

from google.adk.tools import BaseTool, ToolContext


async def block_unknown_category(tool: BaseTool, args: dict[str, Any], tool_context: ToolContext) -> dict | None:
    """
    Checks if 'create_ticket' is called with the category argument 'unknown'.
    If so, blocks the tool executions and returns a specific error dictionary.
    Otherwise, allows the tool call to proceed by returning None.
    """
    tool_name = tool.name
    target_tool_name = "create_ticket"
    blocked_category = "unknown"

    if tool_name == target_tool_name and args.get("category") == blocked_category:
        return {
            "error": (
                "Ticket creation was blocked because the question is not an IT issue. "
                "Tell the user this is not a problem the IT help desk can resolve."
            )
        }

    return None
