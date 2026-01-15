"""
Safety Guardrails
Input/output validation and content safety
"""

import re
from typing import List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import structlog

logger = structlog.get_logger()


class SafetyLevel(Enum):
    SAFE = "safe"
    WARNING = "warning"
    BLOCKED = "blocked"


@dataclass
class SafetyResult:
    """Result of safety check"""
    level: SafetyLevel
    passed: bool
    issues: List[str]
    sanitized_text: Optional[str] = None


class InputGuardrails:
    """
    Validates and sanitizes user input before processing.
    """
    
    # Prompt injection patterns
    INJECTION_PATTERNS = [
        r"ignore (previous|all|your) instructions",
        r"ignore (the|your) (system|initial) prompt",
        r"you are now",
        r"act as",
        r"pretend (to be|you are)",
        r"forget (everything|your training)",
        r"disregard (all|previous)",
        r"new instructions",
        r"override",
        r"jailbreak"
    ]
    
    # PII patterns (to detect and mask)
    PII_PATTERNS = {
        "email": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
        "phone_fr": r"\b(?:0|\+33|33)[1-9](?:[\s.-]?\d{2}){4}\b",
        "card_number": r"\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b",
        "ssn": r"\b\d{3}[-.]?\d{2}[-.]?\d{4}\b",
        "iban": r"\bFR\d{2}[\s]?\d{4}[\s]?\d{4}[\s]?\d{4}[\s]?\d{4}[\s]?\d{3}\b"
    }
    
    # Inappropriate content
    BLOCKED_PATTERNS = [
        r"\b(escort|pornog|xxx)\b",
        r"\b(cocaïne|héroïne|crack|meth)\b",
        r"\b(arme|bombe|explosif|tuer)\b"
    ]
    
    def check(self, text: str) -> SafetyResult:
        """
        Check input text for safety issues.
        
        Args:
            text: User input
            
        Returns:
            SafetyResult with issues found
        """
        issues = []
        level = SafetyLevel.SAFE
        text_lower = text.lower()
        
        # Check for prompt injection
        for pattern in self.INJECTION_PATTERNS:
            if re.search(pattern, text_lower, re.IGNORECASE):
                issues.append(f"Possible prompt injection detected")
                level = SafetyLevel.WARNING
                break
        
        # Check for blocked content
        for pattern in self.BLOCKED_PATTERNS:
            if re.search(pattern, text_lower, re.IGNORECASE):
                issues.append("Inappropriate content detected")
                level = SafetyLevel.BLOCKED
                break
        
        # Check for PII
        for pii_type, pattern in self.PII_PATTERNS.items():
            if re.search(pattern, text):
                issues.append(f"PII detected: {pii_type}")
                if level != SafetyLevel.BLOCKED:
                    level = SafetyLevel.WARNING
        
        # Sanitize if needed
        sanitized = self._sanitize(text) if level == SafetyLevel.WARNING else text
        
        passed = level != SafetyLevel.BLOCKED
        
        if issues:
            logger.warning(f"Input safety check: {level.value}, issues: {issues}")
        
        return SafetyResult(
            level=level,
            passed=passed,
            issues=issues,
            sanitized_text=sanitized
        )
    
    def _sanitize(self, text: str) -> str:
        """Sanitize text by masking PII"""
        result = text
        
        for pii_type, pattern in self.PII_PATTERNS.items():
            if pii_type == "email":
                result = re.sub(pattern, "[EMAIL_HIDDEN]", result)
            elif pii_type in ["phone_fr"]:
                result = re.sub(pattern, "[PHONE_HIDDEN]", result)
            elif pii_type == "card_number":
                result = re.sub(pattern, "[CARD_HIDDEN]", result)
            elif pii_type == "iban":
                result = re.sub(pattern, "[IBAN_HIDDEN]", result)
        
        return result


