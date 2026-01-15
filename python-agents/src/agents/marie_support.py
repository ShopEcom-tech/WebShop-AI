"""
MARIE - Support Chatbot Agent v2.0
Enhanced with RAG, Tools, Memory, Sentiment Analysis, and Guardrails
"""

from typing import List, Dict, Any, Optional
import structlog

from .base import BaseAgent, AgentConfig
from ..orchestrator import AgentState
from ..rag import get_rag_retriever
from ..memory import get_conversation_memory, get_short_term_memory
from ..analysis import get_text_analyzer, Sentiment, Intent
from ..guardrails import get_guardrails
from ..tools import get_tool, PriceCalculatorTool

logger = structlog.get_logger()


MARIE_SYSTEM_PROMPT_V2 = """Tu es MARIE, l'assistante virtuelle de Web Shop, une agence web premium française.

🎯 TA PERSONNALITÉ:
- Prénom: Marie
- Âge apparent: 28 ans
- Tonalité: Professionnelle, chaleureuse, empathique
- Tu parles comme une vraie conseillère clientèle, pas comme un robot

📦 SERVICES WEB SHOP:
• Site Vitrine: 299€ (5 pages, 2 semaines)
• Site E-commerce: 599€ (100 produits, 4 semaines)
• Site Sur-mesure: 1299€ (personnalisé, 6+ semaines)

Options: SEO (150€), Maintenance (49€/mois), Multilangue (200€), Blog (100€)

💡 RÈGLES D'OR:
1. Réponds en français (anglais si le client parle anglais)
2. Sois concise: 2-4 phrases maximum
3. Utilise 1-2 emojis par message (pas plus)
4. Pose une question de suivi pour engager la conversation
5. Si tu ne sais pas: propose de contacter l'équipe
6. N'invente JAMAIS de prix ou délais
7. Adapte ton ton au sentiment du client

🎭 ADAPTATION AU SENTIMENT:
- Client positif → Sois enthousiaste et chaleureuse
- Client neutre → Sois professionnelle et informative
- Client frustré → Sois empathique, excuse-toi, propose des solutions
- Client pressé → Sois directe et efficace

📞 CONTACT WEB SHOP:
- Email: contact@webshop.fr
- Téléphone: +33 1 23 45 67 89
- WhatsApp: +33 6 12 34 56 78
"""


