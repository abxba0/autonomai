"""
FastAPI web interface for the Self-Optimizing Instruction Library
"""

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import uvicorn
import os
from dotenv import load_dotenv

# Add parent directory to path
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src import SelfOptimizingSystem, SystemConfig

# Load environment variables
load_dotenv()

# Create FastAPI app
app = FastAPI(
    title="Self-Optimizing Instruction Library API",
    description="API for the self-optimizing AI instruction system",
    version="1.0.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict this
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Pydantic models for API requests/responses
class ExecuteRequest(BaseModel):
    query: str
    conversation_context: Optional[List[Dict[str, str]]] = None


class ExecuteResponse(BaseModel):
    output: str
    validation_passed: bool
    validation_results: List[Dict[str, Any]]
    optimization_attempted: bool
    optimization_result: Optional[Dict[str, Any]] = None


class FeedbackRequest(BaseModel):
    feedback: str
    severity: str = "moderate"
    attach_last_output: bool = True


class FeedbackContextRequest(BaseModel):
    conversation_history: List[Dict[str, str]]
    focus_recent: int = 10
    min_confidence: float = 0.6
    auto_apply: bool = False


class FeedbackContextResponse(BaseModel):
    success: bool
    message: Optional[str] = None
    rules_count: int = 0
    dont_rules_count: int = 0
    patterns_count: int = 0
    formatted_display: Optional[str] = None
    instruction_updates: Optional[str] = None
    auto_apply_result: Optional[Dict[str, Any]] = None


class VersionInfo(BaseModel):
    version_id: str
    timestamp: str
    trigger_type: str
    diff_summary: str
    rules_added: int
    rules_modified: int
    rules_deprecated: int


class SystemStatus(BaseModel):
    total_failures: int
    total_optimizations: int
    current_version: Optional[str]
    last_optimization: Optional[str]
    system_health: str


# Global system instance
_system_instance = None


def get_system():
    """Get or create system instance"""
    global _system_instance
    if _system_instance is None:
        # Configure system
        config = SystemConfig(
            main_model=os.getenv("MAIN_MODEL", "claude-3-5-sonnet-20241022"),
            critic_model=os.getenv("CRITIC_MODEL", "claude-3-haiku-20240307"),
            enable_auto_optimization=True,
        )
        _system_instance = SelfOptimizingSystem(config)
    return _system_instance


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Self-Optimizing Instruction Library API",
        "version": "1.0.0",
        "endpoints": [
            "/execute - Execute query",
            "/feedback - Provide feedback",
            "/feedback-context - Analyze conversation and extract rules",
            "/status - System status",
            "/versions - Version history",
            "/instructions - Current instructions",
            "/health - Health check",
        ],
    }


@app.post("/execute", response_model=ExecuteResponse)
async def execute_query(
    request: ExecuteRequest, system: SelfOptimizingSystem = Depends(get_system)
):
    """Execute a query with the system"""
    try:
        result = system.execute(
            user_query=request.query, conversation_context=request.conversation_context
        )

        return ExecuteResponse(
            output=result["output"],
            validation_passed=result["validation_passed"],
            validation_results=[
                {
                    "validator_name": r.validator_name,
                    "passed": r.passed,
                    "error_message": r.error_message,
                }
                for r in result["validation_results"]
            ],
            optimization_attempted=result.get("optimization_attempted", False),
            optimization_result=result.get("optimization_result"),
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Execution error: {str(e)}")


@app.post("/feedback")
async def provide_feedback(
    request: FeedbackRequest, system: SelfOptimizingSystem = Depends(get_system)
):
    """Provide manual feedback for system improvement"""
    try:
        result = system.request_instruction_update(
            user_feedback=request.feedback,
            severity=request.severity,
            attach_last_output=request.attach_last_output,
        )

        return {
            "success": result.get("success", False),
            "message": result.get("message", "Feedback processed"),
            "optimization_result": result,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Feedback error: {str(e)}")


@app.post("/feedback-context", response_model=FeedbackContextResponse)
async def analyze_feedback_context(
    request: FeedbackContextRequest, system: SelfOptimizingSystem = Depends(get_system)
):
    """
    Analyze conversation context to extract rules and patterns

    This endpoint processes the conversation history to automatically detect
    user preferences, desired behaviors, and patterns, then proposes new
    rules (both positive "DO" rules and negative "DON'T" rules).
    """
    try:
        result = system.analyze_feedback_context(
            conversation_history=request.conversation_history,
            focus_recent=request.focus_recent,
            min_confidence=request.min_confidence,
            auto_apply=request.auto_apply,
        )

        if not result.get("success"):
            raise HTTPException(
                status_code=400, detail=result.get("message", "Context analysis failed")
            )

        return FeedbackContextResponse(
            success=result["success"],
            message=result.get("analysis", {}).get("message"),
            rules_count=result.get("rules_count", 0),
            dont_rules_count=result.get("dont_rules_count", 0),
            patterns_count=result.get("patterns_count", 0),
            formatted_display=result.get("formatted_display"),
            instruction_updates=result.get("instruction_updates"),
            auto_apply_result=result.get("auto_apply_result"),
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Context analysis error: {str(e)}")


@app.get("/status", response_model=SystemStatus)
async def get_status(system: SelfOptimizingSystem = Depends(get_system)):
    """Get system status"""
    try:
        # Get version history
        history = system.get_version_history()

        # Calculate metrics
        total_optimizations = len(
            [v for v in history if v["trigger_type"] != "initial"]
        )
        last_optimization = history[-1]["timestamp"] if history else None

        return SystemStatus(
            total_failures=len(system.instruction_manager.failure_log.entries),
            total_optimizations=total_optimizations,
            current_version=system.instruction_manager.current_version,
            last_optimization=last_optimization,
            system_health="healthy" if total_optimizations > 0 else "initializing",
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Status error: {str(e)}")


@app.get("/versions", response_model=List[VersionInfo])
async def get_versions(system: SelfOptimizingSystem = Depends(get_system)):
    """Get version history"""
    try:
        history = system.get_version_history()
        return [
            VersionInfo(
                version_id=v["version_id"],
                timestamp=v["timestamp"],
                trigger_type=v["trigger_type"],
                diff_summary=v["diff_summary"],
                rules_added=v["rules_added"],
                rules_modified=v["rules_modified"],
                rules_deprecated=v["rules_deprecated"],
            )
            for v in history
        ]

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Versions error: {str(e)}")


@app.get("/instructions")
async def get_instructions(system: SelfOptimizingSystem = Depends(get_system)):
    """Get current instructions"""
    try:
        instructions = system.get_current_instructions()
        return {
            "instructions": instructions,
            "length": len(instructions),
            "current_version": system.instruction_manager.current_version,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Instructions error: {str(e)}")


@app.post("/rollback/{steps}")
async def rollback_version(
    steps: int, system: SelfOptimizingSystem = Depends(get_system)
):
    """Rollback to previous version"""
    try:
        success = system.rollback(steps)
        return {
            "success": success,
            "message": (
                f"Rolled back {steps} versions" if success else "Rollback failed"
            ),
            "current_version": (
                system.instruction_manager.current_version if success else None
            ),
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Rollback error: {str(e)}")


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "self-optimizing-system"}


if __name__ == "__main__":
    # Run the server
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8000))
    debug = os.getenv("DEBUG", "false").lower() == "true"

    print(f"Starting server on {host}:{port}")
    uvicorn.run(
        "api:app",
        host=host,
        port=port,
        reload=debug,
        log_level="info" if debug else "warning",
    )
