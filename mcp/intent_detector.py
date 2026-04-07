"""
Intent Detection: identifies user intent using rule-based, model-based, and semantic approaches.
"""

import re
import logging
from typing import List, Tuple, Dict, Any, Optional
from .models import IntentMatch

logger = logging.getLogger(__name__)


class IntentDetector:
    """
    Multi-stage intent detection pipeline:
    1. Rule-based matcher (keywords, patterns)
    2. Model-based classifier (LLM/NLI or fine-tuned transformer)
    3. Semantic fallback (embedding similarity)
    
    Returns ranked list of detected intents with confidence scores.
    """

    def __init__(self):
        # Rule-based patterns: intent_name -> (keywords, confidence_boost)
        self.rules: Dict[str, Tuple[List[str], float]] = {
            "it.support.password": (
                ["password", "reset", "login", "credentials", "authenticate", "access"],
                0.90
            ),
            "it.support.vpn": (
                ["vpn", "connection", "network", "connectivity", "latency", "outage"],
                0.85
            ),
            "it.support.general": (
                ["support", "help", "issue", "problem", "troubleshoot", "error"],
                0.70
            ),
            "document.review": (
                ["review", "contract", "document", "agreement", "clause", "compliance", "pdf", "nda"],
                0.88
            ),
            "document.analyze": (
                ["analyze", "extract", "summarize", "audit", "inspect", "policy"],
                0.80
            ),
        }

        # Model-based thresholds (would be replaced with real LLM calls)
        self.model_threshold = 0.60

    def detect(self, text: str, intent_hints: Optional[List[str]] = None) -> List[IntentMatch]:
        """
        Multi-stage intent detection.
        
        Args:
            text: user input text
            intent_hints: optional hints provided by user/UI
            
        Returns:
            Ranked list of IntentMatch objects (highest confidence first)
        """
        if not text.strip():
            return []

        matches: Dict[str, IntentMatch] = {}

        # Stage 1: Rule-based matching
        rule_matches = self._rule_based_match(text)
        for intent, conf, rationale in rule_matches:
            if intent not in matches:
                matches[intent] = IntentMatch(
                    name=intent,
                    confidence=conf,
                    method="rule",
                    rationale=rationale,
                )
            else:
                matches[intent].confidence = max(matches[intent].confidence, conf)

        # Stage 2: Intent hints (user or UI provided)
        if intent_hints:
            for hint in intent_hints:
                if hint not in matches:
                    matches[hint] = IntentMatch(
                        name=hint,
                        confidence=0.95,
                        method="hint",
                        rationale="User provided intent hint",
                    )
                else:
                    matches[hint].confidence = min(0.95, matches[hint].confidence + 0.10)

        # Stage 3: Model-based (placeholder for LLM call)
        model_matches = self._model_based_match(text)
        for intent, conf, rationale in model_matches:
            if conf >= self.model_threshold:
                if intent not in matches:
                    matches[intent] = IntentMatch(
                        name=intent,
                        confidence=conf,
                        method="model",
                        rationale=rationale,
                    )
                else:
                    # Combine model and existing confidence
                    matches[intent].confidence = max(matches[intent].confidence, conf * 0.8)

        # Sort by confidence descending
        result = sorted(matches.values(), key=lambda x: x.confidence, reverse=True)
        logger.info(f"Detected intents for '{text[:50]}...': {[f'{m.name}({m.confidence:.2f})' for m in result]}")
        return result

    def _rule_based_match(self, text: str) -> List[Tuple[str, float, str]]:
        """Rule-based keyword matching."""
        text_lower = text.lower()
        matches = []

        for intent, (keywords, base_conf) in self.rules.items():
            keyword_matches = sum(1 for kw in keywords if kw in text_lower)
            if keyword_matches > 0:
                # Boost confidence if multiple keywords match
                conf = base_conf + (0.05 * (keyword_matches - 1))
                conf = min(conf, 0.99)
                rationale = f"Matched {keyword_matches} keyword(s): {', '.join([kw for kw in keywords if kw in text_lower])}"
                matches.append((intent, conf, rationale))

        return matches

    def _model_based_match(self, text: str) -> List[Tuple[str, float, str]]:
        """
        Model-based intent classification using LLM.
        
        Placeholder: in production, replace with actual HF model or OpenAI call.
        """
        # For demo: simple heuristic
        intent_keywords = {
            "it.support.password": ["password", "credentials"],
            "it.support.vpn": ["vpn", "network"],
            "document.review": ["contract", "agreement", "review"],
        }

        matches = []
        text_lower = text.lower()

        for intent, keywords in intent_keywords.items():
            if any(kw in text_lower for kw in keywords):
                conf = 0.70 + (0.1 * sum(1 for kw in keywords if kw in text_lower))
                matches.append((intent, min(conf, 0.95), "Model-based classification"))

        return matches

    def get_top_intent(self, text: str, intent_hints: Optional[List[str]] = None) -> Optional[IntentMatch]:
        """Get the highest-confidence intent."""
        matches = self.detect(text, intent_hints)
        return matches[0] if matches else None

    def get_top_n_intents(self, text: str, n: int = 3, intent_hints: Optional[List[str]] = None) -> List[IntentMatch]:
        """Get top N intents."""
        matches = self.detect(text, intent_hints)
        return matches[:n]

    def register_intent_rule(self, intent_name: str, keywords: List[str], confidence: float):
        """Register a new intent rule dynamically."""
        self.rules[intent_name] = (keywords, confidence)
        logger.info(f"Registered rule for intent: {intent_name}")
