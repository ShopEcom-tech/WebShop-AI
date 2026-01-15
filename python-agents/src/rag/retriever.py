"""
RAG (Retrieval Augmented Generation) System
Vector-based knowledge retrieval for agents
"""

import json
import hashlib
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import structlog

logger = structlog.get_logger()


@dataclass
class Document:
    """A document in the knowledge base"""
    id: str
    content: str
    metadata: Dict[str, Any]
    embedding: Optional[List[float]] = None
    score: float = 0.0


@dataclass
class RAGResult:
    """Result from a RAG query"""
    query: str
    documents: List[Document]
    context: str  # Formatted context for LLM
    source_count: int


class KnowledgeBase:
    """
    In-memory knowledge base for Web Shop.
    In production, this would use Qdrant for vector search.
    """
    
    def __init__(self):
        self._documents: Dict[str, Document] = {}
        self._load_knowledge()
    
    def _load_knowledge(self):
        """Load Web Shop knowledge base"""
        
        # FAQ Knowledge
        faq_items = [
            {
                "question": "Quels sont vos tarifs ?",
                "answer": "Nos tarifs commencent à 299€ pour un site vitrine, 599€ pour un e-commerce, et 1299€ pour un site sur-mesure. Ces prix incluent l'hébergement pour 1 an.",
                "category": "pricing"
            },
            {
                "question": "Combien de temps pour créer un site ?",
                "answer": "Le délai dépend du type de projet : 2 semaines pour un site vitrine, 4 semaines pour un e-commerce, et 6+ semaines pour un site sur-mesure.",
                "category": "delivery"
            },
            {
                "question": "Proposez-vous la maintenance ?",
                "answer": "Oui, nous proposons un service de maintenance mensuel à 49€/mois incluant les mises à jour de sécurité, les sauvegardes, et le support technique.",
                "category": "maintenance"
            },
            {
                "question": "Quels moyens de paiement acceptez-vous ?",
                "answer": "Nous acceptons les paiements par carte bancaire (Stripe), virement bancaire, et PayPal. Un acompte de 30% est demandé à la commande.",
                "category": "payment"
            },
            {
                "question": "Le site sera-t-il optimisé pour mobile ?",
                "answer": "Oui, tous nos sites sont responsive et optimisés pour mobile, tablette et desktop. C'est inclus dans tous nos forfaits.",
                "category": "features"
            },
            {
                "question": "Proposez-vous l'hébergement ?",
                "answer": "Oui, l'hébergement est inclus pendant 1 an pour tous les forfaits. Ensuite, le renouvellement est à 99€/an pour l'hébergement standard.",
                "category": "hosting"
            },
            {
                "question": "Puis-je voir des exemples de vos réalisations ?",
                "answer": "Bien sûr ! Nous avons livré plus de 50 projets. Vous pouvez consulter notre portfolio sur notre site ou demander des exemples spécifiques à votre secteur.",
                "category": "portfolio"
            },
            {
                "question": "Comment fonctionne le processus de création ?",
                "answer": "Le processus comprend : 1) Consultation initiale, 2) Maquette et validation, 3) Développement, 4) Tests et révisions, 5) Mise en ligne. Vous êtes impliqué à chaque étape.",
                "category": "process"
            },
            {
                "question": "Quelle est votre politique de remboursement ?",
                "answer": "L'acompte de 30% n'est pas remboursable une fois le travail commencé. Cependant, nous garantissons votre satisfaction avec des révisions illimitées sur la maquette.",
                "category": "refund"
            },
            {
                "question": "Faites-vous le référencement (SEO) ?",
                "answer": "Le SEO de base est inclus dans tous nos forfaits. Pour un référencement avancé (audit, stratégie, backlinks), nous proposons un pack SEO à 150€ en supplément.",
                "category": "seo"
            }
        ]
        
        # Services détaillés
        services = [
            {
                "name": "Site Vitrine",
                "price": 299,
                "description": "Idéal pour présenter votre activité en ligne. Inclut 5 pages, design responsive, SEO de base, et hébergement 1 an.",
                "features": ["5 pages maximum", "Design responsive", "SEO de base", "Formulaire de contact", "Hébergement 1 an"],
                "delivery": "2 semaines"
            },
            {
                "name": "Site E-commerce",
                "price": 599,
                "description": "Boutique en ligne complète avec paiement sécurisé. Jusqu'à 100 produits, gestion des stocks, et tableau de bord admin.",
                "features": ["100 produits max", "Paiement Stripe/PayPal", "Gestion des stocks", "Tableau de bord", "Hébergement 1 an"],
                "delivery": "4 semaines"
            },
            {
                "name": "Site Sur-mesure",
                "price": 1299,
                "description": "Solution personnalisée pour des besoins complexes. Architecture sur-mesure, intégrations API, et fonctionnalités avancées.",
                "features": ["Architecture personnalisée", "Intégrations API", "Fonctionnalités sur-mesure", "Maintenance premium", "Support prioritaire"],
                "delivery": "6+ semaines"
            }
        ]
        
        # Add FAQ items
        for i, item in enumerate(faq_items):
            doc_id = f"faq_{i}"
            self._documents[doc_id] = Document(
                id=doc_id,
                content=f"Q: {item['question']}\nR: {item['answer']}",
                metadata={"type": "faq", "category": item["category"]}
            )
        
        # Add services
        for i, service in enumerate(services):
            doc_id = f"service_{i}"
            features_str = ", ".join(service["features"])
            content = (
                f"Service: {service['name']}\n"
                f"Prix: {service['price']}€\n"
                f"Description: {service['description']}\n"
                f"Fonctionnalités: {features_str}\n"
                f"Délai: {service['delivery']}"
            )
            self._documents[doc_id] = Document(
                id=doc_id,
                content=content,
                metadata={"type": "service", "name": service["name"], "price": service["price"]}
            )
        
        logger.info(f"Loaded {len(self._documents)} documents into knowledge base")
    
    def search(self, query: str, top_k: int = 3) -> List[Document]:
        """
        Search for relevant documents.
        Uses simple keyword matching (BM25-like).
        In production, use vector embeddings + Qdrant.
        """
        query_lower = query.lower()
        query_words = set(query_lower.split())
        
        scored_docs = []
        
        for doc in self._documents.values():
            content_lower = doc.content.lower()
            
            # Simple scoring: count matching words
            score = 0.0
            for word in query_words:
                if word in content_lower:
                    score += 1.0
                    # Boost for exact phrase
                    if word in ["prix", "tarif", "coût"]:
                        if "pricing" in doc.metadata.get("category", ""):
                            score += 2.0
                    if word in ["délai", "temps", "combien"]:
                        if "delivery" in doc.metadata.get("category", ""):
                            score += 2.0
            
            if score > 0:
                doc_copy = Document(
                    id=doc.id,
                    content=doc.content,
                    metadata=doc.metadata,
                    score=score
                )
                scored_docs.append(doc_copy)
        
        # Sort by score and return top_k
        scored_docs.sort(key=lambda d: d.score, reverse=True)
        return scored_docs[:top_k]


