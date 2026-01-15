//! Route configuration

use actix_web::web;

pub mod health;
pub mod chat;
pub mod agents;

/// Configure all routes
pub fn configure(cfg: &mut web::ServiceConfig) {
    cfg.service(
        web::scope("/api")
            // Health check
            .route("/health", web::get().to(health::health_check))
            
            // Chat endpoints
            .route("/chat", web::post().to(chat::send_message))
            .route("/chat/history/{session_id}", web::get().to(chat::get_history))
            .route("/chat/history/{session_id}", web::delete().to(chat::clear_history))
            
            // Agent endpoints
            .route("/agents", web::get().to(agents::list_agents))
            .route("/agents/{agent_id}/invoke", web::post().to(agents::invoke_agent))
            .route("/agents/{agent_id}/status", web::get().to(agents::agent_status))
    );
    
    // Root endpoint
    cfg.route("/", web::get().to(health::root));
}
