"""
AI Agent Prompts Module.

This module contains system prompts for AI agents including:
- Chat Agent (Email SDR)
- Call Agent (Voice SDR)
"""

from app.prompts.chat_agent import CHAT_AGENT_PROMPT
from app.prompts.call_agent import CALL_AGENT_PROMPT

__all__ = [
    "CHAT_AGENT_PROMPT",
    "CALL_AGENT_PROMPT",
]
