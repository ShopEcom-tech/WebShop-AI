"""
Sentiment and Intent Analysis
Understand user emotions and intentions
"""

import re
from typing import List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import structlog

logger = structlog.get_logger()


class Sentiment(Enum):
    POSITIVE = "positive"
    NEUTRAL = "neutral"
    NEGATIVE = "negative"
    FRUSTRATED = "frustrated"


class Intent(Enum):
    GREETING = "greeting"
    ASKING_PRICE = "asking_price"
    ASKING_DELIVERY = "asking_delivery"
    ASKING_FEATURES = "asking_features"
    REQUESTING_QUOTE = "requesting_quote"
    COMPLAINING = "complaining"
    THANKING = "thanking"
    SAYING_GOODBYE = "saying_goodbye"
    REQUESTING_HUMAN = "requesting_human"
    GENERAL_QUESTION = "general_question"
    UNKNOWN = "unknown"


@dataclass
class AnalysisResult:
    """Result of sentiment and intent analysis"""
    sentiment: Sentiment
    sentiment_confidence: float
    intent: Intent
    intent_confidence: float
    emotions: List[str]
    urgency: float  # 0.0 = not urgent, 1.0 = very urgent
    needs_human: bool
    language: str


class SentimentAnalyzer:
    """
    Analyze user sentiment from text.
    Uses rule-based approach (in production, use ML model).
    """
    
    # Sentiment keywords
    POSITIVE_KEYWORDS = [
        "merci", "super", "génial", "excellent", "parfait", "bravo",
        "content", "satisfait", "heureux", "top", "bien", "bonne",
        "thank", "great", "perfect", "excellent", "amazing", "love"
    ]
    
    NEGATIVE_KEYWORDS = [
        "problème", "erreur", "bug", "lent", "cher", "déçu", "nul",
        "mauvais", "horrible", "pire", "catastrophe", "horreur",
        "problem", "error", "slow", "expensive", "disappointed", "bad"
    ]
    
    FRUSTRATED_KEYWORDS = [
        "urgent", "inacceptable", "scandaleux", "furieux", "énervé",
        "marre", "ras le bol", "trop c'est trop", "jamais", "toujours",
        "encore", "!!!", "???", "WTF", "ridicule"
    ]
    
    def analyze(self, text: str) -> Tuple[Sentiment, float]:
        """
        Analyze sentiment of text.
        
        Returns:
            Tuple of (Sentiment, confidence)
        """
        text_lower = text.lower()
        
        positive_count = sum(1 for kw in self.POSITIVE_KEYWORDS if kw in text_lower)
        negative_count = sum(1 for kw in self.NEGATIVE_KEYWORDS if kw in text_lower)
        frustrated_count = sum(1 for kw in self.FRUSTRATED_KEYWORDS if kw in text_lower)
        
        # Check for frustration indicators
        exclamation_count = text.count("!")
        question_count = text.count("?")
        caps_ratio = sum(1 for c in text if c.isupper()) / max(len(text), 1)
        
        if caps_ratio > 0.5 and len(text) > 10:
            frustrated_count += 2
        if exclamation_count >= 3:
            frustrated_count += 1
        
        # Determine sentiment
        if frustrated_count >= 2:
            return (Sentiment.FRUSTRATED, 0.8)
        elif negative_count > positive_count:
            confidence = min(0.5 + negative_count * 0.1, 0.95)
            return (Sentiment.NEGATIVE, confidence)
        elif positive_count > negative_count:
            confidence = min(0.5 + positive_count * 0.1, 0.95)
            return (Sentiment.POSITIVE, confidence)
        else:
            return (Sentiment.NEUTRAL, 0.6)


class IntentClassifier:
    """
    Classify user intent.
    Uses rule-based pattern matching.
    """
    
    INTENT_PATTERNS = {
        Intent.GREETING: [
            r"^bonjour", r"^salut", r"^hello", r"^hi\b", r"^coucou",
            r"^bonsoir", r"^hey\b"
        ],
        Intent.ASKING_PRICE: [
            r"prix", r"tarif", r"combien.*coût", r"coût", r"coûte",
            r"budget", r"cher", r"gratuit", r"€", r"euros?"
        ],
        Intent.ASKING_DELIVERY: [
            r"délai", r"temps", r"combien de temps", r"quand",
            r"livr", r"prêt", r"terminer", r"durée"
        ],
        Intent.ASKING_FEATURES: [
            r"fonctionnalit", r"inclus", r"compren", r"propose",
            r"offr", r"servic", r"feature"
        ],
        Intent.REQUESTING_QUOTE: [
            r"devis", r"estimation", r"chiffr", r"propos",
            r"quote", r"estimate"
        ],
        Intent.COMPLAINING: [
            r"plainte", r"problème", r"marche pas", r"bug",
            r"erreur", r"inacceptable", r"remboursement"
        ],
        Intent.THANKING: [
            r"merci", r"thank", r"super", r"parfait", r"génial"
        ],
        Intent.SAYING_GOODBYE: [
            r"au revoir", r"bye", r"à bientôt", r"bonne journée",
            r"bonne soirée", r"ciao"
        ],
        Intent.REQUESTING_HUMAN: [
            r"humain", r"personne", r"quelqu'un", r"agent",
            r"conseiller", r"parler à", r"téléphone"
        ]
    }
    
    def classify(self, text: str) -> Tuple[Intent, float]:
        """
        Classify the intent of user message.
        
        Returns:
            Tuple of (Intent, confidence)
        """
        text_lower = text.lower()
        
        intent_scores = {}
        
        for intent, patterns in self.INTENT_PATTERNS.items():
            score = 0
            for pattern in patterns:
                if re.search(pattern, text_lower):
                    score += 1
            if score > 0:
                intent_scores[intent] = score
        
        if not intent_scores:
            return (Intent.GENERAL_QUESTION, 0.5)
        
        # Get highest scoring intent
        best_intent = max(intent_scores.keys(), key=lambda k: intent_scores[k])
        confidence = min(0.5 + intent_scores[best_intent] * 0.15, 0.95)
        
        return (best_intent, confidence)


