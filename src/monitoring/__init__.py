"""
Performance monitoring and metrics collection for the Self-Optimizing System
"""

from .metrics import MetricsCollector, SystemMetrics
from .dashboard import DashboardServer
from .alerts import AlertManager, AlertRule

__all__ = [
    "MetricsCollector",
    "SystemMetrics",
    "DashboardServer",
    "AlertManager",
    "AlertRule",
]
