/**
 * Chat API Routes
 */

import { FastifyInstance, FastifyRequest, FastifyReply } from 'fastify';
import { ChatbotAgent } from '../../agents/chatbot/index.js';

interface ChatBody {
  message: string;
  sessionId: string;
  language?: 'fr' | 'en';
  customerName?: string;
}

export async function chatRoutes(fastify: FastifyInstance) {
  const chatbot = new ChatbotAgent();

  // POST /api/chat - Send a message
  fastify.post('/api/chat', async (
    request: FastifyRequest<{ Body: ChatBody }>,
    reply: FastifyReply
  ) => {
    try {
      const { message, sessionId, language = 'fr', customerName } = request.body;

      if (!message || !sessionId) {
        return reply.status(400).send({
          error: 'message and sessionId are required',
        });
      }

      const response = await chatbot.respond(message, {
        sessionId,
        language,
        customerName,
      });

      return reply.send({
        success: true,
        data: response,
      });
    } catch (error) {
      console.error('Chat error:', error);
      return reply.status(500).send({
        error: 'Failed to process message',
        details: error instanceof Error ? error.message : 'Unknown error',
      });
    }
  });

  // GET /api/chat/history/:sessionId - Get conversation history
  fastify.get('/api/chat/history/:sessionId', async (
    request: FastifyRequest<{ Params: { sessionId: string } }>,
    reply: FastifyReply
  ) => {
    const { sessionId } = request.params;
    const history = chatbot.getHistory(sessionId);
    
    return reply.send({
      success: true,
      data: {
        sessionId,
        messages: history,
        count: history.length,
      },
    });
  });

  // DELETE /api/chat/history/:sessionId - Clear conversation
  fastify.delete('/api/chat/history/:sessionId', async (
    request: FastifyRequest<{ Params: { sessionId: string } }>,
    reply: FastifyReply
  ) => {
    const { sessionId } = request.params;
    chatbot.clearHistory(sessionId);
    
    return reply.send({
      success: true,
      message: 'Conversation cleared',
    });
  });

  // GET /api/chat/health - Health check
  fastify.get('/api/chat/health', async (_request, reply) => {
    return reply.send({
      status: 'ok',
      agent: 'chatbot',
      timestamp: new Date().toISOString(),
    });
  });
}

export default chatRoutes;
