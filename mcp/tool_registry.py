import json
import logging
from typing import Callable, Dict, Any, List

logger = logging.getLogger(__name__)

class ToolRegistry:
    """
    Registry for Model Context Protocol (MCP) tools.
    Allows easy decorator-based registration and discovery.
    """
    def __init__(self) -> None:
        self._tools: Dict[str, Dict[str, Any]] = {}

    def register_tool(self, name: str, description: str, input_schema: Dict[str, Any]):
        """
        Decorator to register a function as an MCP tool.
        """
        def decorator(func: Callable):
            self._tools[name] = {
                "name": name,
                "description": description,
                "input_schema": input_schema,
                "handler": func
            }
            logger.info(f"Registered MCP tool: {name}")
            return func
        return decorator

    def get_tool_definitions(self) -> List[Dict[str, Any]]:
        """
        Returns the list of tool definitions for client discovery.
        """
        return [
            {
                "name": tool["name"],
                "description": tool["description"],
                "inputSchema": tool["input_schema"]
            }
            for tool in self._tools.values()
        ]

    def execute_tool(self, name: str, arguments: Dict[str, Any]) -> Any:
        """
        Executes a registered tool by name with the given arguments.
        """
        if name not in self._tools:
            raise KeyError(f"Tool {name} not found in registry.")
        
        handler = self._tools[name]["handler"]
        try:
            return handler(**arguments)
        except Exception as e:
            logger.error(f"Error executing tool {name}: {str(e)}")
            raise e

# Global registry instance
mcp_tool_registry = ToolRegistry()
