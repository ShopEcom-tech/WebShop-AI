/**
 * WebShop-AI API Server
 */

import Fastify from 'fastify';
import cors from '@fastify/cors';
import 'dotenv/config';

import { chatRoutes } from './routes/chat.js';

const PORT = parseInt(process.env.PORT || '3000', 10);

async function start() {
  const fastify = Fastify({
    logger: true,
  });

  // CORS for frontend
  await fastify.register(cors, {
    origin: true, // Allow all origins in dev
    methods: ['GET', 'POST', 'DELETE', 'OPTIONS'],
  });

  // Register routes
  await fastify.register(chatRoutes);

  // Root endpoint
  fastify.get('/', async () => {
    return {
      name: 'WebShop-AI',
      version: '1.0.0',
      status: 'running',
      endpoints: {
        chat: '/api/chat',
        health: '/api/chat/health',
      },
    };
  });

  // Start server
  try {
    await fastify.listen({ port: PORT, host: '0.0.0.0' });
    console.log(`
🤖 WebShop-AI Server Started
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📍 URL: http://localhost:${PORT}
💬 Chat: POST /api/chat
📊 Health: GET /api/chat/health
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    `);
  } catch (err) {
    fastify.log.error(err);
    process.exit(1);
  }
}

start();