class MarieAgentV2(BaseAgent):
    """
    MARIE - Enhanced Support Chatbot Agent v2.0
    
    Features:
    - RAG for knowledge retrieval
    - Sentiment-adaptive responses
    - Tool usage (price calculator)
    - Conversation memory
    - Input/output guardrails
    """
    
    def __init__(self):
        config = AgentConfig(
            name="MARIE",
            role="Support Chatbot",
            description="Agent de support client intelligent avec RAG, outils et analyse de sentiment",
            temperature=0.7,
            max_tokens=600
        )
        super().__init__(config)
        
        # Initialize components
        self.rag = get_rag_retriever()
        self.memory = get_conversation_memory()
        self.short_memory = get_short_term_memory()
        self.analyzer = get_text_analyzer()
        self.guardrails = get_guardrails()
        
        # Escalation keywords
        self.escalation_keywords = [
            "parler à un humain", "humain", "agent", "plainte",
            "problème grave", "remboursement", "urgent",
            "talk to human", "real person"
        ]
        
        logger.info("🤖 MARIE v2.0 initialized with all enhancements")
    
    def get_system_prompt(self) -> str:
        """Get MARIE's enhanced system prompt"""
        return MARIE_SYSTEM_PROMPT_V2
    
    async def process(self, state: AgentState) -> str:
        """
        Process user message with full enhancement pipeline.
        
        Pipeline:
        1. Input guardrails check
        2. Sentiment + Intent analysis
        3. RAG knowledge retrieval
        4. Tool usage if needed
        5. Memory context
        6. LLM generation
        7. Output guardrails check
        
        Args:
            state: Agent state with user input
            
        Returns:
            MARIE's enhanced response
        """
        user_message = self._extract_user_message(state)
        session_id = state.session_id
        
        logger.info(f"MARIE v2 processing: {user_message[:50]}...")
        
        # ==== 1. INPUT GUARDRAILS ====
        input_check = self.guardrails.check_input(user_message)
        if not input_check.passed:
            logger.warning(f"Input blocked: {input_check.issues}")
            return self._get_blocked_response()
        
        # Use sanitized input
        safe_message = input_check.sanitized_text or user_message
        
        # ==== 2. SENTIMENT & INTENT ANALYSIS ====
        analysis = self.analyzer.analyze(safe_message)
        
        # Store analysis in memory for context
        self.short_memory.store(
            session_id, 
            "last_sentiment", 
            analysis.sentiment.value
        )
        self.short_memory.store(
            session_id,
            "last_intent",
            analysis.intent.value
        )
        
        # Check if needs escalation
        if analysis.needs_human or self._should_escalate(safe_message):
            state.should_escalate = True
            return self._get_escalation_response(analysis.sentiment)
        
        # ==== 3. RAG KNOWLEDGE RETRIEVAL ====
        rag_result = await self.rag.retrieve(safe_message, top_k=3)
        
        # ==== 4. TOOL USAGE ====
        tool_context = ""
        if analysis.intent == Intent.ASKING_PRICE:
            tool_context = await self._use_price_tool(safe_message)
        
        # ==== 5. BUILD CONTEXT ====
        # Get conversation history
        self.memory.add_message(session_id, "user", safe_message)
        history = self.memory.get_messages(session_id, last_n=6)
        
        # Build enhanced system prompt
        system_prompt = self._build_enhanced_prompt(
            analysis=analysis,
            rag_context=rag_result.context,
            tool_context=tool_context
        )
        
        # ==== 6. LLM GENERATION ====
        try:
            # Convert history to LLM format
            llm_messages = [
                {"role": msg["role"], "content": msg["content"]}
                for msg in history
                if msg["role"] in ["user", "assistant"]
            ]
            
            response = await self.invoke_llm(llm_messages, system_prompt)
            
            # ==== 7. OUTPUT GUARDRAILS ====
            output_check = self.guardrails.check_output(response)
            if output_check.issues:
                logger.warning(f"Output issues: {output_check.issues}")
                # Still return but log the issues
            
            # Store in memory
            self.memory.add_message(session_id, "assistant", response)
            
            logger.info(f"MARIE v2 response: {response[:50]}...")
            return response
            
        except Exception as e:
            logger.error(f"MARIE v2 error: {e}")
            return self._get_fallback_response(analysis.sentiment)
    
    def _build_enhanced_prompt(
        self,
        analysis: Any,
        rag_context: str,
        tool_context: str
    ) -> str:
        """Build enhanced system prompt with context"""
        
        prompt_parts = [MARIE_SYSTEM_PROMPT_V2]
        
        # Add sentiment adaptation
        sentiment_instruction = self._get_sentiment_instruction(analysis.sentiment)
        if sentiment_instruction:
            prompt_parts.append(f"\n⚠️ ADAPTATION REQUISE:\n{sentiment_instruction}")
        
        # Add RAG context
        if rag_context:
            prompt_parts.append(f"\n📚 INFORMATIONS PERTINENTES:\n{rag_context}")
        
        # Add tool context
        if tool_context:
            prompt_parts.append(f"\n🔧 DONNÉES CALCULÉES:\n{tool_context}")
        
        return "\n".join(prompt_parts)
    
    def _get_sentiment_instruction(self, sentiment: Sentiment) -> str:
        """Get instruction based on sentiment"""
        instructions = {
            Sentiment.POSITIVE: "Le client est content! Sois enthousiaste et maintiens cette bonne énergie.",
            Sentiment.NEUTRAL: "Reste professionnelle et informative.",
            Sentiment.NEGATIVE: "Le client semble mécontent. Sois empathique et propose des solutions.",
            Sentiment.FRUSTRATED: "ATTENTION: Client frustré! Commence par t'excuser, sois très empathique, et propose immédiatement de l'aider ou de passer à un humain."
        }
        return instructions.get(sentiment, "")
    
    async def _use_price_tool(self, message: str) -> str:
        """Use price calculator if relevant"""
        message_lower = message.lower()
        
        # Detect service type
        service_type = None
        if any(w in message_lower for w in ["vitrine", "présentation", "simple"]):
            service_type = "vitrine"
        elif any(w in message_lower for w in ["ecommerce", "boutique", "vendre"]):
            service_type = "ecommerce"
        elif any(w in message_lower for w in ["sur-mesure", "personnalisé", "complexe"]):
            service_type = "surmesure"
        
        if not service_type:
            return ""
        
        # Use the tool
        tool = PriceCalculatorTool()
        result = await tool.run(service_type=service_type)
        
        if result.success:
            data = result.data
            return (
                f"Prix calculé pour {data['service_type']}: "
                f"{data['base_price']}€ (prix de base)\n"
                f"Options disponibles: SEO (+150€), Maintenance (+49€/mois), etc."
            )
        
        return ""
    
    def _should_escalate(self, message: str) -> bool:
        """Check if message should be escalated"""
        message_lower = message.lower()
        return any(kw in message_lower for kw in self.escalation_keywords)
    
    def _get_escalation_response(self, sentiment: Sentiment) -> str:
        """Generate escalation response adapted to sentiment"""
        if sentiment == Sentiment.FRUSTRATED:
            return (
                "Je suis sincèrement désolée pour cette situation. 😔\n\n"
                "Je vais immédiatement transférer votre demande à un membre de notre équipe "
                "qui pourra vous aider personnellement:\n\n"
                "📞 Téléphone: +33 1 23 45 67 89 (prioritaire)\n"
                "📧 Email: contact@webshop.fr\n"
                "💬 WhatsApp: +33 6 12 34 56 78\n\n"
                "Nous vous répondrons dans l'heure. Encore une fois, toutes mes excuses."
            )
        else:
            return (
                "Je comprends que vous préfériez parler à un membre de notre équipe. 👤\n\n"
                "Vous pouvez nous contacter:\n"
                "📧 Email: contact@webshop.fr\n"
                "📞 Téléphone: +33 1 23 45 67 89\n"
                "💬 WhatsApp: +33 6 12 34 56 78\n\n"
                "Un conseiller vous répondra sous 24h. "
                "Puis-je vous aider avec autre chose en attendant ?"
            )
    
    def _get_fallback_response(self, sentiment: Sentiment) -> str:
        """Fallback response when LLM fails, adapted to sentiment"""
        if sentiment == Sentiment.FRUSTRATED:
            return (
                "Je suis vraiment désolée, je rencontre un souci technique. 😔\n\n"
                "Pour vous aider au mieux, contactez directement notre équipe:\n"
                "📞 +33 1 23 45 67 89\n\n"
                "Nous nous excusons pour ce désagrément."
            )
        else:
            return (
                "Oups, j'ai un petit souci technique. 😅\n\n"
                "En attendant, vous pouvez:\n"
                "• Visiter notre site: webshop.fr\n"
                "• Nous contacter: contact@webshop.fr\n\n"
                "Puis-je réessayer de vous aider ?"
            )
    
    def _get_blocked_response(self) -> str:
        """Response when input is blocked"""
        return (
            "Je ne suis pas en mesure de traiter cette demande. 🙏\n\n"
            "Si vous avez une question sur nos services, "
            "je serai ravie de vous aider!"
        )


# Keep backward compatibility
MarieAgent = MarieAgentV2

# Singleton instance
_marie_instance = None


def get_marie_agent() -> MarieAgentV2:
    """Get MARIE v2 agent instance"""
    global _marie_instance
    if _marie_instance is None:
        _marie_instance = MarieAgentV2()
    return _marie_instance
