"""
Base Agent Class
All agents inherit from this base class
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
import structlog

from ..orchestrator import AgentState

logger = structlog.get_logger()


@dataclass
class AgentConfig:
    """Configuration for an agent"""
    name: str
    role: str
    description: str
    model: str = "claude-sonnet-4-20250514"
    temperature: float = 0.7
    max_tokens: int = 2048
    system_prompt: str = ""


class BaseAgent(ABC):
    """
    Base class for all AI agents.
    
    Each agent specializes in a specific task:
    - MARIE: Customer support
    - JOHN: Social media
    - HUGO: Content generation
    - LUCAS: Quote generation
    - EMMA: Email handling
    - NOAH: Analytics
    """
    
    def __init__(self, config: AgentConfig):
        self.config = config
        self.name = config.name
        self.role = config.role
        self.description = config.description
        self._llm = None
        logger.info(f"🤖 Agent {self.name} initialized: {self.role}")
    
    @abstractmethod
    async def process(self, state: AgentState) -> str:
        """
        Process the agent state and return a response.
        
        Args:
            state: Current agent state containing user input and context
            
        Returns:
            Response string
        """
        pass
    
    @abstractmethod
    def get_system_prompt(self) -> str:
        """Get the system prompt for this agent"""
        pass
    
    async def invoke_llm(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None
    ) -> str:
        """
        Invoke the LLM with the given messages.
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            system_prompt: Optional override for system prompt
            
        Returns:
            LLM response text
        """
        from ..llm import get_llm_router
        
        router = get_llm_router()
        prompt = system_prompt or self.get_system_prompt()
        
        result = await router.chat(
            messages=messages,
            system_prompt=prompt,
            model=self.config.model,
            temperature=self.config.temperature,
            max_tokens=self.config.max_tokens
        )
        
        return result
    
    def _extract_user_message(self, state: AgentState) -> str:
        """Extract the user message from state"""
        return state.user_input
    
    def _get_conversation_history(self, state: AgentState) -> List[Dict[str, str]]:
        """Get conversation history from state"""
        history = []
        for msg in state.messages:
            history.append({
                "role": msg.get("role", "user"),
                "content": msg.get("content", "")
            })
        return history
    
    def __repr__(self) -> str:
        return f"<Agent {self.name}: {self.role}>"
