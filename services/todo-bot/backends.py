import os
from typing import Protocol, List, Dict
from openai import OpenAI

class ChatBackend(Protocol):
    def chat(self, prompt: str) -> str: 
        ...

class OpenAIBackend:
    def __init__(self): 
        self.model = os.environ.get("OPENAI_MODEL", "gpt-4")
        self.client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY")) 
        self.openai_max_tokens = int(os.environ.get("OPENAI_MAX_TOKENS", "1000"))
        self.openai_temperature = float(os.environ.get("OPENAI_TEMPERATURE", "0.3"))
        self.conversation_history = []

    def chat(self, prompt) -> str:
        system_prompt = f"""You are a friendly bot that specializes in comedy.

CORE CAPABILITIES:
- Answer user questions with humor and wit

AVAILABLE FUNCTIONS:
- None

SAFETY RULES:
- Keep it PG-13

EXAMPLES:
- "Tell me a joke about computers" → Why do programmers prefer dark mode? Because light attracts bugs!
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
        }        

        # Add function calling if MCP client is available
        # functions = self.get_available_functions()
        # if functions and self.mcp_client:
        #     response_kwargs["functions"] = functions
        #     response_kwargs["function_call"] = "auto"

        r = self.client.chat.completions.create(model=self.model, messages=self.conversation_history, **kwargs)
        return r.choices[0].message.content