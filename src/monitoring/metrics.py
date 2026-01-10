"""
Metrics collection and aggregation for performance monitoring
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import time
import statistics
from collections import defaultdict, deque
import json


@dataclass
class SystemMetrics:
    """System performance metrics"""

    # Execution metrics
    total_queries: int = 0
    successful_queries: int = 0
    failed_queries: int = 0
    avg_response_time: float = 0.0
    p95_response_time: float = 0.0
    p99_response_time: float = 0.0

    # Optimization metrics
    total_optimizations: int = 0
    successful_optimizations: int = 0
    failed_optimizations: int = 0
    avg_optimization_time: float = 0.0

    # Failure metrics
    total_failures: int = 0
    failures_by_type: Dict[str, int] = field(default_factory=dict)
    failures_by_severity: Dict[str, int] = field(default_factory=dict)

    # Validation metrics
    validation_passed: int = 0
    validation_failed: int = 0
    validation_errors_by_type: Dict[str, int] = field(default_factory=dict)

    # Cost metrics (for LLM usage)
    total_tokens_used: int = 0
    estimated_cost: float = 0.0
    cost_by_model: Dict[str, float] = field(default_factory=dict)

    # System health
    uptime_seconds: float = 0.0
    memory_usage_mb: float = 0.0
    cpu_percent: float = 0.0

    # Timestamps
    timestamp: datetime = field(default_factory=datetime.now)
    collection_interval_seconds: int = 60

    def to_dict(self) -> Dict[str, Any]:
        """Convert metrics to dictionary"""
        return {
            "execution": {
                "total_queries": self.total_queries,
                "successful_queries": self.successful_queries,
                "failed_queries": self.failed_queries,
                "avg_response_time": self.avg_response_time,
                "p95_response_time": self.p95_response_time,
                "p99_response_time": self.p99_response_time,
                "success_rate": self.successful_queries / max(self.total_queries, 1),
            },
            "optimization": {
                "total_optimizations": self.total_optimizations,
                "successful_optimizations": self.successful_optimizations,
                "failed_optimizations": self.failed_optimizations,
                "avg_optimization_time": self.avg_optimization_time,
                "success_rate": self.successful_optimizations
                / max(self.total_optimizations, 1),
            },
            "failures": {
                "total_failures": self.total_failures,
                "by_type": self.failures_by_type,
                "by_severity": self.failures_by_severity,
            },
            "validation": {
                "passed": self.validation_passed,
                "failed": self.validation_failed,
                "errors_by_type": self.validation_errors_by_type,
                "pass_rate": self.validation_passed
                / max(self.validation_passed + self.validation_failed, 1),
            },
            "cost": {
                "total_tokens": self.total_tokens_used,
                "estimated_cost": self.estimated_cost,
                "cost_by_model": self.cost_by_model,
            },
            "system_health": {
                "uptime_seconds": self.uptime_seconds,
                "memory_usage_mb": self.memory_usage_mb,
                "cpu_percent": self.cpu_percent,
            },
            "timestamp": self.timestamp.isoformat(),
            "collection_interval": self.collection_interval_seconds,
        }

    def to_json(self) -> str:
        """Convert metrics to JSON string"""
        return json.dumps(self.to_dict(), indent=2, default=str)


class MetricsCollector:
    """Collects and aggregates system metrics"""

    def __init__(self, retention_hours: int = 24):
        self.retention_hours = retention_hours
        self.start_time = datetime.now()

        # Storage for metrics
        self.metrics_history: List[SystemMetrics] = []
        self.response_times: deque = deque(maxlen=1000)
        self.optimization_times: deque = deque(maxlen=100)

        # Counters
        self.query_counters = defaultdict(int)
        self.optimization_counters = defaultdict(int)
        self.failure_counters = defaultdict(int)
        self.validation_counters = defaultdict(int)
        self.token_counters = defaultdict(int)

        # Current metrics
        self.current_metrics = SystemMetrics()

    def record_query(self, success: bool, response_time: float, tokens_used: int = 0):
        """Record a query execution"""
        self.query_counters["total"] += 1
        if success:
            self.query_counters["success"] += 1
        else:
            self.query_counters["failed"] += 1

        self.response_times.append(response_time)
        self.token_counters["total"] += tokens_used

    def record_optimization(
        self, success: bool, optimization_time: float, tokens_used: int = 0
    ):
        """Record an optimization attempt"""
        self.optimization_counters["total"] += 1
        if success:
            self.optimization_counters["success"] += 1
        else:
            self.optimization_counters["failed"] += 1

        self.optimization_times.append(optimization_time)
        self.token_counters["total"] += tokens_used

    def record_failure(self, failure_type: str, severity: str):
        """Record a failure"""
        self.failure_counters["total"] += 1
        self.failure_counters[f"type_{failure_type}"] = (
            self.failure_counters.get(f"type_{failure_type}", 0) + 1
        )
        self.failure_counters[f"severity_{severity}"] = (
            self.failure_counters.get(f"severity_{severity}", 0) + 1
        )

    def record_validation(self, passed: bool, error_type: Optional[str] = None):
        """Record a validation result"""
        if passed:
            self.validation_counters["passed"] += 1
        else:
            self.validation_counters["failed"] += 1
            if error_type:
                self.validation_counters[f"error_{error_type}"] = (
                    self.validation_counters.get(f"error_{error_type}", 0) + 1
                )

    def record_cost(self, model: str, tokens: int, cost: float):
        """Record cost for LLM usage"""
        self.token_counters[model] = self.token_counters.get(model, 0) + tokens
        self.token_counters[f"cost_{model}"] = (
            self.token_counters.get(f"cost_{model}", 0) + cost
        )

    def collect_metrics(self) -> SystemMetrics:
        """Collect current metrics and reset counters"""
        import psutil
        import os

        # Calculate response time percentiles
        response_times_list = list(self.response_times)
        if response_times_list:
            avg_response_time = statistics.mean(response_times_list)
            p95_response_time = (
                statistics.quantiles(response_times_list, n=20)[18]
                if len(response_times_list) >= 20
                else avg_response_time
            )
            p99_response_time = (
                statistics.quantiles(response_times_list, n=100)[98]
                if len(response_times_list) >= 100
                else avg_response_time
            )
        else:
            avg_response_time = p95_response_time = p99_response_time = 0.0

        # Calculate optimization time average
        optimization_times_list = list(self.optimization_times)
        avg_optimization_time = (
            statistics.mean(optimization_times_list) if optimization_times_list else 0.0
        )

        # Get system health metrics
        process = psutil.Process(os.getpid())
        memory_usage = process.memory_info().rss / 1024 / 1024  # MB
        cpu_percent = process.cpu_percent(interval=0.1)
        uptime = (datetime.now() - self.start_time).total_seconds()

        # Create metrics object
        metrics = SystemMetrics(
            total_queries=self.query_counters["total"],
            successful_queries=self.query_counters["success"],
            failed_queries=self.query_counters["failed"],
            avg_response_time=avg_response_time,
            p95_response_time=p95_response_time,
            p99_response_time=p99_response_time,
            total_optimizations=self.optimization_counters["total"],
            successful_optimizations=self.optimization_counters["success"],
            failed_optimizations=self.optimization_counters["failed"],
            avg_optimization_time=avg_optimization_time,
            total_failures=self.failure_counters["total"],
            failures_by_type={
                k.replace("type_", ""): v
                for k, v in self.failure_counters.items()
                if k.startswith("type_")
            },
            failures_by_severity={
                k.replace("severity_", ""): v
                for k, v in self.failure_counters.items()
                if k.startswith("severity_")
            },
            validation_passed=self.validation_counters["passed"],
            validation_failed=self.validation_counters["failed"],
            validation_errors_by_type={
                k.replace("error_", ""): v
                for k, v in self.validation_counters.items()
                if k.startswith("error_")
            },
            total_tokens_used=self.token_counters["total"],
            estimated_cost=sum(
                v for k, v in self.token_counters.items() if k.startswith("cost_")
            ),
            cost_by_model={
                k: self.token_counters.get(f"cost_{k}", 0)
                for k in self.token_counters.keys()
                if not k.startswith("cost_") and k != "total"
            },
            uptime_seconds=uptime,
            memory_usage_mb=memory_usage,
            cpu_percent=cpu_percent,
        )

        # Store in history
        self.metrics_history.append(metrics)
        self.current_metrics = metrics

        # Clean old metrics
        cutoff_time = datetime.now() - timedelta(hours=self.retention_hours)
        self.metrics_history = [
            m for m in self.metrics_history if m.timestamp > cutoff_time
        ]

        # Reset counters for next interval
        self._reset_counters()

        return metrics

    def _reset_counters(self):
        """Reset counters for next collection interval"""
        # Keep response times and optimization times for percentiles
        # Only reset counters
        self.query_counters.clear()
        self.optimization_counters.clear()
        self.failure_counters.clear()
        self.validation_counters.clear()
        # Don't reset token counters - they accumulate

    def get_historical_metrics(self, hours: int = 1) -> List[SystemMetrics]:
        """Get metrics from the last N hours"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        return [m for m in self.metrics_history if m.timestamp > cutoff_time]

    def get_summary(self, hours: int = 1) -> Dict[str, Any]:
        """Get summary metrics for the last N hours"""
        recent_metrics = self.get_historical_metrics(hours)
        if not recent_metrics:
            return {}

        # Aggregate metrics
        summary = {
            "period_hours": hours,
            "start_time": min(m.timestamp for m in recent_metrics).isoformat(),
            "end_time": max(m.timestamp for m in recent_metrics).isoformat(),
            "total_queries": sum(m.total_queries for m in recent_metrics),
            "successful_queries": sum(m.successful_queries for m in recent_metrics),
            "failed_queries": sum(m.failed_queries for m in recent_metrics),
            "avg_response_time": statistics.mean(
                [m.avg_response_time for m in recent_metrics if m.avg_response_time > 0]
            ),
            "total_optimizations": sum(m.total_optimizations for m in recent_metrics),
            "successful_optimizations": sum(
                m.successful_optimizations for m in recent_metrics
            ),
            "total_failures": sum(m.total_failures for m in recent_metrics),
            "total_tokens": sum(m.total_tokens_used for m in recent_metrics),
            "estimated_cost": sum(m.estimated_cost for m in recent_metrics),
        }

        # Calculate rates
        summary["query_success_rate"] = summary["successful_queries"] / max(
            summary["total_queries"], 1
        )
        summary["optimization_success_rate"] = summary[
            "successful_optimizations"
        ] / max(summary["total_optimizations"], 1)

        return summary
