//! WebShop-AI Gateway - High Performance API Gateway
//! 
//! This is the entry point for the Rust-based API gateway that handles
//! all incoming requests and routes them to the Python agent orchestrator.

use actix_cors::Cors;
use actix_web::{web, App, HttpServer, middleware};
use tracing::info;
use tracing_subscriber::{layer::SubscriberExt, util::SubscriberInitExt};
use std::env;

mod routes;
mod middleware as mw;
mod models;

/// Application state shared across all handlers
pub struct AppState {
    pub agent_url: String,
    pub jwt_secret: String,
}

#[actix_web::main]
async fn main() -> std::io::Result<()> {
    // Load environment variables
    dotenvy::dotenv().ok();
    
    // Initialize tracing/logging
    tracing_subscriber::registry()
        .with(tracing_subscriber::EnvFilter::new(
            env::var("RUST_LOG").unwrap_or_else(|_| "info,actix_web=debug".into())
        ))
        .with(tracing_subscriber::fmt::layer())
        .init();

    let host = env::var("HOST").unwrap_or_else(|_| "0.0.0.0".to_string());
    let port = env::var("PORT").unwrap_or_else(|_| "8080".to_string());
    let agent_url = env::var("AGENT_URL").unwrap_or_else(|_| "http://localhost:8000".to_string());
    let jwt_secret = env::var("JWT_SECRET").unwrap_or_else(|_| "super-secret-key".to_string());
    
    let bind_addr = format!("{}:{}", host, port);
    
    info!("🦀 WebShop-AI Gateway starting...");
    info!("📍 Listening on: http://{}", bind_addr);
    info!("🐍 Python agents at: {}", agent_url);

    let app_state = web::Data::new(AppState {
        agent_url,
        jwt_secret,
    });

    HttpServer::new(move || {
        // CORS configuration
        let cors = Cors::default()
            .allow_any_origin()
            .allow_any_method()
            .allow_any_header()
            .max_age(3600);

        App::new()
            .app_data(app_state.clone())
            // Middleware
            .wrap(cors)
            .wrap(middleware::Logger::default())
            .wrap(tracing_actix_web::TracingLogger::default())
            // Routes
            .configure(routes::configure)
    })
    .bind(&bind_addr)?
    .workers(num_cpus::get())
    .run()
    .await
}
