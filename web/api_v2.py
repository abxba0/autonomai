"""
API v2 with advanced features: GraphQL, WebSockets, Webhooks, and Versioning
"""

from fastapi import FastAPI, HTTPException, Depends, WebSocket, WebSocketDisconnect, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from contextlib import asynccontextmanager
from strawberry.fastapi import GraphQLRouter
from datetime import datetime
import uvicorn
import os
import asyncio
from dotenv import load_dotenv
import logging

# Add parent directory to path
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src import SelfOptimizingSystem, SystemConfig
from web.graphql_schema import schema
from web.webhook_manager import get_webhook_manager, WebhookManager
from web.websocket_handlers import (
    get_connection_manager,
    handle_websocket_commands,
    notify_workflow_update,
    notify_job_completed,
    notify_optimization_completed,
    notify_regression_detected,
)

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# API versioning configuration
API_VERSION_V1 = "v1"
API_VERSION_V2 = "v2"
CURRENT_VERSION = API_VERSION_V2
DEPRECATED_VERSIONS = [API_VERSION_V1]


# Pydantic models for API v2 (enhanced from v1)
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


class WebhookRegisterRequest(BaseModel):
    url: str
    events: List[str]
    secret: Optional[str] = None


class WebhookInfo(BaseModel):
    id: str
    url: str
    events: List[str]
    created_at: str
    active: bool


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


# Global instances
_system_instance = None
_webhook_manager = None


def get_system():
    """Get or create system instance"""
    global _system_instance
    if _system_instance is None:
        config = SystemConfig(
            main_model=os.getenv("MAIN_MODEL", "claude-3-5-sonnet-20241022"),
            critic_model=os.getenv("CRITIC_MODEL", "claude-3-haiku-20240307"),
            enable_auto_optimization=True,
        )
        _system_instance = SelfOptimizingSystem(config)
    return _system_instance


def get_webhook_manager_instance() -> WebhookManager:
    """Get or create webhook manager instance"""
    global _webhook_manager
    if _webhook_manager is None:
        _webhook_manager = get_webhook_manager()
    return _webhook_manager


async def get_graphql_context():
    """Get context for GraphQL resolvers"""
    return {
        "system": get_system(),
        "webhook_manager": get_webhook_manager_instance(),
    }


# Create versioned FastAPI apps
app_v1 = FastAPI(
    title="Self-Optimizing System API v1 (Deprecated)",
    description="Legacy API endpoints - please migrate to v2",
    version="1.0.0",
    deprecated=True,
)

app_v2 = FastAPI(
    title="Self-Optimizing System API v2",
    description="API with GraphQL, WebSockets, Webhooks, and versioning",
    version="2.0.0",
)


