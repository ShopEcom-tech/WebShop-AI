//! Health check endpoints

use actix_web::{HttpResponse, Responder};
use serde_json::json;

/// Root endpoint - API info
pub async fn root() -> impl Responder {
    HttpResponse::Ok().json(json!({
        "name": "WebShop-AI Gateway",
        "version": "0.1.0",
        "status": "running",
        "language": "Rust (Actix-web)",
        "endpoints": {
            "health": "/api/health",
            "chat": "/api/chat",
            "agents": "/api/agents"
        },
        "agents": [
            {"name": "MARIE", "role": "Support Chatbot", "status": "active"},
            {"name": "JOHN", "role": "Social Media Manager", "status": "coming_soon"},
            {"name": "HUGO", "role": "Content Generator", "status": "coming_soon"},
            {"name": "LUCAS", "role": "Quote Generator", "status": "coming_soon"},
            {"name": "EMMA", "role": "Email Responder", "status": "coming_soon"},
            {"name": "NOAH", "role": "Analytics", "status": "coming_soon"}
        ]
    }))
}

/// Health check endpoint
pub async fn health_check() -> impl Responder {
    HttpResponse::Ok().json(json!({
        "status": "healthy",
        "timestamp": chrono::Utc::now().to_rfc3339(),
        "services": {
            "gateway": "up",
            "python_agents": "pending"
        }
    }))
}
