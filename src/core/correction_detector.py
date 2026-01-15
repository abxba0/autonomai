"""
Correction Detector Module

Detects implicit negative feedback when users correct or express dissatisfaction
with AI responses without using explicit feedback commands.
"""

from typing import Dict, Any, Optional, List, Tuple
import re


class CorrectionDetector:
    """Detects implicit corrections and negative feedback in user messages"""
    
    def __init__(self, confidence_threshold: float = 0.7):
        """
        Initialize the correction detector
        
        Args:
            confidence_threshold: Minimum confidence level (0-1) to trigger detection
        """
        self.confidence_threshold = confidence_threshold
        
        # Patterns for detecting corrections
        self.correction_patterns = [
            # Direct negations
            (r'\b(?:no|nope|nah)\s*,?\s*(?:that\'?s?\s*)?(?:not|wrong|incorrect|false)',
             0.9, "direct_negation"),
            (r'\b(?:that\'?s?\s*)?(?:not|n\'t)\s+(?:right|correct|true|accurate)',
             0.9, "direct_negation"),
            (r'\bactually\s*,?\s*(?:it\'?s?\s*)?(?:not|wrong|incorrect)',
             0.85, "correction_with_actually"),
            
            # Explicit corrections
            (r'\b(?:you\'?re|you are)\s+(?:wrong|incorrect|mistaken)',
             0.95, "explicit_error_statement"),
            (r'\bthat\'?s?\s+(?:wrong|incorrect|false|not right)',
             0.9, "explicit_error_statement"),
            (r'\b(?:this|that)\s+(?:is|was)\s+(?:wrong|incorrect|false)',
             0.9, "explicit_error_statement"),
            
            # Corrections with alternatives
            (r'\b(?:no|not really)\s*,?\s*(?:it should be|it\'?s?\s*(?:actually|really))',
             0.85, "correction_with_alternative"),
            (r'\b(?:wrong|incorrect)\s*[,.;]\s*(?:it should be|the correct answer is)',
             0.9, "correction_with_alternative"),
            
            # Dissatisfaction expressions
            (r'\b(?:that doesn\'?t\s*(?:make sense|work|help|answer))',
             0.75, "dissatisfaction"),
            (r'\b(?:that\'?s?\s*)?(?:not what|nothing like)\s+(?:I|we)\s+(?:asked|wanted|needed)',
             0.8, "dissatisfaction"),
            (r'\b(?:you|this)\s+(?:didn\'?t|haven\'?t)\s+(?:answer|address|help)',
             0.8, "dissatisfaction"),
            
            # Re-asking with correction
            (r'\b(?:let me try again|let me rephrase)\s*[,:]',
             0.65, "rephrase_attempt"),
            (r'\b(?:to clarify|what I meant was)',
             0.7, "clarification"),
            
            # Request for correction
            (r'\b(?:can|could) you (?:fix|correct|revise)',
             0.75, "correction_request"),
            (r'\b(?:please|pls) (?:fix|correct|change|update)',
             0.75, "correction_request"),
            
            # Disappointment markers
            (r'\b(?:unfortunately|sadly)\s*,?\s*(?:that\'?s?\s*)?(?:not|wrong)',
             0.7, "disappointment"),
            (r'\b(?:I\'?m?\s*)?(?:afraid|sorry)\s+(?:that\'?s?\s*)?(?:not|wrong|incorrect)',
             0.7, "disappointment"),
        ]
        
        # Context patterns that increase correction likelihood
        self.context_amplifiers = [
            (r'\bbut\b', 0.1),
            (r'\bhowever\b', 0.1),
            (r'\b(?:as I said|I mentioned)\b', 0.1),
            (r'\bagain\b', 0.05),
        ]
        
        # Patterns that might be false positives (reduce confidence)
        self.false_positive_patterns = [
            (r'\b(?:just kidding|jk)\b', -0.3),
            (r'\b(?:hypothetically|imagine|suppose)\b', -0.2),
            (r'\bwhat if\b', -0.2),
        ]
    
    def detect_correction(
        self,
        user_message: str,
        previous_response: Optional[str] = None,
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> Tuple[bool, float, Optional[str]]:
        """
        Detect if user message contains implicit correction or negative feedback
        
        Args:
            user_message: The user's message to analyze
            previous_response: The AI's previous response (optional)
            conversation_history: Recent conversation context (optional)
            
        Returns:
            Tuple of (is_correction, confidence, correction_type)
        """
        user_message_lower = user_message.lower()
        
        # Track highest confidence match
        max_confidence = 0.0
        detected_type = None
        
        # Check correction patterns
        for pattern, base_confidence, correction_type in self.correction_patterns:
            if re.search(pattern, user_message_lower):
                confidence = base_confidence
                
                # Apply context amplifiers
                for amplifier_pattern, boost in self.context_amplifiers:
                    if re.search(amplifier_pattern, user_message_lower):
                        confidence = min(1.0, confidence + boost)
                
                # Check for false positive patterns
                for fp_pattern, penalty in self.false_positive_patterns:
                    if re.search(fp_pattern, user_message_lower):
                        confidence = max(0.0, confidence + penalty)
                
                if confidence > max_confidence:
                    max_confidence = confidence
                    detected_type = correction_type
        
        # Additional heuristics based on conversation flow
        if conversation_history and len(conversation_history) >= 2:
            # Check if user is repeating similar query (possible dissatisfaction)
            recent_user_msgs = [
                msg["content"] for msg in conversation_history[-4:]
                if msg.get("role") == "user"
            ]
            if len(recent_user_msgs) >= 2:
                # Simple similarity check (more sophisticated NLP could be used)
                if self._messages_similar(recent_user_msgs[-1], user_message):
                    max_confidence = max(max_confidence, 0.6)
                    if not detected_type:
                        detected_type = "repeated_query"
        
        is_correction = max_confidence >= self.confidence_threshold
        
        return is_correction, max_confidence, detected_type if is_correction else None
    
    def _messages_similar(self, msg1: str, msg2: str, threshold: float = 0.5) -> bool:
        """
        Simple similarity check between two messages
        
        More sophisticated approaches could use:
        - Levenshtein distance
        - Word embeddings
        - Semantic similarity
        """
        msg1_words = set(msg1.lower().split())
        msg2_words = set(msg2.lower().split())
        
        if not msg1_words or not msg2_words:
            return False
        
        intersection = msg1_words.intersection(msg2_words)
        union = msg1_words.union(msg2_words)
        
        similarity = len(intersection) / len(union) if union else 0
        return similarity >= threshold
    
    def create_correction_description(
        self,
        user_message: str,
        correction_type: str,
        confidence: float,
        previous_response: Optional[str] = None
    ) -> str:
        """
        Create a detailed description of the detected correction
        
        Args:
            user_message: The user's correcting message
            correction_type: Type of correction detected
            confidence: Confidence level of detection
            previous_response: The AI's previous response that was corrected
            
        Returns:
            Formatted description for the failure log
        """
        description = f"Implicit correction detected (type: {correction_type}, confidence: {confidence:.2f})\n"
        description += f"User indicated dissatisfaction or correction: {user_message[:200]}"
        
        if previous_response:
            description += f"\nPrevious response: {previous_response[:200]}"
        
        return description
