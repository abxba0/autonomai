"""
Audit logging and security monitoring
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from enum import Enum
from dataclasses import dataclass, field, asdict
from pathlib import Path
import sqlite3
from contextlib import contextmanager


class AuditEventType(str, Enum):
    """Types of audit events"""

    # Authentication events
    LOGIN_SUCCESS = "login_success"
    LOGIN_FAILURE = "login_failure"
    LOGOUT = "logout"
    TOKEN_REFRESH = "token_refresh"
    API_KEY_USED = "api_key_used"
    API_KEY_REVOKED = "api_key_revoked"

    # Authorization events
    PERMISSION_DENIED = "permission_denied"
    ROLE_CHANGED = "role_changed"

    # System events
    QUERY_EXECUTED = "query_executed"
    OPTIMIZATION_PERFORMED = "optimization_performed"
    FAILURE_PROCESSED = "failure_processed"
    INSTRUCTION_UPDATED = "instruction_updated"
    VERSION_ROLLBACK = "version_rollback"

    # Security events
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    SUSPICIOUS_INPUT = "suspicious_input"
    SECURITY_ALERT = "security_alert"
    CONFIGURATION_CHANGED = "configuration_changed"

    # User events
    USER_CREATED = "user_created"
    USER_UPDATED = "user_updated"
    USER_DELETED = "user_deleted"


class AuditSeverity(str, Enum):
    """Severity levels for audit events"""

    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class AuditEvent:
    """Audit event data"""

    event_id: str
    event_type: AuditEventType
    severity: AuditSeverity
    timestamp: datetime = field(default_factory=datetime.utcnow)
    user_id: Optional[str] = None
    username: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    resource: Optional[str] = None
    action: Optional[str] = None
    details: Dict[str, Any] = field(default_factory=dict)
    success: bool = True
    error_message: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        data = asdict(self)
        data["timestamp"] = self.timestamp.isoformat()
        data["event_type"] = self.event_type.value
        data["severity"] = self.severity.value
        return data

    def to_json(self) -> str:
        """Convert to JSON string"""
        return json.dumps(self.to_dict(), default=str)


class AuditLogger:
    """Audit logging system"""

    def __init__(
        self,
        log_file: Optional[str] = None,
        database_file: Optional[str] = None,
        enable_console: bool = True,
    ):
        self.log_file = log_file
        self.database_file = database_file
        self.enable_console = enable_console

        # Set up file logging
        if log_file:
            log_dir = Path(log_file).parent
            log_dir.mkdir(parents=True, exist_ok=True)

            self.file_handler = logging.FileHandler(log_file)
            self.file_handler.setLevel(logging.INFO)
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
            self.file_handler.setFormatter(formatter)

        # Set up database
        if database_file:
            self._init_database()

    def _init_database(self):
        """Initialize audit database"""
        conn = sqlite3.connect(self.database_file)
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS audit_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_id TEXT NOT NULL,
                event_type TEXT NOT NULL,
                severity TEXT NOT NULL,
                timestamp DATETIME NOT NULL,
                user_id TEXT,
                username TEXT,
                ip_address TEXT,
                user_agent TEXT,
                resource TEXT,
                action TEXT,
                details TEXT,
                success BOOLEAN,
                error_message TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Create indexes for common queries
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_event_type ON audit_events(event_type)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_timestamp ON audit_events(timestamp)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_user_id ON audit_events(user_id)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_severity ON audit_events(severity)"
        )

        conn.commit()
        conn.close()

    @contextmanager
    def _get_db_connection(self):
        """Get database connection with context manager"""
        if not self.database_file:
            yield None
            return

        conn = sqlite3.connect(self.database_file)
        try:
            yield conn
        finally:
            conn.close()

    def log_event(self, event: AuditEvent):
        """Log an audit event"""
        # Log to console
        if self.enable_console:
            log_message = (
                f"[{event.severity.upper()}] {event.event_type}: {event.details}"
            )
            if event.user_id:
                log_message = f"User {event.user_id} - {log_message}"
            print(log_message)

        # Log to file
        if self.log_file:
            with open(self.log_file, "a") as f:
                f.write(event.to_json() + "\n")

        # Log to database
        if self.database_file:
            with self._get_db_connection() as conn:
                if conn:
                    cursor = conn.cursor()
                    cursor.execute(
                        """
                        INSERT INTO audit_events (
                            event_id, event_type, severity, timestamp,
                            user_id, username, ip_address, user_agent,
                            resource, action, details, success, error_message
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                        (
                            event.event_id,
                            event.event_type.value,
                            event.severity.value,
                            event.timestamp.isoformat(),
                            event.user_id,
                            event.username,
                            event.ip_address,
                            event.user_agent,
                            event.resource,
                            event.action,
                            json.dumps(event.details, default=str),
                            event.success,
                            event.error_message,
                        ),
                    )
                    conn.commit()

    def get_events(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        event_type: Optional[AuditEventType] = None,
        user_id: Optional[str] = None,
        severity: Optional[AuditSeverity] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[AuditEvent]:
        """Retrieve audit events with filters"""
        events = []

        if self.database_file:
            with self._get_db_connection() as conn:
                if conn:
                    cursor = conn.cursor()

                    # Build query
                    query = "SELECT * FROM audit_events WHERE 1=1"
                    params = []

                    if start_time:
                        query += " AND timestamp >= ?"
                        params.append(start_time.isoformat())

                    if end_time:
                        query += " AND timestamp <= ?"
                        params.append(end_time.isoformat())

                    if event_type:
                        query += " AND event_type = ?"
                        params.append(event_type.value)

                    if user_id:
                        query += " AND user_id = ?"
                        params.append(user_id)

                    if severity:
                        query += " AND severity = ?"
                        params.append(severity.value)

                    query += " ORDER BY timestamp DESC LIMIT ? OFFSET ?"
                    params.extend([limit, offset])

                    cursor.execute(query, params)
                    rows = cursor.fetchall()

                    # Convert rows to AuditEvent objects
                    for row in rows:
                        event = AuditEvent(
                            event_id=row[1],
                            event_type=AuditEventType(row[2]),
                            severity=AuditSeverity(row[3]),
                            timestamp=datetime.fromisoformat(row[4]),
                            user_id=row[5],
                            username=row[6],
                            ip_address=row[7],
                            user_agent=row[8],
                            resource=row[9],
                            action=row[10],
                            details=json.loads(row[11]) if row[11] else {},
                            success=bool(row[12]),
                            error_message=row[13],
                        )
                        events.append(event)

        return events

    def get_statistics(
        self, start_time: Optional[datetime] = None, end_time: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Get audit statistics"""
        stats = {
            "total_events": 0,
            "events_by_type": {},
            "events_by_severity": {},
            "events_by_user": {},
            "success_rate": 0.0,
        }

        if self.database_file:
            with self._get_db_connection() as conn:
                if conn:
                    cursor = conn.cursor()

                    # Build where clause
                    where_clause = ""
                    params = []

                    if start_time or end_time:
                        conditions = []
                        if start_time:
                            conditions.append("timestamp >= ?")
                            params.append(start_time.isoformat())
                        if end_time:
                            conditions.append("timestamp <= ?")
                            params.append(end_time.isoformat())
                        where_clause = "WHERE " + " AND ".join(conditions)

                    # Total events
                    cursor.execute(
                        f"SELECT COUNT(*) FROM audit_events {where_clause}", params
                    )
                    stats["total_events"] = cursor.fetchone()[0]

                    # Events by type
                    cursor.execute(
                        f"SELECT event_type, COUNT(*) FROM audit_events {where_clause} GROUP BY event_type",
                        params,
                    )
                    for event_type, count in cursor.fetchall():
                        stats["events_by_type"][event_type] = count

                    # Events by severity
                    cursor.execute(
                        f"SELECT severity, COUNT(*) FROM audit_events {where_clause} GROUP BY severity",
                        params,
                    )
                    for severity, count in cursor.fetchall():
                        stats["events_by_severity"][severity] = count

                    # Events by user
                    cursor.execute(
                        f"SELECT user_id, COUNT(*) FROM audit_events WHERE user_id IS NOT NULL {where_clause.replace('WHERE', 'AND') if where_clause else ''} GROUP BY user_id",
                        params,
                    )
                    for user_id, count in cursor.fetchall():
                        stats["events_by_user"][user_id] = count

                    # Success rate
                    if stats["total_events"] > 0:
                        cursor.execute(
                            f"SELECT COUNT(*) FROM audit_events {where_clause} AND success = 1",
                            params,
                        )
                        success_count = cursor.fetchone()[0]
                        stats["success_rate"] = (
                            success_count / stats["total_events"]
                        ) * 100

        return stats


class SecurityMonitor:
    """Security monitoring and alerting"""

    def __init__(
        self,
        audit_logger: AuditLogger,
        alert_thresholds: Optional[Dict[str, int]] = None,
    ):
        self.audit_logger = audit_logger
        self.alert_thresholds = alert_thresholds or {
            "failed_logins_per_hour": 10,
            "suspicious_inputs_per_hour": 5,
            "rate_limit_exceeded_per_hour": 20,
            "permission_denied_per_hour": 10,
        }

        # Track recent events for rate-based alerts
        self.recent_events: List[AuditEvent] = []

    def monitor_suspicious_activity(self, event: AuditEvent):
        """Monitor for suspicious activity and generate alerts"""
        # Add to recent events
        self.recent_events.append(event)

        # Clean old events (older than 1 hour)
        one_hour_ago = datetime.utcnow() - timedelta(hours=1)
        self.recent_events = [
            e for e in self.recent_events if e.timestamp > one_hour_ago
        ]

        # Check for suspicious patterns
        alerts = []

        # Check failed login attempts
        failed_logins = [
            e
            for e in self.recent_events
            if e.event_type == AuditEventType.LOGIN_FAILURE
        ]
        if len(failed_logins) >= self.alert_thresholds["failed_logins_per_hour"]:
            alerts.append(
                {
                    "type": "excessive_failed_logins",
                    "count": len(failed_logins),
                    "threshold": self.alert_thresholds["failed_logins_per_hour"],
                    "users": list(set(e.user_id for e in failed_logins if e.user_id)),
                }
            )

        # Check suspicious inputs
        suspicious_inputs = [
            e
            for e in self.recent_events
            if e.event_type == AuditEventType.SUSPICIOUS_INPUT
        ]
        if (
            len(suspicious_inputs)
            >= self.alert_thresholds["suspicious_inputs_per_hour"]
        ):
            alerts.append(
                {
                    "type": "excessive_suspicious_inputs",
                    "count": len(suspicious_inputs),
                    "threshold": self.alert_thresholds["suspicious_inputs_per_hour"],
                    "sources": list(
                        set(e.ip_address for e in suspicious_inputs if e.ip_address)
                    ),
                }
            )

        # Check rate limit exceeded
        rate_limit_exceeded = [
            e
            for e in self.recent_events
            if e.event_type == AuditEventType.RATE_LIMIT_EXCEEDED
        ]
        if (
            len(rate_limit_exceeded)
            >= self.alert_thresholds["rate_limit_exceeded_per_hour"]
        ):
            alerts.append(
                {
                    "type": "excessive_rate_limit_violations",
                    "count": len(rate_limit_exceeded),
                    "threshold": self.alert_thresholds["rate_limit_exceeded_per_hour"],
                    "clients": list(
                        set(e.user_id for e in rate_limit_exceeded if e.user_id)
                    ),
                }
            )

        # Generate alert events
        for alert in alerts:
            alert_event = AuditEvent(
                event_id=f"alert_{datetime.utcnow().timestamp()}",
                event_type=AuditEventType.SECURITY_ALERT,
                severity=AuditSeverity.WARNING,
                details=alert,
                resource="security_monitor",
                action="alert_generated",
            )
            self.audit_logger.log_event(alert_event)

        return alerts

    def get_security_report(self, hours: int = 24) -> Dict[str, Any]:
        """Generate security report for the specified time period"""
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=hours)

        events = self.audit_logger.get_events(start_time=start_time, end_time=end_time)

        report = {
            "time_period": {
                "start": start_time.isoformat(),
                "end": end_time.isoformat(),
                "hours": hours,
            },
            "total_events": len(events),
            "security_events": {
                "failed_logins": 0,
                "suspicious_inputs": 0,
                "rate_limit_exceeded": 0,
                "permission_denied": 0,
                "security_alerts": 0,
            },
            "top_users": {},
            "top_ips": {},
            "recommendations": [],
        }

        # Count security events
        for event in events:
            if event.event_type == AuditEventType.LOGIN_FAILURE:
                report["security_events"]["failed_logins"] += 1
            elif event.event_type == AuditEventType.SUSPICIOUS_INPUT:
                report["security_events"]["suspicious_inputs"] += 1
            elif event.event_type == AuditEventType.RATE_LIMIT_EXCEEDED:
                report["security_events"]["rate_limit_exceeded"] += 1
            elif event.event_type == AuditEventType.PERMISSION_DENIED:
                report["security_events"]["permission_denied"] += 1
            elif event.event_type == AuditEventType.SECURITY_ALERT:
                report["security_events"]["security_alerts"] += 1

            # Track top users
            if event.user_id:
                report["top_users"][event.user_id] = (
                    report["top_users"].get(event.user_id, 0) + 1
                )

            # Track top IPs
            if event.ip_address:
                report["top_ips"][event.ip_address] = (
                    report["top_ips"].get(event.ip_address, 0) + 1
                )

        # Generate recommendations
        if report["security_events"]["failed_logins"] > 50:
            report["recommendations"].append(
                "High number of failed login attempts. Consider implementing account lockout."
            )

        if report["security_events"]["suspicious_inputs"] > 20:
            report["recommendations"].append(
                "Multiple suspicious inputs detected. Review input validation rules."
            )

        if report["security_events"]["rate_limit_exceeded"] > 100:
            report["recommendations"].append(
                "High rate limit violations. Consider adjusting rate limits or implementing IP blocking."
            )

        # Sort top users and IPs
        report["top_users"] = dict(
            sorted(report["top_users"].items(), key=lambda x: x[1], reverse=True)[:10]
        )
        report["top_ips"] = dict(
            sorted(report["top_ips"].items(), key=lambda x: x[1], reverse=True)[:10]
        )

        return report


# Convenience functions
def log_security_event(
    event_type: AuditEventType,
    severity: AuditSeverity,
    user_id: Optional[str] = None,
    username: Optional[str] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
    resource: Optional[str] = None,
    action: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
    success: bool = True,
    error_message: Optional[str] = None,
):
    """Convenience function to log a security event"""
    import uuid

    event = AuditEvent(
        event_id=str(uuid.uuid4()),
        event_type=event_type,
        severity=severity,
        user_id=user_id,
        username=username,
        ip_address=ip_address,
        user_agent=user_agent,
        resource=resource,
        action=action,
        details=details or {},
        success=success,
        error_message=error_message,
    )

    # Get default audit logger
    global _default_audit_logger
    if "_default_audit_logger" not in globals():
        _default_audit_logger = AuditLogger(
            log_file="audit.log", database_file="audit.db", enable_console=True
        )

    _default_audit_logger.log_event(event)


def monitor_suspicious_activity(event: AuditEvent):
    """Convenience function to monitor suspicious activity"""
    global _default_security_monitor
    if "_default_security_monitor" not in globals():
        _default_security_monitor = SecurityMonitor(_default_audit_logger)

    return _default_security_monitor.monitor_suspicious_activity(event)


# Default instances
_default_audit_logger = AuditLogger(
    log_file="audit.log", database_file="audit.db", enable_console=True
)

_default_security_monitor = SecurityMonitor(_default_audit_logger)
