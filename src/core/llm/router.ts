/**
 * LLM Router
 * Routes requests to Claude (primary) with Gemini fallback
 */

import { ClaudeClient, ChatMessage as ClaudeMessage } from './claude.js';
import { GeminiClient } from './gemini.js';

export interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
}

export interface LLMOptions {
  maxTokens?: number;
  temperature?: number;
  systemPrompt?: string;
  preferredProvider?: 'claude' | 'gemini';
}

export class LLMRouter {
  private claude: ClaudeClient | null = null;
  private gemini: GeminiClient | null = null;

  constructor() {
    // Initialize available clients
    if (process.env.ANTHROPIC_API_KEY) {
      this.claude = new ClaudeClient();
      console.log('✅ Claude client initialized');
    }
    if (process.env.GOOGLE_AI_API_KEY) {
      this.gemini = new GeminiClient();
      console.log('✅ Gemini client initialized');
    }

    if (!this.claude && !this.gemini) {
      console.warn('⚠️ No LLM API keys configured!');
    }
  }

  /**
   * Send a chat message with automatic failover
   */
  async chat(
    messages: ChatMessage[],
    options: LLMOptions = {}
  ): Promise<{ response: string; provider: string }> {
    const { preferredProvider = 'claude' } = options;

    // Try preferred provider first
    if (preferredProvider === 'claude' && this.claude) {
      try {
        const response = await this.claude.chat(messages, options);
        return { response, provider: 'claude' };
      } catch (error) {
        console.warn('Claude failed, falling back to Gemini:', error);
      }
    }

    if (preferredProvider === 'gemini' && this.gemini) {
      try {
        const response = await this.gemini.chat(messages, options);
        return { response, provider: 'gemini' };
      } catch (error) {
        console.warn('Gemini failed, falling back to Claude:', error);
      }
    }

    // Fallback
    if (this.gemini && preferredProvider === 'claude') {
      const response = await this.gemini.chat(messages, options);
      return { response, provider: 'gemini' };
    }

    if (this.claude && preferredProvider === 'gemini') {
      const response = await this.claude.chat(messages, options);
      return { response, provider: 'claude' };
    }

    throw new Error('No LLM provider available');
  }

  /**
   * Simple ask with failover
   */
  async ask(
    prompt: string,
    options: LLMOptions = {}
  ): Promise<{ response: string; provider: string }> {
    return this.chat([{ role: 'user', content: prompt }], options);
  }

  /**
   * Check which providers are available
   */
  getAvailableProviders(): string[] {
    const providers: string[] = [];
    if (this.claude) providers.push('claude');
    if (this.gemini) providers.push('gemini');
    return providers;
  }
}

// Singleton instance
let routerInstance: LLMRouter | null = null;

export function getLLMRouter(): LLMRouter {
  if (!routerInstance) {
    routerInstance = new LLMRouter();
  }
  return routerInstance;
}

export default LLMRouter;
