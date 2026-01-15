"""
Agent Orchestrator Engine
Central coordinator for all AI agents using LangGraph
"""

from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from enum import Enum
import asyncio
import structlog

from langgraph.graph import StateGraph, END
from pydantic import BaseModel

logger = structlog.get_logger()


class AgentStatus(Enum):
    IDLE = "idle"
    RUNNING = "running"
    ERROR = "error"
    DISABLED = "disabled"


@dataclass
class AgentState:
    """State passed between agents in the graph"""
    messages: List[Dict[str, Any]] = field(default_factory=list)
    current_agent: str = ""
    session_id: str = ""
    user_input: str = ""
    context: Dict[str, Any] = field(default_factory=dict)
    response: str = ""
    should_escalate: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)


class AgentRegistry:
    """Registry of all available agents"""
    
    def __init__(self):
        self._agents: Dict[str, Any] = {}
        self._status: Dict[str, AgentStatus] = {}
    
    def register(self, agent_id: str, agent_instance: Any) -> None:
        """Register an agent"""
        self._agents[agent_id] = agent_instance
        self._status[agent_id] = AgentStatus.IDLE
        logger.info(f"Registered agent: {agent_id}")
    
    def get(self, agent_id: str) -> Optional[Any]:
        """Get an agent by ID"""
        return self._agents.get(agent_id)
    
    def list_agents(self) -> List[Dict[str, Any]]:
        """List all registered agents"""
        return [
            {
                "id": agent_id,
                "name": agent.name,
                "role": agent.role,
                "status": self._status[agent_id].value
            }
            for agent_id, agent in self._agents.items()
        ]
    
    def set_status(self, agent_id: str, status: AgentStatus) -> None:
        """Update agent status"""
        if agent_id in self._status:
            self._status[agent_id] = status


class Orchestrator:
    """
    Main orchestrator that coordinates all agents.
    Uses LangGraph for workflow management.
    """
    
    def __init__(self):
        self.registry = AgentRegistry()
        self.workflows: Dict[str, StateGraph] = {}
        self._setup_default_workflow()
        logger.info("🎭 Orchestrator initialized")
    
    def _setup_default_workflow(self) -> None:
        """Setup the default agent workflow graph"""
        
        # Create the graph
        workflow = StateGraph(AgentState)
        
        # Add nodes for each agent type
        workflow.add_node("router", self._route_request)
        workflow.add_node("marie_support", self._invoke_support)
        workflow.add_node("hugo_content", self._invoke_content)
        workflow.add_node("lucas_quote", self._invoke_quote)
        workflow.add_node("emma_email", self._invoke_email)
        workflow.add_node("noah_analytics", self._invoke_analytics)
        workflow.add_node("john_social", self._invoke_social)
        workflow.add_node("response", self._format_response)
        
        # Set entry point
        workflow.set_entry_point("router")
        
        # Add edges
        workflow.add_conditional_edges(
            "router",
            self._determine_agent,
            {
                "marie": "marie_support",
                "hugo": "hugo_content",
                "lucas": "lucas_quote",
                "emma": "emma_email",
                "noah": "noah_analytics",
                "john": "john_social",
                "end": END
            }
        )
        
        # All agents go to response
        for agent in ["marie_support", "hugo_content", "lucas_quote", 
                      "emma_email", "noah_analytics", "john_social"]:
            workflow.add_edge(agent, "response")
        
        workflow.add_edge("response", END)
        
        self.workflows["default"] = workflow.compile()
    
    async def _route_request(self, state: AgentState) -> AgentState:
        """Route incoming request to appropriate agent"""
        logger.info(f"Routing request for session: {state.session_id}")
        return state
    
    def _determine_agent(self, state: AgentState) -> str:
        """Determine which agent should handle the request"""
        agent = state.current_agent.lower()
        valid_agents = ["marie", "hugo", "lucas", "emma", "noah", "john"]
        
        if agent in valid_agents:
            return agent
        
        # Default to Marie for support
        return "marie"
    
    async def _invoke_support(self, state: AgentState) -> AgentState:
        """Invoke MARIE support agent"""
        agent = self.registry.get("marie")
        if agent:
            response = await agent.process(state)
            state.response = response
        else:
            state.response = "Agent MARIE non disponible"
        return state
    
    async def _invoke_content(self, state: AgentState) -> AgentState:
        """Invoke HUGO content agent"""
        agent = self.registry.get("hugo")
        if agent:
            response = await agent.process(state)
            state.response = response
        else:
            state.response = "Agent HUGO non disponible"
        return state
    
    async def _invoke_quote(self, state: AgentState) -> AgentState:
        """Invoke LUCAS quote agent"""
        agent = self.registry.get("lucas")
        if agent:
            response = await agent.process(state)
            state.response = response
        else:
            state.response = "Agent LUCAS non disponible"
        return state
    
    async def _invoke_email(self, state: AgentState) -> AgentState:
        """Invoke EMMA email agent"""
        agent = self.registry.get("emma")
        if agent:
            response = await agent.process(state)
            state.response = response
        else:
            state.response = "Agent EMMA non disponible"
        return state
    
    async def _invoke_analytics(self, state: AgentState) -> AgentState:
        """Invoke NOAH analytics agent"""
        agent = self.registry.get("noah")
        if agent:
            response = await agent.process(state)
            state.response = response
        else:
            state.response = "Agent NOAH non disponible"
        return state
    
    async def _invoke_social(self, state: AgentState) -> AgentState:
        """Invoke JOHN social media agent"""
        agent = self.registry.get("john")
        if agent:
            response = await agent.process(state)
            state.response = response
        else:
            state.response = "Agent JOHN non disponible"
        return state
    
    async def _format_response(self, state: AgentState) -> AgentState:
        """Format the final response"""
        logger.info(f"Formatting response from {state.current_agent}")
        return state
    
    async def invoke(
        self,
        agent_id: str,
        message: str,
        session_id: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Invoke an agent with a message.
        
        Args:
            agent_id: The agent to invoke (marie, hugo, lucas, etc.)
            message: User message
            session_id: Conversation session ID
            context: Additional context
            
        Returns:
            Agent response
        """
        state = AgentState(
            user_input=message,
            session_id=session_id,
            current_agent=agent_id,
            context=context or {}
        )
        
        try:
            # Run through the workflow
            workflow = self.workflows.get("default")
            if workflow:
                result = await workflow.ainvoke(state)
                return {
                    "success": True,
                    "message": result.response,
                    "agent": agent_id.upper(),
                    "session_id": session_id
                }
        except Exception as e:
            logger.error(f"Error invoking agent {agent_id}: {e}")
            return {
                "success": False,
                "error": str(e),
                "agent": agent_id.upper()
            }
        
        return {
            "success": False,
            "error": "Unknown error"
        }


# Global orchestrator instance
_orchestrator: Optional[Orchestrator] = None


def get_orchestrator() -> Orchestrator:
    """Get the global orchestrator instance"""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = Orchestrator()
    return _orchestrator
