"""
GraphQL schema for advanced API queries and mutations
"""

from typing import List, Optional, Dict, Any
import strawberry
from datetime import datetime


@strawberry.type
class ValidationResult:
    """Validation result type"""
    validator_name: str
    passed: bool
    error_message: Optional[str] = None


@strawberry.type
class OptimizationResult:
    """Optimization result type"""
    success: bool
    message: str
    rules_added: int
    rules_modified: int


@strawberry.type
class ExecutionResult:
    """Query execution result"""
    output: str
    validation_passed: bool
    validation_results: List[ValidationResult]
    optimization_attempted: bool
    optimization_result: Optional[OptimizationResult] = None


@strawberry.type
class VersionInfo:
    """Version information"""
    version_id: str
    timestamp: str
    trigger_type: str
    diff_summary: str
    rules_added: int
    rules_modified: int
    rules_deprecated: int


@strawberry.type
class SystemStatus:
    """System status information"""
    total_failures: int
    total_optimizations: int
    current_version: Optional[str]
    last_optimization: Optional[str]
    system_health: str


@strawberry.type
class FeedbackResult:
    """Feedback submission result"""
    success: bool
    message: str


@strawberry.type
class WebhookInfo:
    """Webhook registration information"""
    id: str
    url: str
    events: List[str]
    created_at: str
    active: bool


@strawberry.input
class ExecuteInput:
    """Input for executing a query"""
    query: str
    conversation_context: Optional[List[str]] = None


@strawberry.input
class FeedbackInput:
    """Input for providing feedback"""
    feedback: str
    severity: str = "moderate"
    attach_last_output: bool = True


@strawberry.input
class WebhookInput:
    """Input for registering a webhook"""
    url: str
    events: List[str]
    secret: Optional[str] = None


@strawberry.type
class Query:
    """GraphQL queries"""

    @strawberry.field
    def status(self, info) -> SystemStatus:
        """Get system status"""
        system = info.context["system"]
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

    @strawberry.field
    def versions(self, info) -> List[VersionInfo]:
        """Get version history"""
        system = info.context["system"]
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

    @strawberry.field
    def webhooks(self, info) -> List[WebhookInfo]:
        """Get registered webhooks"""
        webhook_manager = info.context["webhook_manager"]
        webhooks = webhook_manager.list_webhooks()
        return [
            WebhookInfo(
                id=w["id"],
                url=w["url"],
                events=w["events"],
                created_at=w["created_at"],
                active=w["active"],
            )
            for w in webhooks
        ]


@strawberry.type
class Mutation:
    """GraphQL mutations"""

    @strawberry.mutation
    def execute(self, info, input: ExecuteInput) -> ExecutionResult:
        """Execute a query"""
        system = info.context["system"]
        result = system.execute(
            user_query=input.query,
            conversation_context=input.conversation_context,
        )

        validation_results = [
            ValidationResult(
                validator_name=r.validator_name,
                passed=r.passed,
                error_message=r.error_message,
            )
            for r in result["validation_results"]
        ]

        optimization_result = None
        if result.get("optimization_result"):
            opt = result["optimization_result"]
            optimization_result = OptimizationResult(
                success=opt.get("success", False),
                message=opt.get("message", ""),
                rules_added=opt.get("rules_added", 0),
                rules_modified=opt.get("rules_modified", 0),
            )

        return ExecutionResult(
            output=result["output"],
            validation_passed=result["validation_passed"],
            validation_results=validation_results,
            optimization_attempted=result.get("optimization_attempted", False),
            optimization_result=optimization_result,
        )

    @strawberry.mutation
    def provide_feedback(self, info, input: FeedbackInput) -> FeedbackResult:
        """Provide feedback for system improvement"""
        system = info.context["system"]
        result = system.request_instruction_update(
            user_feedback=input.feedback,
            severity=input.severity,
            attach_last_output=input.attach_last_output,
        )

        return FeedbackResult(
            success=result.get("success", False),
            message=result.get("message", "Feedback processed"),
        )

    @strawberry.mutation
    def register_webhook(self, info, input: WebhookInput) -> WebhookInfo:
        """Register a new webhook"""
        webhook_manager = info.context["webhook_manager"]
        webhook = webhook_manager.register_webhook(
            url=input.url, events=input.events, secret=input.secret
        )

        return WebhookInfo(
            id=webhook["id"],
            url=webhook["url"],
            events=webhook["events"],
            created_at=webhook["created_at"],
            active=webhook["active"],
        )

    @strawberry.mutation
    def unregister_webhook(self, info, webhook_id: str) -> bool:
        """Unregister a webhook"""
        webhook_manager = info.context["webhook_manager"]
        return webhook_manager.unregister_webhook(webhook_id)

    @strawberry.mutation
    def rollback(self, info, steps: int) -> bool:
        """Rollback to a previous version"""
        system = info.context["system"]
        return system.rollback(steps)


# Create the schema
schema = strawberry.Schema(query=Query, mutation=Mutation)
