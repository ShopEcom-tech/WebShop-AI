"""
MARIE - Support Chatbot Agent
Primary customer support agent for Web Shop
"""

from typing import List, Dict, Any
import structlog

from .base import BaseAgent, AgentConfig
from ..orchestrator import AgentState

logger = structlog.get_logger()


MARIE_SYSTEM_PROMPT = """Tu es MARIE, l'assistante virtuelle de Web Shop, une agence web premium française spécialisée dans la création de sites web modernes et performants.

🎯 TA MISSION:
Aider les clients potentiels et existants avec leurs questions sur nos services, tout en étant chaleureuse, professionnelle et efficace.

📦 SERVICES WEB SHOP:
1. Site Vitrine - À partir de 299€
   • 5 pages maximum
   • Design responsive
   • SEO de base
   • Hébergement 1 an offert
   • Livraison: 2 semaines

2. Site E-commerce - À partir de 599€
   • Jusqu'à 100 produits
   • Paiement Stripe/PayPal
   • Gestion des stocks
   • Tableau de bord admin
   • Livraison: 4 semaines

3. Site Sur-mesure - À partir de 1299€
   • Architecture personnalisée
   • Fonctionnalités sur-mesure
   • Intégrations API tierces
   • Maintenance premium
   • Livraison: 6+ semaines

💡 RÈGLES IMPORTANTES:
1. Réponds TOUJOURS en français, sauf si le client écrit en anglais
2. Sois concise - 2-3 phrases maximum par réponse
3. Si on te demande un devis précis → suggère le formulaire de contact
4. Pour les questions techniques complexes → propose un appel avec l'équipe
5. N'invente JAMAIS de délais ou prix non listés ci-dessus
6. Termine souvent par une question pour maintenir la conversation
7. Si tu ne sais pas → dis-le honnêtement et propose de contacter un humain

📊 INFOS UTILES:
- +50 projets livrés
- 98% clients satisfaits
- Support sous 24h
- Basé en France

😊 TON TON:
Professionnel mais chaleureux. Tu es là pour aider, pas pour vendre agressivement.
Utilise des emojis avec modération (1-2 max par réponse).
"""


class MarieAgent(BaseAgent):
    """
    MARIE - Support Chatbot Agent
    
    Handles customer inquiries, FAQ, and general support.
    Can escalate to human if needed.
    """
    
    def __init__(self):
        config = AgentConfig(
            name="MARIE",
            role="Support Chatbot",
            description="Agent de support client 24/7 pour Web Shop",
            temperature=0.7,
            max_tokens=500  # Keep responses concise
        )
        super().__init__(config)
        
        # Keywords that trigger escalation to human
        self.escalation_keywords = [
            "parler à un humain",
            "humain",
            "agent",
            "plainte",
            "problème grave",
            "remboursement",
            "urgent",
            "talk to human",
            "real person"
        ]
    
    def get_system_prompt(self) -> str:
        """Get MARIE's system prompt"""
        return MARIE_SYSTEM_PROMPT
    
    async def process(self, state: AgentState) -> str:
        """
        Process user message and generate response.
        
        Args:
            state: Agent state with user input
            
        Returns:
            MARIE's response
        """
        user_message = self._extract_user_message(state)
        logger.info(f"MARIE processing: {user_message[:50]}...")
        
        # Check for escalation
        if self._should_escalate(user_message):
            state.should_escalate = True
            return self._get_escalation_response()
        
        # Build conversation
        history = self._get_conversation_history(state)
        history.append({"role": "user", "content": user_message})
        
        try:
            response = await self.invoke_llm(history)
            logger.info(f"MARIE response generated: {response[:50]}...")
            return response
        except Exception as e:
            logger.error(f"MARIE error: {e}")
            return self._get_fallback_response()
    
    def _should_escalate(self, message: str) -> bool:
        """Check if message should be escalated to human"""
        message_lower = message.lower()
        return any(kw in message_lower for kw in self.escalation_keywords)
    
    def _get_escalation_response(self) -> str:
        """Response when escalating to human"""
        return (
            "Je comprends que vous souhaitez parler à un membre de notre équipe. 👤\n\n"
            "Vous pouvez nous contacter directement :\n"
            "📧 Email: contact@webshop.fr\n"
            "📞 Téléphone: +33 1 23 45 67 89\n"
            "💬 WhatsApp: +33 6 12 34 56 78\n\n"
            "Un conseiller vous répondra sous 24h. "
            "Puis-je vous aider avec autre chose en attendant ?"
        )
    
    def _get_fallback_response(self) -> str:
        """Fallback response when LLM fails"""
        return (
            "Je suis désolée, je rencontre un petit souci technique. 😅\n\n"
            "En attendant, vous pouvez consulter notre site webshop.fr "
            "ou nous contacter à contact@webshop.fr.\n\n"
            "Puis-je réessayer de vous aider ?"
        )


# Singleton instance
_marie_instance = None


def get_marie_agent() -> MarieAgent:
    """Get MARIE agent instance"""
    global _marie_instance
    if _marie_instance is None:
        _marie_instance = MarieAgent()
    return _marie_instance
