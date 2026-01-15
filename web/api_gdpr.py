"""
UK GDPR Compliance API Endpoints

Provides API endpoints for user rights under UK GDPR:
- Right to Access (Article 15)
- Right to Erasure (Article 17)
- Right to Data Portability (Article 20)
- Right to Rectification (Article 16)
- Consent Management
"""

from fastapi import APIRouter, HTTPException, Depends, Response, status, Request
from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime

from src.security import (
    User,
    get_current_user,
    GDPRCompliance,
    ConsentPurpose,
    DataExportFormat,
)

# Create router
router = APIRouter(prefix="/gdpr", tags=["GDPR Compliance"])

# Initialize GDPR compliance module (would be passed from main app)
gdpr_compliance = GDPRCompliance()


# Pydantic models for requests/responses
class ConsentRequest(BaseModel):
    """Request to grant or withdraw consent"""

    purpose: ConsentPurpose
    granted: bool
    version: str = Field(default="1.0", description="Privacy policy version")


class ConsentResponse(BaseModel):
    """Response for consent operations"""

    success: bool
    purpose: str
    granted: bool
    timestamp: str
    message: str


class DataAccessRequestModel(BaseModel):
    """Request for data access"""

    format: DataExportFormat = Field(
        default=DataExportFormat.JSON, description="Export format (json or csv)"
    )


class DataAccessResponse(BaseModel):
    """Response for data access request"""

    request_id: str
    user_id: str
    status: str
    requested_at: str
    format: str
    message: str


class DataDeletionRequestModel(BaseModel):
    """Request for data deletion"""

    reason: Optional[str] = Field(
        None, description="Reason for deletion (optional)"
    )
    confirm: bool = Field(
        ..., description="Confirmation that user understands consequences"
    )

    @validator("confirm")
    def confirm_must_be_true(cls, v):
        if not v:
            raise ValueError("User must confirm data deletion")
        return v


class DataDeletionResponse(BaseModel):
    """Response for data deletion request"""

    request_id: str
    user_id: str
    status: str
    scheduled_for: str
    grace_period_days: int = 30
    message: str


class DataRectificationRequest(BaseModel):
    """Request to rectify user data"""

    field: str = Field(..., description="Field to update (email, username)")
    new_value: str = Field(..., description="New value for the field")


class DataRectificationResponse(BaseModel):
    """Response for data rectification"""

    success: bool
    field: str
    updated_at: str
    message: str


class ConsentHistoryResponse(BaseModel):
    """Response for consent history"""

    user_id: str
    consents: List[Dict[str, Any]]
    total_count: int


class ProcessingActivitiesResponse(BaseModel):
    """Response for processing activities"""

    user_id: str
    activities: List[Dict[str, Any]]
    generated_at: str


# Endpoints


@router.post("/consent/grant", response_model=ConsentResponse)
async def grant_consent(
    consent_request: ConsentRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
):
    """
    Grant or update consent for specific data processing purpose

    Implements consent requirements under UK GDPR Article 6(1)(a)
    """
    try:
        # Get request metadata
        ip_address = request.client.host if request.client else None
        user_agent = request.headers.get("user-agent")

        # Record consent
        consent = gdpr_compliance.grant_consent(
            user_id=current_user.id,
            purpose=consent_request.purpose,
            version=consent_request.version,
            method="api",
            ip_address=ip_address,
            user_agent=user_agent,
        )

        return ConsentResponse(
            success=True,
            purpose=consent.purpose.value,
            granted=consent.granted,
            timestamp=consent.timestamp.isoformat(),
            message=f"Consent granted for {consent.purpose.value}",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to record consent: {str(e)}",
        )


