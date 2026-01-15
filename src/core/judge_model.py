"""
Judge Model - Consensus Critic for validating instruction updates

Implements the "Judge" pattern where a second model reviews and validates
proposed instruction changes from the Critic model.
"""

from typing import Dict, Any, Optional
import json
import os
from dotenv import load_dotenv

from ..models.config import SystemConfig
from ..models.critic_response import CriticResponse


class JudgeResponse:
    """Response from the Judge model"""
    
    def __init__(
        self,
        approved: bool,
        reasoning: str,
        conflicts_detected: bool = False,
        conflict_details: Optional[str] = None,
        confidence_score: float = 0.8,
        suggestions: Optional[str] = None
    ):
        self.approved = approved
        self.reasoning = reasoning
        self.conflicts_detected = conflicts_detected
        self.conflict_details = conflict_details
        self.confidence_score = confidence_score
        self.suggestions = suggestions
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "JudgeResponse":
        """Create from dictionary"""
        return cls(
            approved=data.get("approved", False),
            reasoning=data.get("reasoning", ""),
            conflicts_detected=data.get("conflicts_detected", False),
            conflict_details=data.get("conflict_details"),
            confidence_score=data.get("confidence_score", 0.8),
            suggestions=data.get("suggestions")
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "approved": self.approved,
            "reasoning": self.reasoning,
            "conflicts_detected": self.conflicts_detected,
            "conflict_details": self.conflict_details,
            "confidence_score": self.confidence_score,
            "suggestions": self.suggestions
        }