# Lifespan event handler for startup/shutdown
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan events"""
    # Startup
    logger.info("Starting Self-Optimizing System API v2")
    webhook_manager = get_webhook_manager_instance()
    await webhook_manager.start_async()
    logger.info("Webhook manager started")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Self-Optimizing System API v2")
    webhook_manager = get_webhook_manager_instance()
    await webhook_manager.stop()
    logger.info("Webhook manager stopped")


# Main app with versioning
app = FastAPI(
    title="Self-Optimizing Instruction Library API",
    description="Production API with advanced features and versioning",
    version="2.0.0",
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict this
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Deprecation warning middleware
@app.middleware("http")
async def add_deprecation_warning(request: Request, call_next):
    """Add deprecation warnings for old API versions"""
    response = await call_next(request)
    if request.url.path.startswith("/v1/"):
        response.headers["X-API-Deprecated"] = "true"
        response.headers["X-API-Sunset"] = "2026-06-01"  # 6 months notice
        response.headers["X-API-Migration"] = "Please migrate to /v2/ endpoints"
    return response


# ============ API v1 Routes (Deprecated) ============

@app_v1.get("/")
async def v1_root():
    """Root endpoint for v1 (deprecated)"""
    return {
        "message": "API v1 is deprecated. Please migrate to v2.",
        "version": "1.0.0",
        "deprecated": True,
        "sunset_date": "2026-06-01",
        "migration_guide": "/docs/v2-migration",
    }


@app_v1.post("/execute", response_model=ExecuteResponse)
async def v1_execute_query(
    request: ExecuteRequest, system: SelfOptimizingSystem = Depends(get_system)
):
    """Execute a query (v1 - deprecated)"""
    logger.warning("v1 execute endpoint called - deprecated")
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


@app_v1.get("/status", response_model=SystemStatus)
async def v1_get_status(system: SelfOptimizingSystem = Depends(get_system)):
    """Get system status (v1 - deprecated)"""
    logger.warning("v1 status endpoint called - deprecated")
    try:
        history = system.get_version_history()
        total_optimizations = len([v for v in history if v["trigger_type"] != "initial"])
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


# ============ API v2 Routes (Current) ============

@app_v2.get("/")
async def v2_root():
    """Root endpoint for v2"""
    return {
        "message": "Self-Optimizing Instruction Library API v2",
        "version": "2.0.0",
        "features": [
            "GraphQL endpoint at /graphql",
            "WebSocket support at /ws",
            "Webhook management",
            "API versioning with deprecation",
        ],
        "endpoints": {
            "rest": ["/execute", "/feedback", "/status", "/versions", "/health"],
            "graphql": "/graphql",
            "websocket": "/ws",
            "webhooks": ["/webhooks", "/webhooks/{id}"],
        },
    }


@app_v2.post("/execute", response_model=ExecuteResponse)
async def v2_execute_query(
    request: ExecuteRequest, system: SelfOptimizingSystem = Depends(get_system)
):
    """Execute a query (v2)"""
    try:
        result = system.execute(
            user_query=request.query, conversation_context=request.conversation_context
        )

        # Trigger webhook for job completion
        webhook_manager = get_webhook_manager_instance()
        await webhook_manager.trigger_event(
            "job_finished",
            {
                "query": request.query,
                "validation_passed": result["validation_passed"],
                "optimization_attempted": result.get("optimization_attempted", False),
            },
        )

        # Notify WebSocket clients
        await notify_job_completed(
            job_id=str(hash(request.query)),
            success=result["validation_passed"],
            result={"output_length": len(result["output"])},
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


@app_v2.post("/feedback")
async def v2_provide_feedback(
    request: FeedbackRequest, system: SelfOptimizingSystem = Depends(get_system)
):
    """Provide manual feedback for system improvement (v2)"""
    try:
        result = system.request_instruction_update(
            user_feedback=request.feedback,
            severity=request.severity,
            attach_last_output=request.attach_last_output,
        )

        # Trigger webhook for optimization completion
        if result.get("success"):
            webhook_manager = get_webhook_manager_instance()
            await webhook_manager.trigger_event(
                "optimization_completed",
                {
                    "feedback": request.feedback,
                    "severity": request.severity,
                    "result": result,
                },
            )

            # Notify WebSocket clients
            await notify_optimization_completed(
                version_id=result.get("version_id", "unknown"),
                changes=result,
            )

        return {
            "success": result.get("success", False),
            "message": result.get("message", "Feedback processed"),
            "optimization_result": result,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Feedback error: {str(e)}")


@app_v2.get("/status", response_model=SystemStatus)
async def v2_get_status(system: SelfOptimizingSystem = Depends(get_system)):
    """Get system status (v2)"""
    try:
        history = system.get_version_history()
        total_optimizations = len([v for v in history if v["trigger_type"] != "initial"])
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


@app_v2.get("/versions", response_model=List[VersionInfo])
async def v2_get_versions(system: SelfOptimizingSystem = Depends(get_system)):
    """Get version history (v2)"""
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


# ============ Webhook Routes ============

@app_v2.post("/webhooks", response_model=WebhookInfo)
async def register_webhook(
    request: WebhookRegisterRequest,
    webhook_manager: WebhookManager = Depends(get_webhook_manager_instance),
):
    """Register a new webhook (v2)"""
    try:
        webhook_id = await webhook_manager.register(
            request.url, request.events, request.secret
        )
        return WebhookInfo(
            id=webhook_id,
            url=request.url,
            events=request.events,
            created_at=datetime.now().isoformat(),
            active=True,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Webhook registration error: {str(e)}")


# ============ Batch Processing Routes ============

try:
    from web.batch_routes import router as batch_router
    app_v2.include_router(batch_router)
    logger.info("Batch processing routes added to API v2")
except Exception as e:
    logger.warning(f"Failed to load batch processing routes: {e}")


@app_v2.get("/webhooks", response_model=List[WebhookInfo])
async def list_webhooks(
    webhook_manager: WebhookManager = Depends(get_webhook_manager_instance),
):
    """List all registered webhooks"""
    try:
        webhooks = webhook_manager.list_webhooks()
        return [WebhookInfo(**w) for w in webhooks]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing webhooks: {str(e)}")


@app_v2.delete("/webhooks/{webhook_id}")
async def unregister_webhook(
    webhook_id: str,
    webhook_manager: WebhookManager = Depends(get_webhook_manager_instance),
):
    """Unregister a webhook"""
    success = webhook_manager.unregister_webhook(webhook_id)
    if not success:
        raise HTTPException(status_code=404, detail="Webhook not found")
    return {"success": True, "message": "Webhook unregistered"}


@app_v2.post("/webhooks/{webhook_id}/activate")
async def activate_webhook(
    webhook_id: str,
    webhook_manager: WebhookManager = Depends(get_webhook_manager_instance),
):
    """Activate a webhook"""
    success = webhook_manager.activate_webhook(webhook_id)
    if not success:
        raise HTTPException(status_code=404, detail="Webhook not found")
    return {"success": True, "message": "Webhook activated"}


@app_v2.post("/webhooks/{webhook_id}/deactivate")
async def deactivate_webhook(
    webhook_id: str,
    webhook_manager: WebhookManager = Depends(get_webhook_manager_instance),
):
    """Deactivate a webhook"""
    success = webhook_manager.deactivate_webhook(webhook_id)
    if not success:
        raise HTTPException(status_code=404, detail="Webhook not found")
    return {"success": True, "message": "Webhook deactivated"}


# ============ WebSocket Routes ============

@app_v2.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates"""
    connection_manager = get_connection_manager()
    await connection_manager.connect(websocket)

    try:
        await handle_websocket_commands(websocket, connection_manager)
    except WebSocketDisconnect:
        connection_manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        connection_manager.disconnect(websocket)