@router.post("/consent/withdraw", response_model=ConsentResponse)
async def withdraw_consent(
    consent_request: ConsentRequest,
    current_user: User = Depends(get_current_user),
):
    """
    Withdraw consent for specific data processing purpose

    Implements right to withdraw consent under UK GDPR Article 7(3)
    """
    try:
        consent = gdpr_compliance.withdraw_consent(
            user_id=current_user.id, purpose=consent_request.purpose
        )

        return ConsentResponse(
            success=True,
            purpose=consent.purpose.value,
            granted=consent.granted,
            timestamp=consent.timestamp.isoformat(),
            message=f"Consent withdrawn for {consent.purpose.value}",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to withdraw consent: {str(e)}",
        )


@router.get("/consent/status")
async def get_consent_status(
    purpose: Optional[ConsentPurpose] = None,
    current_user: User = Depends(get_current_user),
):
    """
    Get current consent status for specific purpose or all purposes
    """
    try:
        if purpose:
            # Check specific purpose
            status_value = gdpr_compliance.check_consent(current_user.id, purpose)
            return {
                "user_id": current_user.id,
                "purpose": purpose.value,
                "granted": status_value,
            }
        else:
            # Get all consent statuses
            history = gdpr_compliance.get_consent_history(current_user.id)
            # Get latest consent for each purpose
            latest_consents = {}
            for consent in history:
                purpose_key = consent["purpose"]
                if (
                    purpose_key not in latest_consents
                    or consent["timestamp"] > latest_consents[purpose_key]["timestamp"]
                ):
                    latest_consents[purpose_key] = consent

            return {
                "user_id": current_user.id,
                "consents": list(latest_consents.values()),
            }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get consent status: {str(e)}",
        )


@router.get("/consent/history", response_model=ConsentHistoryResponse)
async def get_consent_history_endpoint(
    current_user: User = Depends(get_current_user),
):
    """
    Get complete consent history for the user

    Shows all consent grants and withdrawals over time
    """
    try:
        history = gdpr_compliance.get_consent_history(current_user.id)

        return ConsentHistoryResponse(
            user_id=current_user.id, consents=history, total_count=len(history)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get consent history: {str(e)}",
        )


@router.post("/access", response_model=DataAccessResponse)
async def request_data_access(
    access_request: DataAccessRequestModel,
    current_user: User = Depends(get_current_user),
):
    """
    Request access to all personal data (Right to Access - Article 15)

    Creates a data access request that will be processed within 30 days
    as required by UK GDPR.
    """
    try:
        request = gdpr_compliance.request_data_access(
            user_id=current_user.id, format=access_request.format
        )

        return DataAccessResponse(
            request_id=request.request_id,
            user_id=current_user.id,
            status=request.status,
            requested_at=request.requested_at.isoformat(),
            format=request.format.value,
            message="Data access request created. Your data will be available within 30 days.",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create data access request: {str(e)}",
        )


@router.get("/export")
async def export_user_data(
    format: DataExportFormat = DataExportFormat.JSON,
    current_user: User = Depends(get_current_user),
):
    """
    Export user data immediately (Right to Data Portability - Article 20)

    Returns all personal data in machine-readable format (JSON or CSV)
    """
    try:
        exported_data = gdpr_compliance.export_user_data(
            user_id=current_user.id, format=format
        )

        if format == DataExportFormat.JSON:
            return Response(
                content=exported_data,
                media_type="application/json",
                headers={
                    "Content-Disposition": f"attachment; filename=user_data_{current_user.id}.json"
                },
            )
        else:  # CSV
            return Response(
                content=exported_data,
                media_type="text/csv",
                headers={
                    "Content-Disposition": f"attachment; filename=user_data_{current_user.id}.csv"
                },
            )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to export user data: {str(e)}",
        )


