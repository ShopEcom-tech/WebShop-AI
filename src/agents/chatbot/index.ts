/**
 * Chatbot Agent
 * Handles customer support conversations
 */

import { getLLMRouter, ChatMessage, LLMOptions } from '../../core/llm/index.js';

export interface ChatContext {
  sessionId: string;
  language?: 'fr' | 'en';
  customerName?: string;
}

export interface ChatResponse {
  message: string;
  provider: string;
  suggestions?: string[];
  shouldEscalate?: boolean;
}

// In-memory conversation store (replace with Redis in production)
const conversations: Map<string, ChatMessage[]> = new Map();

export const CHATBOT_PROMPTS = {
  system: {
    fr: `Tu es l'assistant virtuel de Web Shop, une agence web premium française spécialisée dans la création de sites web modernes.

SERVICES ET TARIFS:
- Site Vitrine: à partir de 299€ (livraison 2 semaines)
- E-commerce: à partir de 599€ (livraison 4 semaines)  
- Sur-mesure: à partir de 1299€ (livraison 6+ semaines)

RÈGLES IMPORTANTES:
1. Réponds toujours en français de manière professionnelle mais chaleureuse
2. Sois concis - maximum 2-3 phrases par réponse
3. Si le client veut un devis précis, suggère de remplir le formulaire de contact
4. Pour les questions techniques complexes, propose de les mettre en relation avec un expert
5. N'invente jamais d'informations sur les délais ou prix exacts
6. Termine souvent par une question pour engager la conversation

INFORMATIONS UTILES:
- Support réactif sous 24h
- 50+ projets livrés
- 98% de clients satisfaits
- Basé en France`,

    en: `You are the virtual assistant of Web Shop, a premium French web agency specializing in modern website creation.

SERVICES AND PRICING:
- Showcase Site: from €299 (2 weeks delivery)
- E-commerce: from €599 (4 weeks delivery)
- Custom Build: from €1299 (6+ weeks delivery)

IMPORTANT RULES:
1. Always respond professionally but warmly in English
2. Be concise - maximum 2-3 sentences per response
3. If the client wants a precise quote, suggest filling out the contact form
4. For complex technical questions, offer to connect them with an expert
5. Never invent information about exact deadlines or prices
6. Often end with a question to engage the conversation

USEFUL INFORMATION:
- Responsive support within 24h
- 50+ projects delivered
- 98% satisfied clients
- Based in France`,
  },

  suggestions: {
    fr: [
      'Quels sont vos tarifs ?',
      'Combien de temps pour créer un site ?',
      'Puis-je voir des exemples ?',
      'Je voudrais un devis',
    ],
    en: [
      'What are your prices?',
      'How long to create a website?',
      'Can I see examples?',
      'I would like a quote',
    ],
  },
};

export class ChatbotAgent {
  private router = getLLMRouter();

  /**
   * Process a user message and return a response
   */
  async respond(
    message: string,
    context: ChatContext
  ): Promise<ChatResponse> {
    const { sessionId, language = 'fr' } = context;

    // Get or create conversation history
    const history = this.getHistory(sessionId);
    
    // Add user message to history
    history.push({ role: 'user', content: message });

    // Check for escalation keywords
    const shouldEscalate = this.checkEscalation(message);

    // Get LLM response
    const options: LLMOptions = {
      systemPrompt: CHATBOT_PROMPTS.system[language],
      maxTokens: 500,
      temperature: 0.7,
    };

    const result = await this.router.chat(history, options);

    // Add assistant response to history
    history.push({ role: 'assistant', content: result.response });

    // Save updated history
    this.saveHistory(sessionId, history);

    return {
      message: result.response,
      provider: result.provider,
      suggestions: CHATBOT_PROMPTS.suggestions[language],
      shouldEscalate,
    };
  }

  /**
   * Get conversation history for a session
   */
  getHistory(sessionId: string): ChatMessage[] {
    return conversations.get(sessionId) || [];
  }

  /**
   * Save conversation history
   */
  private saveHistory(sessionId: string, history: ChatMessage[]): void {
    // Keep only last 20 messages to manage memory
    const trimmedHistory = history.slice(-20);
    conversations.set(sessionId, trimmedHistory);
  }

  /**
   * Clear conversation history
   */
  clearHistory(sessionId: string): void {
    conversations.delete(sessionId);
  }

  /**
   * Check if message requires human escalation
   */
  private checkEscalation(message: string): boolean {
    const escalationKeywords = [
      'parler à un humain',
      'talk to human',
      'agent',
      'plainte',
      'complaint',
      'urgent',
      'problème grave',
      'serious problem',
      'remboursement',
      'refund',
    ];

    const lowerMessage = message.toLowerCase();
    return escalationKeywords.some((keyword) =>
      lowerMessage.includes(keyword)
    );
  }
}

export default ChatbotAgent;
