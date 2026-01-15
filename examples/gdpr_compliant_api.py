"""
Example: Integrating UK GDPR endpoints into the existing secure API

This example shows how to add GDPR compliance endpoints to an existing
FastAPI application with authentication.
"""

from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src import SelfOptimizingSystem, SystemConfig
from src.security import (
    User,
    get_current_user,
    GDPRCompliance,
    AuditLogger,
)

# Import GDPR router
from web.api_gdpr import router as gdpr_router

# Create FastAPI app
app = FastAPI(
    title="Self-Optimizing System with UK GDPR Compliance",
    description="AI system with full UK GDPR compliance",
    version="2.0.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:8000"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Initialize system
system = SelfOptimizingSystem()

# Initialize GDPR compliance
audit_logger = AuditLogger(
    log_file="audit.log",
    database_file="audit.db",
    enable_console=True,
)

gdpr_compliance = GDPRCompliance(
    database_manager=None,  # Would be your actual DB manager
    audit_logger=audit_logger,
)

# Include GDPR router
app.include_router(gdpr_router)


# Example protected endpoint
@app.post("/execute")
async def execute_query(
    query: str,
    current_user: User = Depends(get_current_user),
):
    """
    Execute a query with GDPR compliance checks
    """
    # Check consent for system improvement
    has_consent = gdpr_compliance.check_consent(
        current_user.id,
        "system_improvement"  # Would be ConsentPurpose enum
    )
    
    # Execute query
    result = system.execute(query)
    
    # Log to audit
    audit_logger.log_event(
        event_type="query_executed",
        user_id=current_user.id,
        details={
            "query": query,
            "has_improvement_consent": has_consent,
        },
    )
    
    return {
        "output": result.get("output"),
        "validation_passed": result.get("validation_passed"),
        "user_id": current_user.id,
    }


@app.get("/")
async def root():
    """Root endpoint with compliance information"""
    return {
        "message": "Self-Optimizing System API",
        "version": "2.0.0",
        "compliance": {
            "uk_gdpr": "compliant",
            "data_protection_act_2018": "compliant",
        },
        "documentation": {
            "api_docs": "/docs",
            "privacy_policy": "/gdpr/privacy-policy",
            "compliance_info": "/gdpr/compliance-info",
            "gdpr_endpoints": "/gdpr/*",
        },
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "gdpr_module": "active",
        "audit_logging": "active",
    }


# Example: Custom endpoint with data minimization
@app.get("/profile")
async def get_profile(current_user: User = Depends(get_current_user)):
    """
    Get user profile with data minimization
    
    Only returns necessary data, following GDPR principle of data minimization
    """
    return {
        "username": current_user.username,
        "email": current_user.email,
        "role": current_user.role,
        # Note: We don't return sensitive data like password hashes
        # Note: We don't return API keys
        "data_rights": {
            "access": "/gdpr/access",
            "export": "/gdpr/export",
            "delete": "/gdpr/delete",
            "rectify": "/gdpr/rectify",
        },
    }


# Example: Endpoint with consent check
@app.post("/analytics")
async def submit_analytics(
    event: str,
    current_user: User = Depends(get_current_user),
):
    """
    Submit analytics event - requires consent
    
    Demonstrates checking consent before processing optional data
    """
    from src.security import ConsentPurpose
    
    # Check if user has consented to analytics
    has_consent = gdpr_compliance.check_consent(
        current_user.id,
        ConsentPurpose.ANALYTICS
    )
    
    if not has_consent:
        return {
            "success": False,
            "message": "Analytics consent required",
            "consent_endpoint": "/gdpr/consent/grant",
        }
    
    # Process analytics if consent given
    # ... analytics processing ...
    
    return {
        "success": True,
        "message": "Analytics event recorded",
    }


if __name__ == "__main__":
    import uvicorn
    
    print("=" * 60)
    print("Starting Self-Optimizing System with UK GDPR Compliance")
    print("=" * 60)
    print()
    print("API Documentation: http://localhost:8000/docs")
    print("Privacy Policy: http://localhost:8000/gdpr/privacy-policy")
    print("Compliance Info: http://localhost:8000/gdpr/compliance-info")
    print()
    print("GDPR Endpoints:")
    print("  - /gdpr/consent/* - Consent management")
    print("  - /gdpr/access - Request data access")
    print("  - /gdpr/export - Export user data")
    print("  - /gdpr/delete - Request data deletion")
    print("  - /gdpr/rectify - Correct user data")
    print()
    print("=" * 60)
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info",
    )