class TextAnalyzer:
    """
    Combined text analyzer for sentiment, intent, and other features.
    """
    
    def __init__(self):
        self.sentiment_analyzer = SentimentAnalyzer()
        self.intent_classifier = IntentClassifier()
    
    def analyze(self, text: str) -> AnalysisResult:
        """
        Perform full analysis of user text.
        
        Args:
            text: User message
            
        Returns:
            Complete analysis result
        """
        # Sentiment
        sentiment, sentiment_conf = self.sentiment_analyzer.analyze(text)
        
        # Intent
        intent, intent_conf = self.intent_classifier.classify(text)
        
        # Emotions
        emotions = self._detect_emotions(text)
        
        # Urgency
        urgency = self._calculate_urgency(text, sentiment, intent)
        
        # Needs human?
        needs_human = (
            intent == Intent.REQUESTING_HUMAN or
            sentiment == Sentiment.FRUSTRATED or
            urgency > 0.7
        )
        
        # Language detection (simple)
        language = self._detect_language(text)
        
        result = AnalysisResult(
            sentiment=sentiment,
            sentiment_confidence=sentiment_conf,
            intent=intent,
            intent_confidence=intent_conf,
            emotions=emotions,
            urgency=urgency,
            needs_human=needs_human,
            language=language
        )
        
        logger.debug(
            f"Text analysis: sentiment={sentiment.value}, "
            f"intent={intent.value}, urgency={urgency:.2f}"
        )
        
        return result
    
    def _detect_emotions(self, text: str) -> List[str]:
        """Detect emotions in text"""
        emotions = []
        text_lower = text.lower()
        
        if any(w in text_lower for w in ["😊", "🙂", "content", "heureux"]):
            emotions.append("happy")
        if any(w in text_lower for w in ["😢", "😞", "triste", "déçu"]):
            emotions.append("sad")
        if any(w in text_lower for w in ["😠", "😡", "énervé", "furieux"]):
            emotions.append("angry")
        if any(w in text_lower for w in ["🤔", "?", "comment", "pourquoi"]):
            emotions.append("curious")
        if any(w in text_lower for w in ["😰", "inquiet", "urgent", "rapidement"]):
            emotions.append("anxious")
        
        return emotions if emotions else ["neutral"]
    
    def _calculate_urgency(
        self, 
        text: str, 
        sentiment: Sentiment, 
        intent: Intent
    ) -> float:
        """Calculate urgency score (0.0 to 1.0)"""
        urgency = 0.0
        text_lower = text.lower()
        
        urgent_words = ["urgent", "rapidement", "vite", "aujourd'hui", "maintenant", "asap"]
        urgency += sum(0.2 for w in urgent_words if w in text_lower)
        
        if sentiment == Sentiment.FRUSTRATED:
            urgency += 0.3
        if sentiment == Sentiment.NEGATIVE:
            urgency += 0.15
        
        if intent == Intent.COMPLAINING:
            urgency += 0.25
        if intent == Intent.REQUESTING_HUMAN:
            urgency += 0.2
        
        return min(urgency, 1.0)
    
    def _detect_language(self, text: str) -> str:
        """Simple language detection"""
        text_lower = text.lower()
        
        french_words = ["je", "le", "la", "de", "et", "est", "un", "une", "pour", "vous"]
        english_words = ["the", "a", "is", "are", "i", "you", "we", "for", "to", "and"]
        
        french_count = sum(1 for w in french_words if f" {w} " in f" {text_lower} ")
        english_count = sum(1 for w in english_words if f" {w} " in f" {text_lower} ")
        
        if french_count > english_count:
            return "fr"
        elif english_count > french_count:
            return "en"
        else:
            return "fr"  # Default to French


# Singleton
_analyzer: Optional[TextAnalyzer] = None


def get_text_analyzer() -> TextAnalyzer:
    """Get the text analyzer singleton"""
    global _analyzer
    if _analyzer is None:
        _analyzer = TextAnalyzer()
    return _analyzer