@app_v2.websocket("/ws/workflows")
async def websocket_workflows(websocket: WebSocket):
    """WebSocket endpoint specifically for workflow updates"""
    connection_manager = get_connection_manager()
    await connection_manager.connect(websocket, channels=["workflows"])

    try:
        await handle_websocket_commands(websocket, connection_manager)
    except WebSocketDisconnect:
        connection_manager.disconnect(websocket)


@app_v2.websocket("/ws/jobs")
async def websocket_jobs(websocket: WebSocket):
    """WebSocket endpoint specifically for job updates"""
    connection_manager = get_connection_manager()
    await connection_manager.connect(websocket, channels=["jobs"])

    try:
        await handle_websocket_commands(websocket, connection_manager)
    except WebSocketDisconnect:
        connection_manager.disconnect(websocket)


# ============ GraphQL Routes ============

graphql_app = GraphQLRouter(schema, context_getter=get_graphql_context)
app_v2.include_router(graphql_app, prefix="/graphql")


# ============ Health Check ============

@app_v2.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "self-optimizing-system",
        "version": "2.0.0",
        "features": {
            "graphql": True,
            "websockets": True,
            "webhooks": True,
            "versioning": True,
        },
    }


# ============ Mount versioned apps ============

app.mount("/v1", app_v1)
app.mount("/v2", app_v2)


@app.get("/")
async def root():
    """Root endpoint with API versioning information"""
    return {
        "message": "Self-Optimizing Instruction Library API",
        "current_version": CURRENT_VERSION,
        "deprecated_versions": DEPRECATED_VERSIONS,
        "available_versions": {
            "v1": {
                "path": "/v1",
                "status": "deprecated",
                "sunset_date": "2026-06-01",
                "docs": "/v1/docs",
            },
            "v2": {
                "path": "/v2",
                "status": "current",
                "docs": "/v2/docs",
                "features": ["graphql", "websockets", "webhooks"],
            },
        },
        "migration_guide": "/docs/v2-migration",
    }


if __name__ == "__main__":
    # Run the server
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8000))
    debug = os.getenv("DEBUG", "false").lower() == "true"

    print(f"Starting server on {host}:{port}")
    print(f"API v2 available at: http://{host}:{port}/v2")
    print(f"GraphQL available at: http://{host}:{port}/v2/graphql")
    print(f"WebSocket available at: ws://{host}:{port}/v2/ws")

    uvicorn.run(
        "api_v2:app",
        host=host,
        port=port,
        reload=debug,
        log_level="info" if debug else "warning",
    )