class RAGRetriever:
    """
    RAG Retriever for augmenting agent responses with knowledge.
    """
    
    def __init__(self, knowledge_base: Optional[KnowledgeBase] = None):
        self.kb = knowledge_base or KnowledgeBase()
    
    async def retrieve(self, query: str, top_k: int = 3) -> RAGResult:
        """
        Retrieve relevant documents for a query.
        
        Args:
            query: User's question
            top_k: Number of documents to retrieve
            
        Returns:
            RAGResult with documents and formatted context
        """
        documents = self.kb.search(query, top_k)
        
        # Format context for LLM
        if documents:
            context_parts = ["Informations pertinentes de la base de connaissances:"]
            for i, doc in enumerate(documents, 1):
                context_parts.append(f"\n--- Document {i} ---")
                context_parts.append(doc.content)
            context = "\n".join(context_parts)
        else:
            context = ""
        
        logger.info(f"RAG retrieved {len(documents)} documents for query: {query[:50]}...")
        
        return RAGResult(
            query=query,
            documents=documents,
            context=context,
            source_count=len(documents)
        )
    
    def augment_prompt(self, system_prompt: str, rag_result: RAGResult) -> str:
        """
        Augment a system prompt with RAG context.
        
        Args:
            system_prompt: Original system prompt
            rag_result: RAG retrieval result
            
        Returns:
            Augmented system prompt
        """
        if not rag_result.context:
            return system_prompt
        
        return (
            f"{system_prompt}\n\n"
            f"---\n"
            f"CONTEXTE SUPPLÉMENTAIRE (utilise ces informations pour répondre avec précision):\n"
            f"{rag_result.context}"
        )


# Singleton
_retriever: Optional[RAGRetriever] = None


def get_rag_retriever() -> RAGRetriever:
    """Get the RAG retriever singleton"""
    global _retriever
    if _retriever is None:
        _retriever = RAGRetriever()
    return _retriever
