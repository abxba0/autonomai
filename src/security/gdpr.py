"""
UK GDPR Compliance Module

Implements user rights under UK GDPR including:
- Right to Access (Article 15)
- Right to Erasure (Article 17)
- Right to Data Portability (Article 20)
- Right to Rectification (Article 16)
- Consent Management
- Data Retention Policies
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from enum import Enum
import json
import csv
import io
from dataclasses import dataclass, field, asdict

# Default retention period for GDPR data (7 years for audit compliance)
GDPR_AUDIT_RETENTION_DAYS = 365 * 7
# Default retention for completed requests
GDPR_REQUEST_RETENTION_DAYS = 90


class ConsentPurpose(str, Enum):
    """Types of consent purposes"""

    SERVICE_PROVISION = "service_provision"
    SYSTEM_IMPROVEMENT = "system_improvement"
    ANALYTICS = "analytics"
    MARKETING = "marketing"
    THIRD_PARTY_SHARING = "third_party_sharing"


class DataExportFormat(str, Enum):
    """Supported export formats"""

    JSON = "json"
    CSV = "csv"


@dataclass
class ConsentRecord:
    """Record of user consent"""

    user_id: str
    purpose: ConsentPurpose
    granted: bool
    timestamp: datetime = field(default_factory=datetime.utcnow)
    version: str = "1.0"  # Privacy policy version
    method: str = "web"  # How consent was given
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        data = asdict(self)
        data["timestamp"] = self.timestamp.isoformat()
        data["purpose"] = self.purpose.value
        return data


@dataclass
class DataAccessRequest:
    """Request for data access"""

    request_id: str
    user_id: str
    requested_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    status: str = "pending"  # pending, completed, failed
    format: DataExportFormat = DataExportFormat.JSON

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "request_id": self.request_id,
            "user_id": self.user_id,
            "requested_at": self.requested_at.isoformat(),
            "completed_at": self.completed_at.isoformat()
            if self.completed_at
            else None,
            "status": self.status,
            "format": self.format.value,
        }


@dataclass
class DataDeletionRequest:
    """Request for data deletion"""

    request_id: str
    user_id: str
    requested_at: datetime = field(default_factory=datetime.utcnow)
    scheduled_for: datetime = field(
        default_factory=lambda: datetime.utcnow() + timedelta(days=30)
    )
    completed_at: Optional[datetime] = None
    status: str = "pending"  # pending, grace_period, completed, cancelled
    reason: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "request_id": self.request_id,
            "user_id": self.user_id,
            "requested_at": self.requested_at.isoformat(),
            "scheduled_for": self.scheduled_for.isoformat(),
            "completed_at": self.completed_at.isoformat()
            if self.completed_at
            else None,
            "status": self.status,
            "reason": self.reason,
        }


class GDPRCompliance:
    """
    Handles UK GDPR compliance operations including user rights and consent management
    """

    def __init__(self, database_manager=None, audit_logger=None):
        """
        Initialize GDPR compliance module

        Args:
            database_manager: Database manager for data operations
            audit_logger: Audit logger for compliance tracking
        """
        self.db = database_manager
        self.audit_logger = audit_logger
        self.consent_records: Dict[str, List[ConsentRecord]] = {}
        self.access_requests: Dict[str, DataAccessRequest] = {}
        self.deletion_requests: Dict[str, DataDeletionRequest] = {}

    def _log_audit_event(
        self,
        event_type: str,
        user_id: str,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Log an audit event, adapting to the AuditLogger interface."""
        if not self.audit_logger:
            return

        # Import here to avoid circular imports at module level
        try:
            from src.security.audit import AuditEvent, AuditEventType, AuditSeverity
            import uuid

            # Map GDPR event types to AuditEventType or use SECURITY_ALERT as default
            type_map = {
                "consent_granted": AuditEventType.CONFIGURATION_CHANGED,
                "consent_withdrawn": AuditEventType.CONFIGURATION_CHANGED,
                "data_access_requested": AuditEventType.QUERY_EXECUTED,
                "data_deletion_requested": AuditEventType.USER_DELETED,
                "data_deletion_cancelled": AuditEventType.USER_UPDATED,
                "data_deletion_completed": AuditEventType.USER_DELETED,
                "data_deletion_failed": AuditEventType.SECURITY_ALERT,
                "data_rectified": AuditEventType.USER_UPDATED,
                "gdpr_retention_cleanup": AuditEventType.CONFIGURATION_CHANGED,
            }
            audit_event_type = type_map.get(
                event_type, AuditEventType.SECURITY_ALERT
            )

            event = AuditEvent(
                event_id=str(uuid.uuid4()),
                event_type=audit_event_type,
                severity=AuditSeverity.INFO,
                user_id=user_id,
                resource="gdpr",
                action=event_type,
                details=details or {},
            )
            self.audit_logger.log_event(event)
        except (ImportError, Exception):
            # Fallback: try calling with keyword args for duck-typed loggers
            try:
                self.audit_logger.log_event(
                    event_type=event_type,
                    user_id=user_id,
                    details=details or {},
                )
            except Exception:
                pass

    def grant_consent(
        self,
        user_id: str,
        purpose: ConsentPurpose,
        version: str = "1.0",
        method: str = "web",
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> ConsentRecord:
        """
        Record user consent for specific purpose

        Args:
            user_id: User identifier
            purpose: Purpose of data processing
            version: Privacy policy version
            method: Method of consent (web, api, etc.)
            ip_address: User's IP address
            user_agent: User's browser/client

        Returns:
            ConsentRecord: Record of the consent
        """
        consent = ConsentRecord(
            user_id=user_id,
            purpose=purpose,
            granted=True,
            timestamp=datetime.utcnow(),
            version=version,
            method=method,
            ip_address=ip_address,
            user_agent=user_agent,
        )

        # Persist to database if available
        if self.db:
            self.db.save_consent_record(
                user_id=user_id,
                purpose=purpose.value,
                granted=True,
                timestamp=consent.timestamp,
                version=version,
                method=method,
                ip_address=ip_address,
                user_agent=user_agent,
            )
        else:
            # Fallback to in-memory storage
            if user_id not in self.consent_records:
                self.consent_records[user_id] = []
            self.consent_records[user_id].append(consent)

        self._log_audit_event(
            event_type="consent_granted",
            user_id=user_id,
            details={
                "purpose": purpose.value,
                "version": version,
                "method": method,
            },
        )

        return consent

    def withdraw_consent(
        self, user_id: str, purpose: ConsentPurpose
    ) -> ConsentRecord:
        """
        Record withdrawal of user consent

        Args:
            user_id: User identifier
            purpose: Purpose to withdraw consent for

        Returns:
            ConsentRecord: Record of the withdrawal
        """
        consent = ConsentRecord(
            user_id=user_id,
            purpose=purpose,
            granted=False,
            timestamp=datetime.utcnow(),
        )

        # Persist to database if available
        if self.db:
            self.db.save_consent_record(
                user_id=user_id,
                purpose=purpose.value,
                granted=False,
                timestamp=consent.timestamp,
            )
        else:
            if user_id not in self.consent_records:
                self.consent_records[user_id] = []
            self.consent_records[user_id].append(consent)

        self._log_audit_event(
            event_type="consent_withdrawn",
            user_id=user_id,
            details={"purpose": purpose.value},
        )

        return consent

    def check_consent(self, user_id: str, purpose: ConsentPurpose) -> bool:
        """
        Check if user has granted consent for specific purpose

        Args:
            user_id: User identifier
            purpose: Purpose to check

        Returns:
            bool: True if consent is granted and current
        """
        # Check database first if available
        if self.db:
            record = self.db.get_latest_consent(user_id, purpose.value)
            if record:
                return record["granted"]
            return False

        # Fallback to in-memory
        if user_id not in self.consent_records:
            return False

        relevant_consents = [
            c for c in self.consent_records[user_id] if c.purpose == purpose
        ]

        if not relevant_consents:
            return False

        latest_consent = max(relevant_consents, key=lambda x: x.timestamp)
        return latest_consent.granted

    def get_consent_history(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Get complete consent history for user

        Args:
            user_id: User identifier

        Returns:
            List of consent records
        """
        # Use database if available
        if self.db:
            return self.db.get_consent_records(user_id)

        # Fallback to in-memory
        if user_id not in self.consent_records:
            return []

        return [c.to_dict() for c in self.consent_records[user_id]]

    def request_data_access(
        self, user_id: str, format: DataExportFormat = DataExportFormat.JSON
    ) -> DataAccessRequest:
        """
        Create data access request (Right to Access - Article 15)

        Args:
            user_id: User identifier
            format: Export format (JSON or CSV)

        Returns:
            DataAccessRequest: Request record
        """
        request_id = f"access_{user_id}_{datetime.utcnow().timestamp()}"

        request = DataAccessRequest(
            request_id=request_id, user_id=user_id, format=format, status="pending"
        )

        # Persist to database if available
        if self.db:
            self.db.save_data_access_request(
                request_id=request_id,
                user_id=user_id,
                format=format.value,
            )

        self.access_requests[request_id] = request

        self._log_audit_event(
            event_type="data_access_requested",
            user_id=user_id,
            details={"request_id": request_id, "format": format.value},
        )

        return request

    def export_user_data(
        self, user_id: str, format: DataExportFormat = DataExportFormat.JSON
    ) -> str:
        """
        Export all user data (Right to Data Portability - Article 20)

        Args:
            user_id: User identifier
            format: Export format

        Returns:
            str: Exported data in requested format
        """
        # Collect all user data
        user_data = self._collect_user_data(user_id)

        if format == DataExportFormat.JSON:
            return json.dumps(user_data, indent=2, default=str)
        elif format == DataExportFormat.CSV:
            return self._convert_to_csv(user_data)
        else:
            raise ValueError(f"Unsupported export format: {format}")

    def _collect_user_data(self, user_id: str) -> Dict[str, Any]:
        """
        Collect all personal data for a user

        Args:
            user_id: User identifier

        Returns:
            Dictionary containing all user data
        """
        data = {
            "user_id": user_id,
            "export_date": datetime.utcnow().isoformat(),
            "account_data": {},
            "authentication_data": {},
            "usage_data": {},
            "consent_records": [],
            "audit_logs": [],
        }

        # Account data from database
        if self.db:
            user_data = self.db.get_user_personal_data(user_id)
            if user_data:
                data["account_data"] = {
                    "username": user_data.get("username"),
                    "email": user_data.get("email"),
                    "role": user_data.get("role"),
                    "created_at": user_data.get("created_at"),
                    "last_login": user_data.get("last_login"),
                    "is_active": user_data.get("is_active"),
                }
            else:
                data["account_data"] = {}
        else:
            data["account_data"] = {
                "username": f"user_{user_id}",
                "email": f"user_{user_id}@example.com",
                "role": "viewer",
                "created_at": "2024-01-01T00:00:00Z",
                "last_login": datetime.utcnow().isoformat(),
                "is_active": True,
                "note": "This is placeholder data. Configure database manager for real data.",
            }

        # Authentication data (excluding sensitive hashes)
        if self.db:
            user_data = self.db.get_user_personal_data(user_id)
            data["authentication_data"] = {
                "api_keys": [],  # API key metadata only, never actual keys
                "last_login": user_data.get("last_login") if user_data else None,
            }
        else:
            data["authentication_data"] = {
                "api_keys": [],
                "session_count": 0,
                "login_history": [],
                "note": "This is placeholder data. Configure database manager for real data.",
            }

        # Usage data from database
        if self.db:
            usage_records = self.db.get_user_usage_data(user_id)
            data["usage_data"] = {
                "total_queries": len(usage_records),
                "queries": usage_records,
            }
        else:
            data["usage_data"] = {
                "total_queries": 0,
                "queries": [],
                "feedback_provided": [],
                "system_interactions": [],
                "note": "This is placeholder data. Configure database manager for real data.",
            }

        # Consent records (from database or in-memory)
        data["consent_records"] = self.get_consent_history(user_id)

        # Audit logs related to this user
        if self.audit_logger:
            data["audit_logs"] = self.audit_logger.get_user_logs(user_id)
        else:
            data["audit_logs"] = []

        return data

    def _convert_to_csv(self, data: Dict[str, Any]) -> str:
        """
        Convert user data to CSV format

        Args:
            data: User data dictionary

        Returns:
            str: CSV formatted data
        """
        output = io.StringIO()
        writer = csv.writer(output)

        # Write account data
        writer.writerow(["Account Data"])
        writer.writerow(["Field", "Value"])
        for key, value in data.get("account_data", {}).items():
            writer.writerow([key, str(value)])
        writer.writerow([])

        # Write consent records
        writer.writerow(["Consent Records"])
        if data.get("consent_records"):
            writer.writerow(["Purpose", "Granted", "Timestamp", "Version"])
            for record in data["consent_records"]:
                writer.writerow(
                    [
                        record.get("purpose"),
                        record.get("granted"),
                        record.get("timestamp"),
                        record.get("version"),
                    ]
                )
        writer.writerow([])

        return output.getvalue()

    def request_data_deletion(
        self, user_id: str, reason: Optional[str] = None
    ) -> DataDeletionRequest:
        """
        Create data deletion request (Right to Erasure - Article 17)

        Implements 30-day grace period before permanent deletion

        Args:
            user_id: User identifier
            reason: Reason for deletion request

        Returns:
            DataDeletionRequest: Request record
        """
        request_id = f"delete_{user_id}_{datetime.utcnow().timestamp()}"

        request = DataDeletionRequest(
            request_id=request_id,
            user_id=user_id,
            status="grace_period",
            reason=reason,
        )

        # Persist to database if available
        if self.db:
            self.db.save_data_deletion_request(
                request_id=request_id,
                user_id=user_id,
                scheduled_for=request.scheduled_for,
                reason=reason,
            )

        self.deletion_requests[request_id] = request

        self._log_audit_event(
            event_type="data_deletion_requested",
            user_id=user_id,
            details={"request_id": request_id, "reason": reason},
        )

        return request

    def cancel_deletion_request(self, request_id: str) -> bool:
        """
        Cancel a pending deletion request (during grace period)

        Args:
            request_id: Deletion request ID

        Returns:
            bool: True if cancelled successfully
        """
        if request_id not in self.deletion_requests:
            return False

        request = self.deletion_requests[request_id]

        if request.status != "grace_period":
            return False

        request.status = "cancelled"

        self._log_audit_event(
            event_type="data_deletion_cancelled",
            user_id=request.user_id,
            details={"request_id": request_id},
        )

        return True

    def execute_data_deletion(self, request_id: str) -> bool:
        """
        Execute data deletion after grace period

        Args:
            request_id: Deletion request ID

        Returns:
            bool: True if deletion successful
        """
        if request_id not in self.deletion_requests:
            return False

        request = self.deletion_requests[request_id]

        if request.status != "grace_period":
            return False

        # Check if grace period has elapsed
        if datetime.utcnow() < request.scheduled_for:
            return False

        # Perform deletion
        success = self._delete_user_data(request.user_id)

        if success:
            request.status = "completed"
            request.completed_at = datetime.utcnow()

            # Log deletion with anonymized user reference
            self._log_audit_event(
                event_type="data_deletion_completed",
                user_id=f"deleted_{request.user_id[:8]}",
                details={"request_id": request_id},
            )

        return success

    def _delete_user_data(self, user_id: str) -> bool:
        """
        Delete all user personal data

        Implements soft delete followed by hard delete
        Retains anonymized audit logs for legal compliance

        Args:
            user_id: User identifier

        Returns:
            bool: True if deletion successful
        """
        try:
            # 1. Deactivate account in database
            if self.db:
                self.db.deactivate_user(user_id)

            # 2. Delete personal data from all tables
            if self.db:
                self.db.delete_user_personal_data(user_id)

            # 3. Anonymize audit logs (keep for legal compliance - 7 years)
            # Do NOT delete audit logs - anonymize them instead
            if self.audit_logger:
                self.audit_logger.anonymize_user_logs(user_id)

            # 4. Remove from in-memory consent records
            if user_id in self.consent_records:
                del self.consent_records[user_id]

            # 5. Remove from in-memory access request records
            for request_id in list(self.access_requests.keys()):
                if self.access_requests[request_id].user_id == user_id:
                    del self.access_requests[request_id]

            # Keep deletion request records for audit purposes (in-memory)
            for request_id in list(self.deletion_requests.keys()):
                if self.deletion_requests[request_id].user_id == user_id:
                    pass

            return True
        except Exception as e:
            self._log_audit_event(
                event_type="data_deletion_failed",
                user_id=user_id,
                details={"error": str(e)},
            )
            return False

    def rectify_user_data(
        self, user_id: str, field: str, new_value: str
    ) -> Dict[str, Any]:
        """
        Update incorrect or incomplete user data (Right to Rectification - Article 16)

        Args:
            user_id: User identifier
            field: Field to update (email, username, etc.)
            new_value: New value

        Returns:
            Dictionary with update result
        """
        allowed_fields = ["email", "username"]

        if field not in allowed_fields:
            return {
                "success": False,
                "error": f"Field '{field}' cannot be rectified directly",
            }

        # Perform update in database
        success = True
        if self.db:
            success = self.db.update_user_personal_field(user_id, field, new_value)

        self._log_audit_event(
            event_type="data_rectified",
            user_id=user_id,
            details={"field": field, "new_value": new_value},
        )

        return {
            "success": success,
            "field": field,
            "updated_at": datetime.utcnow().isoformat(),
        }

    def get_processing_activities(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Get list of processing activities for user data

        Args:
            user_id: User identifier

        Returns:
            List of processing activities
        """
        activities = [
            {
                "activity": "Service Delivery",
                "purpose": "Providing AI instruction services",
                "legal_basis": "Contract",
                "data_categories": ["Account data", "Usage data"],
                "recipients": ["Internal systems"],
                "retention": "While account is active",
            },
            {
                "activity": "System Improvement",
                "purpose": "Learning from failures to optimize",
                "legal_basis": "Legitimate Interest",
                "data_categories": ["Usage data", "Feedback"],
                "recipients": ["Internal systems"],
                "retention": "90 days",
            },
            {
                "activity": "Security Monitoring",
                "purpose": "Protecting account and system",
                "legal_basis": "Legitimate Interest",
                "data_categories": ["Authentication data", "IP addresses"],
                "recipients": ["Internal security systems"],
                "retention": "12 months",
            },
            {
                "activity": "AI Model Processing",
                "purpose": "Generating responses to queries",
                "legal_basis": "Contract",
                "data_categories": ["Queries", "Context"],
                "recipients": ["Third-party AI providers"],
                "retention": "0-30 days (provider dependent)",
            },
        ]

        return activities

    def run_data_retention_cleanup(
        self, retention_days: int = GDPR_REQUEST_RETENTION_DAYS
    ) -> Dict[str, Any]:
        """
        Run automated data retention cleanup.

        Removes completed access/deletion requests older than the retention period.
        Processes any pending deletion requests that have passed their grace period.

        Args:
            retention_days: Number of days to retain completed request data

        Returns:
            Dictionary with cleanup results
        """
        results = {
            "timestamp": datetime.utcnow().isoformat(),
            "retention_days": retention_days,
            "deletions_executed": 0,
            "requests_cleaned": {},
        }

        # Process pending deletion requests past grace period
        if self.db:
            pending = self.db.get_pending_deletion_requests()
            for req in pending:
                request_id = req["request_id"]
                # If the request is also tracked in-memory, execute from there
                if request_id in self.deletion_requests:
                    self.deletion_requests[request_id].status = "grace_period"
                    success = self.execute_data_deletion(request_id)
                else:
                    # Execute directly from database state
                    success = self._delete_user_data(req["user_id"])
                    if success:
                        self.db.update_data_deletion_request(request_id, "completed")
                if success:
                    results["deletions_executed"] += 1

            # Clean up old completed requests
            results["requests_cleaned"] = self.db.cleanup_expired_gdpr_data(
                retention_days=retention_days
            )

        self._log_audit_event(
            event_type="gdpr_retention_cleanup",
            user_id="system",
            details=results,
        )

        return results
