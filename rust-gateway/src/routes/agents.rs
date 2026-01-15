//! Agent management endpoints

use actix_web::{web, HttpResponse, Responder};
use serde::{Deserialize, Serialize};
use crate::AppState;

#[derive(Serialize)]
pub struct Agent {
    pub id: String,
    pub name: String,
    pub role: String,
    pub status: String,
    pub description: String,
    pub capabilities: Vec<String>,
}

/// List all available agents
pub async fn list_agents() -> impl Responder {
    let agents = vec![
        Agent {
            id: "marie".to_string(),
            name: "MARIE".to_string(),
            role: "Support Chatbot".to_string(),
            status: "active".to_string(),
            description: "Agent de support client 24/7, répond aux questions et escalade si nécessaire".to_string(),
            capabilities: vec![
                "Réponses contextuelles".to_string(),
                "Multi-langue (FR/EN)".to_string(),
                "Mémoire de conversation".to_string(),
                "Escalade vers humain".to_string(),
            ],
        },
        Agent {
            id: "john".to_string(),
            name: "JOHN".to_string(),
            role: "Social Media Manager".to_string(),
            status: "coming_soon".to_string(),
            description: "Gère les réseaux sociaux, crée et publie du contenu".to_string(),
            capabilities: vec![
                "Génération de posts".to_string(),
                "Création de visuels".to_string(),
                "Planification automatique".to_string(),
                "LinkedIn, Instagram, TikTok".to_string(),
            ],
        },
        Agent {
            id: "hugo".to_string(),
            name: "HUGO".to_string(),
            role: "Content Generator".to_string(),
            status: "coming_soon".to_string(),
            description: "Génère du contenu marketing et SEO".to_string(),
            capabilities: vec![
                "Articles de blog SEO".to_string(),
                "Descriptions produits".to_string(),
                "Emails marketing".to_string(),
                "Traduction multi-langues".to_string(),
            ],
        },
        Agent {
            id: "lucas".to_string(),
            name: "LUCAS".to_string(),
            role: "Quote Generator".to_string(),
            status: "coming_soon".to_string(),
            description: "Crée des devis personnalisés automatiquement".to_string(),
            capabilities: vec![
                "Analyse des besoins".to_string(),
                "Calcul de prix intelligent".to_string(),
                "Export PDF".to_string(),
                "Envoi automatique".to_string(),
            ],
        },
        Agent {
            id: "emma".to_string(),
            name: "EMMA".to_string(),
            role: "Email Responder".to_string(),
            status: "coming_soon".to_string(),
            description: "Gère et répond aux emails automatiquement".to_string(),
            capabilities: vec![
                "Connexion Gmail/Outlook".to_string(),
                "Catégorisation auto".to_string(),
                "Réponses intelligentes".to_string(),
                "Détection d'urgence".to_string(),
            ],
        },
        Agent {
            id: "noah".to_string(),
            name: "NOAH".to_string(),
            role: "Analytics & Insights".to_string(),
            status: "coming_soon".to_string(),
            description: "Analyse les données et génère des insights".to_string(),
            capabilities: vec![
                "Tableaux de bord".to_string(),
                "Rapports automatiques".to_string(),
                "Prédictions".to_string(),
                "Alertes intelligentes".to_string(),
            ],
        },
    ];

    HttpResponse::Ok().json(serde_json::json!({
        "agents": agents,
        "total": agents.len()
    }))
}

#[derive(Deserialize)]
pub struct InvokeRequest {
    pub action: String,
    pub params: serde_json::Value,
}

/// Invoke a specific agent
pub async fn invoke_agent(
    state: web::Data<AppState>,
    path: web::Path<String>,
    body: web::Json<InvokeRequest>,
) -> impl Responder {
    let agent_id = path.into_inner();
    
    // Forward to Python orchestrator
    let client = reqwest::Client::new();
    let python_url = format!("{}/agents/{}/invoke", state.agent_url, agent_id);
    
    match client.post(&python_url)
        .json(&*body)
        .send()
        .await
    {
        Ok(response) => {
            match response.json::<serde_json::Value>().await {
                Ok(data) => HttpResponse::Ok().json(data),
                Err(e) => HttpResponse::InternalServerError().json(serde_json::json!({
                    "error": format!("Failed to parse response: {}", e)
                })),
            }
        },
        Err(e) => {
            HttpResponse::ServiceUnavailable().json(serde_json::json!({
                "error": format!("Agent {} unavailable: {}", agent_id, e)
            }))
        }
    }
}

/// Get agent status
pub async fn agent_status(
    path: web::Path<String>,
) -> impl Responder {
    let agent_id = path.into_inner();
    
    HttpResponse::Ok().json(serde_json::json!({
        "agent_id": agent_id,
        "status": "active",
        "uptime": "0d 0h 0m",
        "requests_handled": 0,
        "average_response_time_ms": 0
    }))
}
