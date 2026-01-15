//! Chat route handlers

use actix_web::{web, HttpResponse, Responder};
use serde::{Deserialize, Serialize};
use crate::AppState;

#[derive(Deserialize)]
pub struct ChatRequest {
    pub message: String,
    pub session_id: String,
    pub language: Option<String>,
    pub agent: Option<String>,
}

#[derive(Serialize)]
pub struct ChatResponse {
    pub success: bool,
    pub data: Option<ChatData>,
    pub error: Option<String>,
}

#[derive(Serialize)]
pub struct ChatData {
    pub message: String,
    pub agent: String,
    pub session_id: String,
    pub timestamp: String,
}

/// Send a message to the chatbot
pub async fn send_message(
    state: web::Data<AppState>,
    body: web::Json<ChatRequest>,
) -> impl Responder {
    let agent = body.agent.clone().unwrap_or_else(|| "marie".to_string());
    
    // Forward to Python agent orchestrator
    let client = reqwest::Client::new();
    let python_url = format!("{}/agents/{}/chat", state.agent_url, agent);
    
    let payload = serde_json::json!({
        "message": body.message,
        "session_id": body.session_id,
        "language": body.language.clone().unwrap_or_else(|| "fr".to_string())
    });
    
    match client.post(&python_url)
        .json(&payload)
        .send()
        .await
    {
        Ok(response) => {
            match response.json::<serde_json::Value>().await {
                Ok(data) => HttpResponse::Ok().json(ChatResponse {
                    success: true,
                    data: Some(ChatData {
                        message: data["message"].as_str().unwrap_or("").to_string(),
                        agent: agent.to_uppercase(),
                        session_id: body.session_id.clone(),
                        timestamp: chrono::Utc::now().to_rfc3339(),
                    }),
                    error: None,
                }),
                Err(e) => HttpResponse::InternalServerError().json(ChatResponse {
                    success: false,
                    data: None,
                    error: Some(format!("Failed to parse response: {}", e)),
                }),
            }
        },
        Err(e) => {
            // Fallback response when Python agents are not available
            tracing::warn!("Python agents unavailable: {}", e);
            HttpResponse::Ok().json(ChatResponse {
                success: true,
                data: Some(ChatData {
                    message: "Je suis MARIE, l'assistante de Web Shop. Les services Python sont en cours de démarrage. En attendant, comment puis-je vous aider ?".to_string(),
                    agent: "MARIE".to_string(),
                    session_id: body.session_id.clone(),
                    timestamp: chrono::Utc::now().to_rfc3339(),
                }),
                error: None,
            })
        }
    }
}

/// Get conversation history
pub async fn get_history(
    path: web::Path<String>,
) -> impl Responder {
    let session_id = path.into_inner();
    HttpResponse::Ok().json(serde_json::json!({
        "session_id": session_id,
        "messages": [],
        "count": 0
    }))
}

/// Clear conversation history
pub async fn clear_history(
    path: web::Path<String>,
) -> impl Responder {
    let session_id = path.into_inner();
    HttpResponse::Ok().json(serde_json::json!({
        "success": true,
        "message": format!("Session {} cleared", session_id)
    }))
}
