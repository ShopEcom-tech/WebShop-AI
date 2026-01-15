"""
LLM Router
Routes requests to Claude (primary) or Gemini (fallback)
"""

import os
from typing import List, Dict, Optional, Any
import structlog
import anthropic
import google.generativeai as genai

logger = structlog.get_logger()


class LLMRouter:
    """
    Routes LLM requests to available providers.
    Claude is primary, Gemini is fallback.
    """
    
    def __init__(self):
        self.claude_client = None
        self.gemini_model = None
        self._init_providers()
    
    def _init_providers(self) -> None:
        """Initialize available LLM providers"""
        
        # Claude (Anthropic)
        anthropic_key = os.getenv("ANTHROPIC_API_KEY")
        if anthropic_key:
            self.claude_client = anthropic.AsyncAnthropic(api_key=anthropic_key)
            logger.info("✅ Claude client initialized")
        
        # Gemini (Google)
        google_key = os.getenv("GOOGLE_AI_API_KEY")
        if google_key:
            genai.configure(api_key=google_key)
            self.gemini_model = genai.GenerativeModel('gemini-2.0-flash')
            logger.info("✅ Gemini client initialized")
        
        if not self.claude_client and not self.gemini_model:
            logger.warning("⚠️ No LLM providers configured!")
    
    async def chat(
        self,
        messages: List[Dict[str, str]],
        system_prompt: str = "",
        model: str = "claude-sonnet-4-20250514",
        temperature: float = 0.7,
        max_tokens: int = 2048
    ) -> str:
        """
        Send a chat completion request.
        
        Args:
            messages: Conversation history
            system_prompt: System prompt for the model
            model: Model name
            temperature: Response creativity (0-1)
            max_tokens: Maximum response length
            
        Returns:
            Model response text
        """
        
        # Try Claude first
        if self.claude_client:
            try:
                return await self._chat_claude(
                    messages, system_prompt, model, temperature, max_tokens
                )
            except Exception as e:
                logger.warning(f"Claude failed, trying Gemini: {e}")
        
        # Fallback to Gemini
        if self.gemini_model:
            try:
                return await self._chat_gemini(
                    messages, system_prompt, temperature, max_tokens
                )
            except Exception as e:
                logger.error(f"Gemini failed: {e}")
        
        raise RuntimeError("No LLM provider available")
    
    async def _chat_claude(
        self,
        messages: List[Dict[str, str]],
        system_prompt: str,
        model: str,
        temperature: float,
        max_tokens: int
    ) -> str:
        """Chat with Claude"""
        
        response = await self.claude_client.messages.create(
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
            system=system_prompt,
            messages=messages
        )
        
        # Extract text from response
        for block in response.content:
            if block.type == "text":
                return block.text
        
        return ""
    
    async def _chat_gemini(
        self,
        messages: List[Dict[str, str]],
        system_prompt: str,
        temperature: float,
        max_tokens: int
    ) -> str:
        """Chat with Gemini"""
        
        # Convert messages to Gemini format
        history = []
        for msg in messages[:-1]:
            role = "model" if msg["role"] == "assistant" else "user"
            history.append({"role": role, "parts": [msg["content"]]})
        
        # Create chat
        chat = self.gemini_model.start_chat(history=history)
        
        # Prepend system prompt to last message
        last_msg = messages[-1]["content"]
        if system_prompt:
            last_msg = f"{system_prompt}\n\n{last_msg}"
        
        # Generate response
        response = await chat.send_message_async(
            last_msg,
            generation_config={
                "temperature": temperature,
                "max_output_tokens": max_tokens
            }
        )
        
        return response.text


# Singleton
_router_instance: Optional[LLMRouter] = None


def get_llm_router() -> LLMRouter:
    """Get the LLM router singleton"""
    global _router_instance
    if _router_instance is None:
        _router_instance = LLMRouter()
    return _router_instance
