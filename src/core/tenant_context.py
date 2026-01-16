"""
Tenant Context Middleware for Multi-Tenant Support
Automatically extracts and validates tenant context from requests
"""

from typing import Optional, Callable
from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from datetime import datetime
import time

from ..models.tenant import Tenant, TenantStatus
from ..storage import DatabaseManager, TenantManager, UsageTracker


class TenantContext:
    """Holds tenant context for the current request"""
    
    def __init__(
        self,
        tenant_id: str,
        tenant: Optional[Tenant] = None,
    ):
        self.tenant_id = tenant_id
        self.tenant = tenant
        self.start_time = time.time()
    
    def is_active(self) -> bool:
        """Check if tenant is active"""
        return self.tenant and self.tenant.is_active()
    
    def can_make_request(self) -> bool:
        """Check if tenant can make requests"""
        return self.tenant and self.tenant.can_make_request()
    
    def get_execution_time_ms(self) -> float:
        """Get request execution time in milliseconds"""
        return (time.time() - self.start_time) * 1000


class TenantContextMiddleware(BaseHTTPMiddleware):
    """
    Middleware to extract and validate tenant context from requests
    
    Tenant identification can be done via:
    1. X-Tenant-ID header
    2. JWT token claim (tenant_id)
    3. API key mapping
    4. Subdomain (tenant.domain.com)
    """
    
    def __init__(
        self,
        app,
        db_manager: DatabaseManager,
        tenant_manager: TenantManager,
        usage_tracker: UsageTracker,
        default_tenant_id: str = "default",
        require_tenant: bool = False,
    ):
        super().__init__(app)
        self.db_manager = db_manager
        self.tenant_manager = tenant_manager
        self.usage_tracker = usage_tracker
        self.default_tenant_id = default_tenant_id
        self.require_tenant = require_tenant
    
    async def dispatch(self, request: Request, call_next: Callable):
        """Process request with tenant context"""
        
        # Extract tenant ID from request
        tenant_id = await self._extract_tenant_id(request)
        
        # If no tenant ID and required, reject request
        if not tenant_id and self.require_tenant:
            return HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Tenant identification required",
            )
        
        # Use default tenant if none specified
        if not tenant_id:
            tenant_id = self.default_tenant_id
        
        # Get tenant from database
        tenant = self.db_manager.get_tenant(tenant_id)
        
        # Validate tenant exists
        if not tenant and tenant_id != self.default_tenant_id:
            return HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Tenant '{tenant_id}' not found",
            )
        
        # Create tenant context
        tenant_context = TenantContext(tenant_id=tenant_id, tenant=tenant)
        
        # Validate tenant can make requests
        if tenant and not tenant_context.can_make_request():
            return HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Tenant is {tenant.status.value}",
            )
        
        # Check tenant limits before processing request
        if tenant:
            limits_check = self.tenant_manager.check_tenant_limits(tenant_id)
            if not limits_check.get("can_proceed", False):
                return HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=f"Tenant limit exceeded: {limits_check.get('exceeded', [])}",
                )
        
        # Attach tenant context to request state
        request.state.tenant_context = tenant_context
        request.state.tenant_id = tenant_id
        request.state.tenant = tenant
        
        # Process request
        try:
            response = await call_next(request)
            
            # Record usage after successful request
            if tenant:
                await self._record_usage(request, response, tenant_context, success=True)
            
            # Add tenant ID to response headers
            response.headers["X-Tenant-ID"] = tenant_id
            
            return response
            
        except Exception as e:
            # Record failed request
            if tenant:
                await self._record_usage(request, None, tenant_context, success=False)
            raise
    
    async def _extract_tenant_id(self, request: Request) -> Optional[str]:
        """
        Extract tenant ID from request using multiple methods
        Priority: Header > Token > Subdomain > Default
        """
        
        # Method 1: X-Tenant-ID header
        tenant_id = request.headers.get("X-Tenant-ID")
        if tenant_id:
            return tenant_id
        
        # Method 2: JWT token claim (if available)
        if hasattr(request.state, "token_data") and request.state.token_data:
            token_data = request.state.token_data
            if hasattr(token_data, "tenant_id"):
                return token_data.tenant_id
        
        # Method 3: API key mapping (would need API key lookup)
        api_key = request.headers.get("X-API-Key")
        if api_key:
            # TODO: Implement API key to tenant mapping
            pass
        
        # Method 4: Subdomain extraction
        host = request.headers.get("Host", "")
        if "." in host:
            subdomain = host.split(".")[0]
            # Check if subdomain is a valid tenant
            # For now, skip subdomain logic
            pass
        
        return None
    
    async def _record_usage(
        self,
        request: Request,
        response: Optional[object],
        tenant_context: TenantContext,
        success: bool,
    ):
        """Record usage for the request"""
        try:
            # Extract request info
            endpoint = str(request.url.path)
            method = request.method
            
            # Get execution time
            execution_time_ms = tenant_context.get_execution_time_ms()
            
            # TODO: Extract token counts from response if available
            tokens_used = 0
            input_tokens = 0
            output_tokens = 0
            
            # Record usage
            self.usage_tracker.record_request(
                tenant_id=tenant_context.tenant_id,
                tokens_used=tokens_used,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                success=success,
                execution_time_ms=execution_time_ms,
                endpoint=endpoint,
                operation_type=method,
            )
        except Exception as e:
            # Don't fail the request if usage recording fails
            print(f"Failed to record usage: {e}")


def get_tenant_context(request: Request) -> TenantContext:
    """
    Dependency to get tenant context from request
    Usage: tenant_context: TenantContext = Depends(get_tenant_context)
    """
    if not hasattr(request.state, "tenant_context"):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Tenant context not available",
        )
    return request.state.tenant_context


def get_tenant_id(request: Request) -> str:
    """
    Dependency to get tenant ID from request
    Usage: tenant_id: str = Depends(get_tenant_id)
    """
    if not hasattr(request.state, "tenant_id"):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Tenant context not available",
        )
    return request.state.tenant_id


def require_tenant(request: Request) -> Tenant:
    """
    Dependency to require tenant object
    Usage: tenant: Tenant = Depends(require_tenant)
    """
    if not hasattr(request.state, "tenant") or not request.state.tenant:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Valid tenant required",
        )
    return request.state.tenant
