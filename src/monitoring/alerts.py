"""
Alert system for monitoring and notifications
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime, timedelta
from enum import Enum
import json
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import requests


class AlertSeverity(Enum):
    """Alert severity levels"""

    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class AlertChannel(Enum):
    """Alert notification channels"""

    EMAIL = "email"
    SLACK = "slack"
    WEBHOOK = "webhook"
    CONSOLE = "console"


@dataclass
class AlertRule:
    """Rule for triggering alerts"""

    name: str
    condition: str  # Python expression that evaluates to True/False
    severity: AlertSeverity
    channels: List[AlertChannel]
    cooldown_minutes: int = 5
    last_triggered: Optional[datetime] = None

    def should_trigger(self, metrics: Dict[str, Any]) -> bool:
        """Check if alert should trigger based on metrics"""
        # Check cooldown
        if self.last_triggered:
            cooldown_end = self.last_triggered + timedelta(
                minutes=self.cooldown_minutes
            )
            if datetime.now() < cooldown_end:
                return False

        # Evaluate condition
        try:
            # Create safe evaluation context
            context = {
                "metrics": metrics,
                "now": datetime.now(),
                "timedelta": timedelta,
                "len": len,
                "sum": sum,
                "min": min,
                "max": max,
                "avg": lambda x: sum(x) / len(x) if x else 0,
            }

            # Evaluate condition
            result = eval(self.condition, {"__builtins__": {}}, context)
            return bool(result)
        except Exception:
            return False

    def trigger(self, metrics: Dict[str, Any]) -> "Alert":
        """Trigger the alert"""
        self.last_triggered = datetime.now()
        return Alert(
            rule_name=self.name,
            severity=self.severity,
            message=self._generate_message(metrics),
            metrics=metrics,
            timestamp=datetime.now(),
        )

    def _generate_message(self, metrics: Dict[str, Any]) -> str:
        """Generate alert message"""
        if self.severity == AlertSeverity.CRITICAL:
            return f"🚨 CRITICAL: {self.name} - System requires immediate attention"
        elif self.severity == AlertSeverity.WARNING:
            return f"⚠️ WARNING: {self.name} - System performance degraded"
        else:
            return f"ℹ️ INFO: {self.name} - System notification"


@dataclass
class Alert:
    """Alert instance"""

    rule_name: str
    severity: AlertSeverity
    message: str
    metrics: Dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.now)
    acknowledged: bool = False
    acknowledged_by: Optional[str] = None
    acknowledged_at: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert alert to dictionary"""
        return {
            "rule_name": self.rule_name,
            "severity": self.severity.value,
            "message": self.message,
            "timestamp": self.timestamp.isoformat(),
            "acknowledged": self.acknowledged,
            "acknowledged_by": self.acknowledged_by,
            "acknowledged_at": self.acknowledged_at.isoformat()
            if self.acknowledged_at
            else None,
            "metrics": self.metrics,
        }

    def acknowledge(self, user: str):
        """Acknowledge the alert"""
        self.acknowledged = True
        self.acknowledged_by = user
        self.acknowledged_at = datetime.now()