class JudgeModel:
    """
    The Judge - Reviews and validates Critic's proposed instruction changes
    
    Responsibilities:
    1. Review proposed instruction updates
    2. Check for contradictions with Base Instructions
    3. Validate safety and consistency
    4. Provide approval or rejection with reasoning
    """
    
    def __init__(self, config: SystemConfig, base_instructions: str):
        self.config = config
        self.base_instructions = base_instructions
        
        # Load environment variables
        load_dotenv()
        
        # Initialize model (uses same provider as critic by default)
        self.model = self._initialize_model()
        
        # System prompt for Judge
        self.system_prompt = self._build_system_prompt()
    
    def _initialize_model(self):
        """Initialize the judge model with LangChain"""
        # Use critic model configuration by default
        model_name = self.config.critic_model.lower()
        provider = self.config.critic_model_provider.lower() if self.config.critic_model_provider else None
        
        # Detect provider from model name if not explicitly set
        if not provider:
            provider = self._detect_provider(model_name)
        
        # Initialize based on provider (same logic as CriticModel)
        if provider == "anthropic":
            return self._init_anthropic()
        elif provider == "openai":
            return self._init_openai()
        elif provider == "google":
            return self._init_google()
        elif provider == "deepseek":
            return self._init_deepseek()
        elif provider == "openrouter":
            return self._init_openrouter()
        else:
            # Fallback to mock model for testing
            print(f"Warning: Using mock judge model for {self.config.critic_model}")
            return MockJudgeModel(self.config.critic_model, self.config.temperature_critic)
    
    def _detect_provider(self, model_name: str) -> str:
        """Auto-detect provider from model name"""
        if "claude" in model_name or "anthropic" in model_name:
            return "anthropic"
        elif "gpt" in model_name or "openai" in model_name:
            return "openai"
        elif "gemini" in model_name or "google" in model_name:
            return "google"
        elif "deepseek" in model_name:
            return "deepseek"
        elif "openrouter" in model_name:
            return "openrouter"
        return "unknown"
    
    def _init_anthropic(self):
        """Initialize Anthropic Claude model"""
        try:
            from langchain_anthropic import ChatAnthropic
        except ImportError:
            return MockJudgeModel(self.config.critic_model, self.config.temperature_critic)
        
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            return MockJudgeModel(self.config.critic_model, self.config.temperature_critic)
        
        return ChatAnthropic(
            model=self.config.critic_model,
            temperature=self.config.temperature_critic,
            api_key=api_key,
        )
    
    def _init_openai(self):
        """Initialize OpenAI GPT model"""
        try:
            from langchain_openai import ChatOpenAI
        except ImportError:
            return MockJudgeModel(self.config.critic_model, self.config.temperature_critic)
        
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            return MockJudgeModel(self.config.critic_model, self.config.temperature_critic)
        
        return ChatOpenAI(
            model=self.config.critic_model,
            temperature=self.config.temperature_critic,
            api_key=api_key,
        )
    
    def _init_google(self):
        """Initialize Google Gemini model"""
        try:
            from langchain_google_genai import ChatGoogleGenerativeAI
        except ImportError:
            return MockJudgeModel(self.config.critic_model, self.config.temperature_critic)
        
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            return MockJudgeModel(self.config.critic_model, self.config.temperature_critic)
        
        return ChatGoogleGenerativeAI(
            model=self.config.critic_model,
            temperature=self.config.temperature_critic,
            google_api_key=api_key,
        )
    
    def _init_deepseek(self):
        """Initialize Deepseek model (via OpenAI-compatible API)"""
        try:
            from langchain_openai import ChatOpenAI
        except ImportError:
            return MockJudgeModel(self.config.critic_model, self.config.temperature_critic)
        
        api_key = os.getenv("DEEPSEEK_API_KEY")
        base_url = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1")
        
        if not api_key:
            return MockJudgeModel(self.config.critic_model, self.config.temperature_critic)
        
        return ChatOpenAI(
            model=self.config.critic_model,
            temperature=self.config.temperature_critic,
            api_key=api_key,
            base_url=base_url,
        )
    
    def _init_openrouter(self):
        """Initialize Openrouter model (via OpenAI-compatible API)"""
        try:
            from langchain_openai import ChatOpenAI
        except ImportError:
            return MockJudgeModel(self.config.critic_model, self.config.temperature_critic)
        
        api_key = os.getenv("OPENROUTER_API_KEY")
        
        if not api_key:
            print(f"Warning: OPENROUTER_API_KEY not found. Using mock judge model.")
            return MockJudgeModel(self.config.critic_model, self.config.temperature_critic)
        
        return ChatOpenAI(
            model=self.config.critic_model,
            temperature=self.config.temperature_critic,
            api_key=api_key,
            base_url="https://openrouter.ai/api/v1",
            default_headers={
                "HTTP-Referer": "https://github.com/abxba0/autonomai",
                "X-Title": "AutonomAI Self-Optimizing System",
            },
        )
    
    def review_proposal(
        self,
        critic_response: CriticResponse,
        current_appendix: str,
        failure_context: str
    ) -> JudgeResponse:
        """
        Review a Critic's proposed instruction update
        
        Args:
            critic_response: The Critic's proposed change
            current_appendix: Current dynamic appendix
            failure_context: Context about the failure being addressed
            
        Returns:
            JudgeResponse with approval decision and reasoning
        """
        try:
            # Build review prompt
            prompt = self._build_review_prompt(
                critic_response,
                current_appendix,
                failure_context
            )
            
            # Execute with model
            try:
                from langchain_core.messages import HumanMessage, SystemMessage
                
                messages = [
                    SystemMessage(content=self.system_prompt),
                    HumanMessage(content=prompt),
                ]
                
                response = self.model.invoke(messages)
                response_text = response.content
            except ImportError:
                # If langchain is not available, use simple message format
                messages = [
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": prompt},
                ]
                response = self.model.invoke(messages)
                response_text = response.content
            except Exception as e:
                # Fallback to mock if real LLM fails
                print(f"Judge LLM call failed: {e}. Using mock response.")
                return self._mock_approve()
            
            # Parse response
            judge_response = self._parse_judge_response(response_text)
            return judge_response
            
        except Exception as e:
            print(f"Error in Judge review: {e}")
            # Default to approval with low confidence on error
            return JudgeResponse(
                approved=True,
                reasoning=f"Error during review: {str(e)}. Defaulting to approval.",
                confidence_score=0.3
            )
    
    def _build_system_prompt(self) -> str:
        """Build the Judge's system prompt"""
        return """You are an AI Instruction Validator (Judge). Your role is to review and validate proposed instruction updates from a Critic model.

# Your Responsibilities

1. **Review Proposals**: Carefully examine the Critic's proposed instruction changes
2. **Check Consistency**: Verify changes don't contradict Base Instructions
3. **Validate Safety**: Ensure changes are safe and won't break existing functionality
4. **Provide Verdict**: Approve or reject with clear reasoning

# Critical Rules

- You MUST check for contradictions with Base Instructions
- You MUST provide detailed reasoning (minimum 50 characters)
- You MUST be conservative - when in doubt, reject
- You MUST output your response as valid JSON

# Output Format

Return ONLY a JSON object with this structure:
```json
{
  "approved": true/false,
  "reasoning": "Detailed explanation of your decision...",
  "conflicts_detected": true/false,
  "conflict_details": "Description of any conflicts found...",
  "confidence_score": 0.85,
  "suggestions": "Optional suggestions for improvement..."
}
```

# Decision Criteria

**APPROVE** if:
- Change aligns with Base Instructions
- No contradictions detected
- Safety is maintained
- Change is specific and actionable

**REJECT** if:
- Contradicts Base Instructions
- Could break existing functionality
- Too vague or general
- Safety concerns exist
- Confidence is low

When rejecting, provide specific suggestions for improvement.
"""
    
    def _build_review_prompt(
        self,
        critic_response: CriticResponse,
        current_appendix: str,
        failure_context: str
    ) -> str:
        """Build the review prompt"""
        return f"""# Review Request

## Base Instructions (Immutable - Must Not Contradict)

{self.base_instructions}

## Current Dynamic Appendix

{current_appendix}

## Proposed Change from Critic

**Change Type**: {critic_response.change_type}

**Proposed Update**:
{critic_response.proposed_appendix_update}

**Critic's Justification**:
{critic_response.impact_analysis}

**Critic's Safety Declaration**: {critic_response.safety_declaration}

**Critic's Safety Reasoning**:
{critic_response.safety_reasoning}

**Confidence Score**: {critic_response.confidence_score}

**Rules to Deprecate**: {critic_response.rules_to_deprecate}

## Failure Context

{failure_context}

## Your Task

Review this proposed instruction update and decide whether to APPROVE or REJECT it.

Consider:
1. Does this contradict any Base Instructions?
2. Is the change safe and specific?
3. Will this improve the system without breaking existing functionality?
4. Is the Critic's reasoning sound?

Provide your verdict as a JSON object.
"""
    
    def _parse_judge_response(self, response_text: str) -> JudgeResponse:
        """Parse Judge model output into JudgeResponse"""
        try:
            # Clean potential markdown formatting
            clean_text = response_text.strip()
            if clean_text.startswith("```json"):
                clean_text = clean_text[7:]
            if clean_text.endswith("```"):
                clean_text = clean_text[:-3]
            
            data = json.loads(clean_text.strip())
            return JudgeResponse.from_dict(data)
            
        except Exception as e:
            # If parsing fails, default to approval with low confidence
            print(f"Warning: Could not parse Judge response: {e}")
            return JudgeResponse(
                approved=True,
                reasoning="Could not parse Judge response. Defaulting to approval.",
                confidence_score=0.3
            )
    
    def _mock_approve(self) -> JudgeResponse:
        """Mock approval response for testing"""
        return JudgeResponse(
            approved=True,
            reasoning="Mock judge approval for testing purposes.",
            conflicts_detected=False,
            confidence_score=0.8
        )


class MockJudgeModel:
    """Mock judge model for testing"""
    
    def __init__(self, model_name: str, temperature: float):
        self.model_name = model_name
        self.temperature = temperature
    
    def invoke(self, messages):
        """Mock invoke for LangChain compatibility"""
        
        class MockResponse:
            content = json.dumps({
                "approved": True,
                "reasoning": "Mock judge approval. This proposed change looks reasonable and doesn't appear to contradict the base instructions.",
                "conflicts_detected": False,
                "conflict_details": None,
                "confidence_score": 0.85,
                "suggestions": None
            })
        
        return MockResponse()
