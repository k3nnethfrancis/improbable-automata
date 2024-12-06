import os
from datetime import datetime
from dotenv import load_dotenv; load_dotenv()
from mirascope.core import openai

# BaseAgent
from abc import abstractmethod

from mirascope.core import BaseMessageParam, openai
from pydantic import BaseModel
from typing import Dict, Any


class OpenAIAgent(BaseModel):
    history: list[BaseMessageParam | openai.OpenAIMessageParam] = []

    @abstractmethod
    def _step(self, prompt: str) -> Dict[str, Any]: ...

    def run(self, prompt: str) -> Dict[str, Any]:
        """Run the agent and return the response directly."""
        return self._step(prompt)