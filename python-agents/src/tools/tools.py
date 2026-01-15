"""
Agent Tools - Base class and implementations
Tools extend agent capabilities with external actions
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, List
from dataclasses import dataclass
import httpx
import json
import math
from datetime import datetime
import structlog

logger = structlog.get_logger()


@dataclass
class ToolResult:
    """Result from a tool execution"""
    success: bool
    data: Any
    error: Optional[str] = None
    metadata: Dict[str, Any] = None


class BaseTool(ABC):
    """Base class for all agent tools"""
    
    name: str
    description: str
    
    @abstractmethod
    async def run(self, **kwargs) -> ToolResult:
        """Execute the tool with given parameters"""
        pass
    
    def to_schema(self) -> Dict:
        """Return tool schema for LLM function calling"""
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.get_parameters()
        }
    
    def get_parameters(self) -> Dict:
        """Override to define tool parameters"""
        return {"type": "object", "properties": {}}


class WebSearchTool(BaseTool):
    """
    Search the web for information.
    Uses DuckDuckGo Instant Answer API (free, no API key required).
    """
    
    name = "web_search"
    description = "Search the web for current information on any topic"
    
    def __init__(self):
        self.base_url = "https://api.duckduckgo.com/"
    
    async def run(self, query: str, max_results: int = 5) -> ToolResult:
        """
        Search the web for a query.
        
        Args:
            query: Search query
            max_results: Maximum number of results
            
        Returns:
            ToolResult with search results
        """
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    self.base_url,
                    params={
                        "q": query,
                        "format": "json",
                        "no_html": 1,
                        "skip_disambig": 1
                    }
                )
                response.raise_for_status()
                data = response.json()
            
            results = []
            
            # Abstract (main answer)
            if data.get("Abstract"):
                results.append({
                    "type": "abstract",
                    "text": data["Abstract"],
                    "source": data.get("AbstractSource", ""),
                    "url": data.get("AbstractURL", "")
                })
            
            # Related topics
            for topic in data.get("RelatedTopics", [])[:max_results]:
                if isinstance(topic, dict) and "Text" in topic:
                    results.append({
                        "type": "related",
                        "text": topic["Text"],
                        "url": topic.get("FirstURL", "")
                    })
            
            logger.info(f"Web search for '{query}' returned {len(results)} results")
            
            return ToolResult(
                success=True,
                data=results,
                metadata={"query": query, "result_count": len(results)}
            )
            
        except Exception as e:
            logger.error(f"Web search failed: {e}")
            return ToolResult(
                success=False,
                data=None,
                error=str(e)
            )
    
    def get_parameters(self) -> Dict:
        return {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The search query"
                },
                "max_results": {
                    "type": "integer",
                    "description": "Maximum number of results",
                    "default": 5
                }
            },
            "required": ["query"]
        }


class CalculatorTool(BaseTool):
    """
    Perform mathematical calculations.
    Supports basic arithmetic and common functions.
    """
    
    name = "calculator"
    description = "Perform mathematical calculations (add, subtract, multiply, divide, percentages)"
    
    async def run(self, expression: str) -> ToolResult:
        """
        Evaluate a mathematical expression.
        
        Args:
            expression: Math expression to evaluate
            
        Returns:
            ToolResult with calculation result
        """
        try:
            # Safe math functions
            safe_dict = {
                "abs": abs,
                "round": round,
                "min": min,
                "max": max,
                "sum": sum,
                "pow": pow,
                "sqrt": math.sqrt,
                "sin": math.sin,
                "cos": math.cos,
                "tan": math.tan,
                "log": math.log,
                "log10": math.log10,
                "pi": math.pi,
                "e": math.e
            }
            
            # Clean the expression
            clean_expr = expression.replace("^", "**")
            clean_expr = clean_expr.replace("%", "/100*")  # Handle percentages
            
            # Evaluate safely
            result = eval(clean_expr, {"__builtins__": {}}, safe_dict)
            
            logger.info(f"Calculator: {expression} = {result}")
            
            return ToolResult(
                success=True,
                data={"expression": expression, "result": result},
                metadata={"type": "calculation"}
            )
            
        except Exception as e:
            logger.error(f"Calculator error: {e}")
            return ToolResult(
                success=False,
                data=None,
                error=f"Cannot evaluate: {expression}. Error: {e}"
            )
    
    def get_parameters(self) -> Dict:
        return {
            "type": "object",
            "properties": {
                "expression": {
                    "type": "string",
                    "description": "Mathematical expression to evaluate"
                }
            },
            "required": ["expression"]
        }


class PriceCalculatorTool(BaseTool):
    """
    Calculate prices for Web Shop services.
    Uses the official pricing rules.
    """
    
    name = "price_calculator"
    description = "Calculate price for Web Shop services based on requirements"
    
    PRICING = {
        "base": {
            "vitrine": 299,
            "ecommerce": 599,
            "surmesure": 1299
        },
        "addons": {
            "seo": 150,
            "maintenance_mensuelle": 49,
            "multilangue": 200,
            "blog": 100,
            "reservation": 250,
            "paiement_stripe": 150,
            "newsletter": 75,
            "analytics": 100,
            "chatbot": 200
        },
        "multipliers": {
            "urgent": 1.3,  # < 2 semaines
            "complexe": 1.5,  # > 10 pages
            "refonte": 0.8  # Client existant
        }
    }
    
    async def run(
        self,
        service_type: str,
        addons: Optional[List[str]] = None,
        is_urgent: bool = False,
        is_complex: bool = False,
        is_refonte: bool = False
    ) -> ToolResult:
        """
        Calculate total price for a service.
        
        Args:
            service_type: Type of service (vitrine, ecommerce, surmesure)
            addons: List of addon IDs
            is_urgent: Urgent delivery (< 2 weeks)
            is_complex: Complex project (> 10 pages)
            is_refonte: Existing client redesign
            
        Returns:
            ToolResult with detailed price breakdown
        """
        try:
            service_type = service_type.lower()
            if service_type not in self.PRICING["base"]:
                return ToolResult(
                    success=False,
                    data=None,
                    error=f"Service inconnu: {service_type}. Options: vitrine, ecommerce, surmesure"
                )
            
            base_price = self.PRICING["base"][service_type]
            addon_total = 0
            addon_details = []
            
            if addons:
                for addon in addons:
                    addon = addon.lower().replace(" ", "_")
                    if addon in self.PRICING["addons"]:
                        price = self.PRICING["addons"][addon]
                        addon_total += price
                        addon_details.append({"name": addon, "price": price})
            
            subtotal = base_price + addon_total
            
            # Apply multipliers
            multiplier = 1.0
            multiplier_notes = []
            
            if is_urgent:
                multiplier *= self.PRICING["multipliers"]["urgent"]
                multiplier_notes.append("Urgent +30%")
            if is_complex:
                multiplier *= self.PRICING["multipliers"]["complexe"]
                multiplier_notes.append("Complexe +50%")
            if is_refonte:
                multiplier *= self.PRICING["multipliers"]["refonte"]
                multiplier_notes.append("Refonte -20%")
            
            total = round(subtotal * multiplier, 2)
            
            result = {
                "service_type": service_type,
                "base_price": base_price,
                "addons": addon_details,
                "addon_total": addon_total,
                "subtotal": subtotal,
                "multiplier": multiplier,
                "multiplier_notes": multiplier_notes,
                "total": total,
                "currency": "EUR"
            }
            
            logger.info(f"Price calculated: {total}€ for {service_type}")
            
            return ToolResult(
                success=True,
                data=result,
                metadata={"type": "price_calculation"}
            )
            
        except Exception as e:
            logger.error(f"Price calculation error: {e}")
            return ToolResult(
                success=False,
                data=None,
                error=str(e)
            )
    
    def get_parameters(self) -> Dict:
        return {
            "type": "object",
            "properties": {
                "service_type": {
                    "type": "string",
                    "enum": ["vitrine", "ecommerce", "surmesure"],
                    "description": "Type of website service"
                },
                "addons": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of add-ons (seo, multilangue, blog, etc.)"
                },
                "is_urgent": {
                    "type": "boolean",
                    "description": "Urgent delivery needed",
                    "default": False
                },
                "is_complex": {
                    "type": "boolean",
                    "description": "Complex project (>10 pages)",
                    "default": False
                },
                "is_refonte": {
                    "type": "boolean",
                    "description": "Redesign for existing client",
                    "default": False
                }
            },
            "required": ["service_type"]
        }


class DateTimeTool(BaseTool):
    """Get current date/time and calculate dates"""
    
    name = "datetime"
    description = "Get current date/time or calculate future dates"
    
    async def run(
        self, 
        action: str = "now",
        days_offset: int = 0
    ) -> ToolResult:
        """
        Get date/time information.
        
        Args:
            action: "now" for current time, "future" for calculated date
            days_offset: Days to add to current date
            
        Returns:
            ToolResult with date information
        """
        now = datetime.now()
        
        if action == "now":
            return ToolResult(
                success=True,
                data={
                    "date": now.strftime("%Y-%m-%d"),
                    "time": now.strftime("%H:%M:%S"),
                    "day": now.strftime("%A"),
                    "formatted_fr": now.strftime("%d/%m/%Y à %H:%M")
                }
            )
        elif action == "future":
            from datetime import timedelta
            future = now + timedelta(days=days_offset)
            return ToolResult(
                success=True,
                data={
                    "date": future.strftime("%Y-%m-%d"),
                    "day": future.strftime("%A"),
                    "days_from_now": days_offset,
                    "formatted_fr": future.strftime("%d/%m/%Y")
                }
            )
        else:
            return ToolResult(
                success=False,
                data=None,
                error=f"Unknown action: {action}"
            )


# Tool registry
_tools: Dict[str, BaseTool] = {}


def register_tool(tool: BaseTool) -> None:
    """Register a tool"""
    _tools[tool.name] = tool
    logger.info(f"Registered tool: {tool.name}")


def get_tool(name: str) -> Optional[BaseTool]:
    """Get a tool by name"""
    return _tools.get(name)


def get_all_tools() -> List[BaseTool]:
    """Get all registered tools"""
    return list(_tools.values())


def get_tool_schemas() -> List[Dict]:
    """Get schemas for all tools (for LLM function calling)"""
    return [tool.to_schema() for tool in _tools.values()]


# Register default tools
def initialize_tools():
    """Initialize all default tools"""
    register_tool(WebSearchTool())
    register_tool(CalculatorTool())
    register_tool(PriceCalculatorTool())
    register_tool(DateTimeTool())
    logger.info(f"Initialized {len(_tools)} tools")


# Auto-initialize on import
initialize_tools()