class OutputGuardrails:
    """
    Validates agent output before sending to user.
    """
    
    # Things the agent should never say
    BLOCKED_OUTPUTS = [
        r"je suis un (modèle|programme|ia|robot)",
        r"en tant qu'(ia|intelligence artificielle|chatbot)",
        r"je n'ai pas (d'émotions|de sentiments)",
        r"competitor",  # Should not mention competitors
    ]
    
    # Price validation (ensure prices match official pricing)
    OFFICIAL_PRICES = {
        "vitrine": 299,
        "ecommerce": 599,
        "surmesure": 1299,
        "maintenance": 49,
        "seo": 150
    }
    
    def check(self, text: str) -> SafetyResult:
        """
        Check output text for issues before sending.
        
        Args:
            text: Agent response
            
        Returns:
            SafetyResult
        """
        issues = []
        level = SafetyLevel.SAFE
        text_lower = text.lower()
        
        # Check for blocked outputs
        for pattern in self.BLOCKED_OUTPUTS:
            if re.search(pattern, text_lower, re.IGNORECASE):
                issues.append(f"Inappropriate self-reference detected")
                level = SafetyLevel.WARNING
                break
        
        # Check for hallucinated prices
        price_issues = self._validate_prices(text)
        if price_issues:
            issues.extend(price_issues)
            level = SafetyLevel.WARNING
        
        # Check response length (too short or too long)
        if len(text) < 10:
            issues.append("Response too short")
            level = SafetyLevel.WARNING
        elif len(text) > 2000:
            issues.append("Response too long")
            level = SafetyLevel.WARNING
        
        passed = level != SafetyLevel.BLOCKED
        
        if issues:
            logger.warning(f"Output safety check: {level.value}, issues: {issues}")
        
        return SafetyResult(
            level=level,
            passed=passed,
            issues=issues,
            sanitized_text=text
        )
    
    def _validate_prices(self, text: str) -> List[str]:
        """Check for potentially hallucinated prices"""
        issues = []
        
        # Find all prices mentioned in the text
        price_pattern = r"(\d+)\s*€"
        prices_found = re.findall(price_pattern, text)
        
        valid_prices = set(self.OFFICIAL_PRICES.values())
        valid_prices.update([199, 399, 499, 799, 999, 1499])  # Add common valid prices
        
        for price_str in prices_found:
            price = int(price_str)
            # Only flag if price is suspiciously specific and not in valid list
            if price not in valid_prices and price > 50:
                # Allow reasonable variations (maintenance, add-ons, etc.)
                if not any(abs(price - vp) <= 50 for vp in valid_prices):
                    issues.append(f"Potentially incorrect price: {price}€")
        
        return issues


class GuardrailsManager:
    """
    Central manager for all guardrails.
    """
    
    def __init__(self):
        self.input_guardrails = InputGuardrails()
        self.output_guardrails = OutputGuardrails()
    
    def check_input(self, text: str) -> SafetyResult:
        """Check user input"""
        return self.input_guardrails.check(text)
    
    def check_output(self, text: str) -> SafetyResult:
        """Check agent output"""
        return self.output_guardrails.check(text)
    
    def process_safely(
        self, 
        input_text: str, 
        process_fn, 
        *args, 
        **kwargs
    ) -> Tuple[bool, str]:
        """
        Safely process input through a function with guardrails.
        
        Args:
            input_text: User input
            process_fn: Function to process (async or sync)
            *args, **kwargs: Arguments for process_fn
            
        Returns:
            Tuple of (success, result_or_error)
        """
        # Check input
        input_check = self.check_input(input_text)
        if not input_check.passed:
            return (False, "Je ne peux pas traiter cette demande.")
        
        # Use sanitized input if available
        safe_input = input_check.sanitized_text or input_text
        
        return (True, safe_input)


# Singleton
_manager: Optional[GuardrailsManager] = None


def get_guardrails() -> GuardrailsManager:
    """Get the guardrails manager singleton"""
    global _manager
    if _manager is None:
        _manager = GuardrailsManager()
    return _manager