@router.post("/delete", response_model=DataDeletionResponse)
async def request_data_deletion(
    deletion_request: DataDeletionRequestModel,
    current_user: User = Depends(get_current_user),
):
    """
    Request deletion of all personal data (Right to Erasure - Article 17)

    Implements 30-day grace period before permanent deletion.
    Data can be recovered during this period.
    """
    try:
        request = gdpr_compliance.request_data_deletion(
            user_id=current_user.id, reason=deletion_request.reason
        )

        return DataDeletionResponse(
            request_id=request.request_id,
            user_id=current_user.id,
            status=request.status,
            scheduled_for=request.scheduled_for.isoformat(),
            grace_period_days=30,
            message=(
                f"Data deletion scheduled for {request.scheduled_for.date()}. "
                "You have 30 days to cancel this request if needed. "
                "After this period, your data will be permanently deleted."
            ),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to request data deletion: {str(e)}",
        )


@router.post("/delete/cancel")
async def cancel_data_deletion(
    request_id: str, current_user: User = Depends(get_current_user)
):
    """
    Cancel a pending data deletion request (during grace period)
    """
    try:
        success = gdpr_compliance.cancel_deletion_request(request_id)

        if success:
            return {
                "success": True,
                "request_id": request_id,
                "message": "Data deletion request cancelled successfully",
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Deletion request not found or already processed",
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to cancel deletion request: {str(e)}",
        )


@router.post("/rectify", response_model=DataRectificationResponse)
async def rectify_user_data(
    rectification_request: DataRectificationRequest,
    current_user: User = Depends(get_current_user),
):
    """
    Update incorrect or incomplete personal data (Right to Rectification - Article 16)

    Allowed fields: email, username
    """
    try:
        result = gdpr_compliance.rectify_user_data(
            user_id=current_user.id,
            field=rectification_request.field,
            new_value=rectification_request.new_value,
        )

        if result.get("success"):
            return DataRectificationResponse(
                success=True,
                field=result["field"],
                updated_at=result["updated_at"],
                message=f"Field '{result['field']}' updated successfully",
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail=result.get("error")
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to rectify data: {str(e)}",
        )


@router.get("/processing-activities", response_model=ProcessingActivitiesResponse)
async def get_processing_activities(current_user: User = Depends(get_current_user)):
    """
    Get list of data processing activities for user data

    Provides transparency about how personal data is being processed
    """
    try:
        activities = gdpr_compliance.get_processing_activities(current_user.id)

        return ProcessingActivitiesResponse(
            user_id=current_user.id,
            activities=activities,
            generated_at=datetime.utcnow().isoformat(),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get processing activities: {str(e)}",
        )


@router.get("/privacy-policy")
async def get_privacy_policy():
    """
    Get the current privacy policy

    Returns link to privacy policy document
    """
    return {
        "version": "1.0",
        "effective_date": "2026-01-15",
        "url": "/docs/PRIVACY_POLICY.md",
        "last_updated": "2026-01-15",
    }


@router.get("/compliance-info")
async def get_compliance_info():
    """
    Get UK GDPR compliance information

    Provides information about data protection measures and user rights
    """
    return {
        "legislation": ["UK GDPR", "Data Protection Act 2018"],
        "data_controller": {
            "name": "Your Organization Name",
            "email": "privacy@example.com",
            "dpo_email": "dpo@example.com",
        },
        "user_rights": [
            {
                "right": "Right to Access",
                "article": "Article 15",
                "endpoint": "/gdpr/access",
            },
            {
                "right": "Right to Rectification",
                "article": "Article 16",
                "endpoint": "/gdpr/rectify",
            },
            {
                "right": "Right to Erasure",
                "article": "Article 17",
                "endpoint": "/gdpr/delete",
            },
            {
                "right": "Right to Data Portability",
                "article": "Article 20",
                "endpoint": "/gdpr/export",
            },
        ],
        "ico_contact": {
            "website": "https://ico.org.uk",
            "helpline": "0303 123 1113",
            "address": "Wycliffe House, Water Lane, Wilmslow, Cheshire SK9 5AF",
        },
        "documentation": {
            "privacy_policy": "/docs/PRIVACY_POLICY.md",
            "compliance_guide": "/docs/uk-gdpr-compliance.md",
        },
    }
