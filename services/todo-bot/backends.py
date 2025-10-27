import os
import logging
import json
from typing import Dict, Any, List, Protocol
from openai import OpenAI
from todoclientmcp import TodoMCPClient, MCPError


logger = logging.getLogger(__name__)

# Configuration
TODO_MCP_URL = os.environ.get("TODO_MCP_URL", "http://localhost:8081")

class ChatBackend(Protocol):
    def chat(self, prompt: str, user: str) -> str: 
        ...

class OpenAIBackend:
    def __init__(self): 
        self.model = os.environ.get("OPENAI_MODEL", "gpt-4")
        self.client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY")) 
        self.openai_max_tokens = int(os.environ.get("OPENAI_MAX_TOKENS", "1000"))
        self.openai_temperature = float(os.environ.get("OPENAI_TEMPERATURE", "0.3"))
        self.conversation_history = []
        self.mcpclient = TodoMCPClient(TODO_MCP_URL)
        self.mcpclient.connect()
        self.mcp_tools = self.mcpclient.list_tools()
        # logger.info(f"MCP tools loaded: {self.mcp_tools}")

    async def chat(self, prompt: str, user: str) -> str:
        system_prompt = f"""You are a friendly bot that manages todos.

CORE CAPABILITIES:
- Manage a list of todos, including adding, updating, deleting, and listing todos.

AVAILABLE FUNCTIONS:
- todos-list(): List all todos
- todos-add(title: str): Add a new todo with the given title
- todos-delete(id: int): Delete the todo with the given ID
- todos-update(id: int, title: str): Update the todo with the given ID to the new title

SAFETY RULES:
- Ask for confirmation when deleting todos

EXAMPLES:
- "Get my todo list" → todos-list()
- "Add a new todo to buy milk" → todos-add("buy milk")
- "Delete my todo with id 1" → todos-delete(1)
- "Update my todo with id 2 to 'walk the dog'" → todos-update(2, "walk the dog")
"""
        # Prepare messages
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ]
        self.conversation_history.extend(messages)

        # Prepare API call parameters
        kwargs = {
            "max_tokens": self.openai_max_tokens,
            "temperature": self.openai_temperature,
            "functions": self._get_available_functions(),
            "function_call": "auto"
        }

        response = self.client.chat.completions.create(model=self.model, messages=self.conversation_history, **kwargs)
    
        logger.info(f"OpenAI response: {response}")

        # Handle function calls
        if response.choices[0].message.function_call:
            return await self._handle_function_call(
                response.choices[0].message,
                user
            )

        # Handle regular text response
        if response.choices and len(response.choices) > 0:
            assistant_reply = response.choices[0].message.content
            if assistant_reply:
                self.conversation_history.append({"role": "assistant", "content": assistant_reply})
                assistant_reply = assistant_reply.strip()
                if len(assistant_reply) > 3000:
                    assistant_reply = assistant_reply[:2900] + "... (truncated for length)"
                return assistant_reply

        return "❌ No response generated from AI agent."

    def _get_available_functions(self) -> List[Dict[str, Any]]:
        """Get the list of available functions for OpenAI function calling."""
        if not self.mcpclient:
            return []

        # Use dynamically fetched MCP tools if available
        if self.mcpclient:
            return [self._convert_mcp_tool_to_openai_function(tool) for tool in self.mcp_tools]

        # Fallback: Return empty list if no tools fetched
        logger.warning("No MCP tools available - agent will have limited functionality")
        return []
    
    def _convert_mcp_tool_to_openai_function(self, mcp_tool: Dict[str, Any]) -> Dict[str, Any]:
        """Convert MCP tool definition to OpenAI function format."""
        # Convert MCP parameters to OpenAI schema
        properties = {}
        required = []

        for param_name, param_def in mcp_tool.get("parameters", {}).items():
            properties[param_name] = {
                "type": param_def.get("type", "string"),
                "description": param_def.get("description", "")
            }

            # Add enum if present
            if param_def.get("enum"):
                properties[param_name]["enum"] = param_def["enum"]

            # Add to required if specified
            if param_def.get("required", True):
                required.append(param_name)

        return {
            "name": mcp_tool["name"],
            "description": mcp_tool["description"],
            "parameters": {
                "type": "object",
                "properties": properties,
                "required": required
            }
        }
    
    async def _handle_function_call(self, message: Dict[str, Any], user: str) -> str:
        """Handle function call from OpenAI response."""
        logger.info(f"Handling function call: {message.function_call}")

        function_call = message.function_call
        function_name = function_call.name
        function_args_str = function_call.arguments

        logger.info(f"Function call detected: {function_name} with args {function_args_str}")

        try:
            # Parse function arguments from JSON string to dict
            function_args = json.loads(function_args_str) if isinstance(function_args_str, str) else function_args_str

            # Call the MCP client to execute the tool
            tool_response = self.mcpclient.call_tool(function_name, function_args)

            # Append function call and response to conversation history
            self.conversation_history.append({
                "role": "assistant",
                "content": None,
                "function_call": {
                    "name": function_name,
                    "arguments": function_args_str  # Keep as string for OpenAI format
                }
            })
            self.conversation_history.append({
                "role": "function",
                "name": function_name,
                "content": tool_response
            })

            # Make another call to LLM to synthesize the function result into natural language
            logger.info("Asking LLM to synthesize function result into natural language")
            synthesis_response = self.client.chat.completions.create(
                model=self.model,
                messages=self.conversation_history,
                max_tokens=self.openai_max_tokens,
                temperature=self.openai_temperature
            )

            if synthesis_response.choices and len(synthesis_response.choices) > 0:
                assistant_reply = synthesis_response.choices[0].message.content
                if assistant_reply:
                    self.conversation_history.append({"role": "assistant", "content": assistant_reply})
                    return assistant_reply.strip()

            # Fallback to raw response if synthesis fails
            return tool_response

        except MCPError as e:
            logger.error(f"Error calling tool {function_name}: {e}")
            return f"❌ Error executing function {function_name}: {e}"  