class AlertManager:
    """Manages alerts and notifications"""

    def __init__(self):
        self.rules: List[AlertRule] = []
        self.alerts: List[Alert] = []
        self.notification_handlers: Dict[AlertChannel, Callable] = {
            AlertChannel.CONSOLE: self._send_console_notification,
        }

        # Load default rules
        self._load_default_rules()

    def _load_default_rules(self):
        """Load default alert rules"""
        default_rules = [
            AlertRule(
                name="High Failure Rate",
                condition="metrics.get('execution', {}).get('failed_queries', 0) > 10 and metrics.get('execution', {}).get('success_rate', 1) < 0.8",
                severity=AlertSeverity.CRITICAL,
                channels=[AlertChannel.CONSOLE, AlertChannel.EMAIL],
            ),
            AlertRule(
                name="Slow Response Time",
                condition="metrics.get('execution', {}).get('avg_response_time', 0) > 5.0",
                severity=AlertSeverity.WARNING,
                channels=[AlertChannel.CONSOLE],
            ),
            AlertRule(
                name="High Memory Usage",
                condition="metrics.get('system_health', {}).get('memory_usage_mb', 0) > 1000",
                severity=AlertSeverity.WARNING,
                channels=[AlertChannel.CONSOLE],
            ),
            AlertRule(
                name="High CPU Usage",
                condition="metrics.get('system_health', {}).get('cpu_percent', 0) > 80",
                severity=AlertSeverity.WARNING,
                channels=[AlertChannel.CONSOLE],
            ),
            AlertRule(
                name="Optimization Failure",
                condition="metrics.get('optimization', {}).get('success_rate', 1) < 0.5",
                severity=AlertSeverity.WARNING,
                channels=[AlertChannel.CONSOLE],
            ),
            AlertRule(
                name="High Cost Alert",
                condition="metrics.get('cost', {}).get('estimated_cost', 0) > 100",
                severity=AlertSeverity.WARNING,
                channels=[AlertChannel.CONSOLE, AlertChannel.EMAIL],
            ),
            AlertRule(
                name="System Down",
                condition="'system_health' not in metrics or metrics.get('system_health', {}).get('uptime_seconds', 0) < 60",
                severity=AlertSeverity.CRITICAL,
                channels=[AlertChannel.CONSOLE, AlertChannel.EMAIL, AlertChannel.SLACK],
            ),
        ]

        self.rules.extend(default_rules)

    def add_rule(self, rule: AlertRule):
        """Add a new alert rule"""
        self.rules.append(rule)

    def remove_rule(self, rule_name: str):
        """Remove an alert rule"""
        self.rules = [r for r in self.rules if r.name != rule_name]

    def check_metrics(self, metrics: Dict[str, Any]) -> List[Alert]:
        """Check metrics against all rules and trigger alerts"""
        triggered_alerts = []

        for rule in self.rules:
            if rule.should_trigger(metrics):
                alert = rule.trigger(metrics)
                triggered_alerts.append(alert)
                self.alerts.append(alert)

                # Send notifications
                self._send_notifications(alert, rule.channels)

        # Keep only recent alerts (last 24 hours)
        cutoff_time = datetime.now() - timedelta(hours=24)
        self.alerts = [a for a in self.alerts if a.timestamp > cutoff_time]

        return triggered_alerts

    def _send_notifications(self, alert: Alert, channels: List[AlertChannel]):
        """Send notifications through specified channels"""
        for channel in channels:
            handler = self.notification_handlers.get(channel)
            if handler:
                try:
                    handler(alert)
                except Exception as e:
                    print(f"Failed to send {channel.value} notification: {e}")

    def _send_console_notification(self, alert: Alert):
        """Send notification to console"""
        print(f"\n{'=' * 60}")
        print(f"ALERT: {alert.message}")
        print(f"Time: {alert.timestamp}")
        print(f"Severity: {alert.severity.value.upper()}")
        print(f"{'=' * 60}\n")

    def _send_email_notification(self, alert: Alert, config: Dict[str, Any]):
        """Send email notification"""
        # This would be implemented with actual email configuration
        pass

    def _send_slack_notification(self, alert: Alert, config: Dict[str, Any]):
        """Send Slack notification"""
        # This would be implemented with actual Slack webhook
        pass

    def _send_webhook_notification(self, alert: Alert, config: Dict[str, Any]):
        """Send webhook notification"""
        # This would be implemented with actual webhook URL
        pass

    def get_active_alerts(self) -> List[Alert]:
        """Get active (unacknowledged) alerts"""
        return [a for a in self.alerts if not a.acknowledged]

    def get_alerts_by_severity(self, severity: AlertSeverity) -> List[Alert]:
        """Get alerts by severity"""
        return [a for a in self.alerts if a.severity == severity]

    def get_recent_alerts(self, hours: int = 24) -> List[Alert]:
        """Get alerts from the last N hours"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        return [a for a in self.alerts if a.timestamp > cutoff_time]

    def acknowledge_alert(self, alert_id: int, user: str) -> bool:
        """Acknowledge an alert"""
        if 0 <= alert_id < len(self.alerts):
            self.alerts[alert_id].acknowledge(user)
            return True
        return False

    def configure_email(
        self,
        smtp_server: str,
        smtp_port: int,
        username: str,
        password: str,
        from_email: str,
        to_emails: List[str],
    ):
        """Configure email notifications"""
        self.email_config = {
            "smtp_server": smtp_server,
            "smtp_port": smtp_port,
            "username": username,
            "password": password,
            "from_email": from_email,
            "to_emails": to_emails,
        }
        self.notification_handlers[AlertChannel.EMAIL] = (
            lambda alert: self._send_email_notification(alert, self.email_config)
        )

    def configure_slack(self, webhook_url: str):
        """Configure Slack notifications"""
        self.slack_config = {"webhook_url": webhook_url}
        self.notification_handlers[AlertChannel.SLACK] = (
            lambda alert: self._send_slack_notification(alert, self.slack_config)
        )

    def configure_webhook(self, webhook_url: str):
        """Configure webhook notifications"""
        self.webhook_config = {"webhook_url": webhook_url}
        self.notification_handlers[AlertChannel.WEBHOOK] = (
            lambda alert: self._send_webhook_notification(alert, self.webhook_config)
        )

    def export_alerts(self, filepath: str):
        """Export alerts to JSON file"""
        alerts_data = [alert.to_dict() for alert in self.alerts]
        with open(filepath, "w") as f:
            json.dump(alerts_data, f, indent=2, default=str)

    def import_alerts(self, filepath: str):
        """Import alerts from JSON file"""
        with open(filepath, "r") as f:
            alerts_data = json.load(f)

        for alert_data in alerts_data:
            alert = Alert(
                rule_name=alert_data["rule_name"],
                severity=AlertSeverity(alert_data["severity"]),
                message=alert_data["message"],
                metrics=alert_data["metrics"],
                timestamp=datetime.fromisoformat(alert_data["timestamp"]),
                acknowledged=alert_data["acknowledged"],
                acknowledged_by=alert_data["acknowledged_by"],
                acknowledged_at=datetime.fromisoformat(alert_data["acknowledged_at"])
                if alert_data["acknowledged_at"]
                else None,
            )
            self.alerts.append(alert)
