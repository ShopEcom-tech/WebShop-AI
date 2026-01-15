/**
 * Gemini API Wrapper
 * Fallback LLM for WebShop-AI
 */

import { GoogleGenerativeAI, GenerativeModel } from '@google/generative-ai';

export interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
}

export interface GeminiOptions {
  maxTokens?: number;
  temperature?: number;
  systemPrompt?: string;
}

export class GeminiClient {
  private client: GoogleGenerativeAI;
  private model: GenerativeModel;

  constructor(apiKey?: string) {
    this.client = new GoogleGenerativeAI(
      apiKey || process.env.GOOGLE_AI_API_KEY || ''
    );
    this.model = this.client.getGenerativeModel({ model: 'gemini-pro' });
  }

  /**
   * Send a message to Gemini and get a response
   */
  async chat(
    messages: ChatMessage[],
    options: GeminiOptions = {}
  ): Promise<string> {
    const { systemPrompt } = options;

    try {
      // Convert messages to Gemini format
      const history = messages.slice(0, -1).map((m) => ({
        role: m.role === 'assistant' ? 'model' : 'user',
        parts: [{ text: m.content }],
      }));

      const lastMessage = messages[messages.length - 1];
      
      // Start chat with history
      const chat = this.model.startChat({
        history: history as any,
        generationConfig: {
          maxOutputTokens: options.maxTokens || 2048,
          temperature: options.temperature || 0.7,
        },
      });

      // Prepend system prompt to first message if provided
      const prompt = systemPrompt
        ? `${systemPrompt}\n\n${lastMessage.content}`
        : lastMessage.content;

      const result = await chat.sendMessage(prompt);
      const response = await result.response;
      return response.text();
    } catch (error) {
      console.error('Gemini API Error:', error);
      throw new Error(`Gemini API failed: ${error}`);
    }
  }

  /**
   * Simple single-message query
   */
  async ask(prompt: string, systemPrompt?: string): Promise<string> {
    return this.chat([{ role: 'user', content: prompt }], { systemPrompt });
  }

  /**
   * Stream a response
   */
  async *stream(
    messages: ChatMessage[],
    options: GeminiOptions = {}
  ): AsyncGenerator<string> {
    const { systemPrompt } = options;

    const history = messages.slice(0, -1).map((m) => ({
      role: m.role === 'assistant' ? 'model' : 'user',
      parts: [{ text: m.content }],
    }));

    const lastMessage = messages[messages.length - 1];

    const chat = this.model.startChat({
      history: history as any,
      generationConfig: {
        maxOutputTokens: options.maxTokens || 2048,
        temperature: options.temperature || 0.7,
      },
    });

    const prompt = systemPrompt
      ? `${systemPrompt}\n\n${lastMessage.content}`
      : lastMessage.content;

    const result = await chat.sendMessageStream(prompt);

    for await (const chunk of result.stream) {
      yield chunk.text();
    }
  }
}

export default GeminiClient;
