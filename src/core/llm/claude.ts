/**
 * Claude API Wrapper
 * Primary LLM for WebShop-AI
 */

import Anthropic from '@anthropic-ai/sdk';

export interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
}

export interface ClaudeOptions {
  maxTokens?: number;
  temperature?: number;
  systemPrompt?: string;
}

export class ClaudeClient {
  private client: Anthropic;
  private model = 'claude-sonnet-4-20250514';

  constructor(apiKey?: string) {
    this.client = new Anthropic({
      apiKey: apiKey || process.env.ANTHROPIC_API_KEY,
    });
  }

  /**
   * Send a message to Claude and get a response
   */
  async chat(
    messages: ChatMessage[],
    options: ClaudeOptions = {}
  ): Promise<string> {
    const { maxTokens = 2048, temperature = 0.7, systemPrompt } = options;

    try {
      const response = await this.client.messages.create({
        model: this.model,
        max_tokens: maxTokens,
        temperature,
        system: systemPrompt || this.getDefaultSystemPrompt(),
        messages: messages.map((m) => ({
          role: m.role,
          content: m.content,
        })),
      });

      // Extract text from response
      const textBlock = response.content.find((block) => block.type === 'text');
      return textBlock ? textBlock.text : '';
    } catch (error) {
      console.error('Claude API Error:', error);
      throw new Error(`Claude API failed: ${error}`);
    }
  }

  /**
   * Simple single-message query
   */
  async ask(prompt: string, systemPrompt?: string): Promise<string> {
    return this.chat([{ role: 'user', content: prompt }], { systemPrompt });
  }

  /**
   * Stream a response (for real-time chat)
   */
  async *stream(
    messages: ChatMessage[],
    options: ClaudeOptions = {}
  ): AsyncGenerator<string> {
    const { maxTokens = 2048, temperature = 0.7, systemPrompt } = options;

    const stream = await this.client.messages.create({
      model: this.model,
      max_tokens: maxTokens,
      temperature,
      system: systemPrompt || this.getDefaultSystemPrompt(),
      messages: messages.map((m) => ({
        role: m.role,
        content: m.content,
      })),
      stream: true,
    });

    for await (const event of stream) {
      if (
        event.type === 'content_block_delta' &&
        event.delta.type === 'text_delta'
      ) {
        yield event.delta.text;
      }
    }
  }

  private getDefaultSystemPrompt(): string {
    return `Tu es un assistant IA pour Web Shop, une agence web premium française.
    
Règles:
- Réponds toujours en français sauf si le client parle anglais
- Sois professionnel mais chaleureux
- Aide les clients avec leurs questions sur les services web
- Pour les devis détaillés, suggère de contacter l'équipe`;
  }
}

export default ClaudeClient;
