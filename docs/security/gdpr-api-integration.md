# UK GDPR API Integration Guide

## Overview

This guide explains how to integrate the UK GDPR compliance endpoints into your application. These endpoints implement all user rights under UK GDPR and Data Protection Act 2018.

## Quick Start

### 1. Import GDPR Router

Add the GDPR router to your FastAPI application:

```python
from fastapi import FastAPI
from web.api_gdpr import router as gdpr_router

app = FastAPI()

# Include GDPR routes
app.include_router(gdpr_router)
```

### 2. Initialize GDPR Compliance Module

```python
from src.security import GDPRCompliance, AuditLogger

# Initialize audit logger
audit_logger = AuditLogger(
    log_file="audit.log",
    database_file="audit.db"
)

# Initialize GDPR compliance
gdpr_compliance = GDPRCompliance(
    database_manager=your_db_manager,
    audit_logger=audit_logger
)
```

## API Endpoints

All endpoints require authentication (JWT token or API key).

### Consent Management

#### Grant Consent

```bash
POST /gdpr/consent/grant
Authorization: Bearer {token}
Content-Type: application/json

{
  "purpose": "service_provision",
  "granted": true,
  "version": "1.0"
}
```

**Response:**
```json
{
  "success": true,
  "purpose": "service_provision",
  "granted": true,
  "timestamp": "2026-01-15T10:30:00Z",
  "message": "Consent granted for service_provision"
}
```

**Available Purposes:**
- `service_provision` - Core service delivery
- `system_improvement` - System optimization
- `analytics` - Usage analytics
- `marketing` - Marketing communications
- `third_party_sharing` - Data sharing with partners

#### Withdraw Consent

```bash
POST /gdpr/consent/withdraw
Authorization: Bearer {token}
Content-Type: application/json

{
  "purpose": "marketing",
  "granted": false
}
```

#### Check Consent Status

```bash
GET /gdpr/consent/status?purpose=marketing
Authorization: Bearer {token}
```

**Response:**
```json
{
  "user_id": "user123",
  "purpose": "marketing",
  "granted": false
}
```

#### Get Consent History

```bash
GET /gdpr/consent/history
Authorization: Bearer {token}
```

**Response:**
```json
{
  "user_id": "user123",
  "consents": [
    {
      "purpose": "service_provision",
      "granted": true,
      "timestamp": "2026-01-15T10:00:00Z",
      "version": "1.0",
      "method": "web"
    }
  ],
  "total_count": 1
}
```

### Right to Access (Article 15)

Request access to all personal data:

```bash
POST /gdpr/access
Authorization: Bearer {token}
Content-Type: application/json

{
  "format": "json"
}
```

**Response:**
```json
{
  "request_id": "access_user123_1705316400.0",
  "user_id": "user123",
  "status": "pending",
  "requested_at": "2026-01-15T10:00:00Z",
  "format": "json",
  "message": "Data access request created. Your data will be available within 30 days."
}
```

### Right to Data Portability (Article 20)

Export data immediately:

```bash
GET /gdpr/export?format=json
Authorization: Bearer {token}
```

**Response:** JSON or CSV file download containing:
- Account data
- Authentication data (excluding sensitive hashes)
- Usage data (queries, feedback)
- Consent records
- Audit logs

**Example JSON Response:**
```json
{
  "user_id": "user123",
  "export_date": "2026-01-15T10:00:00Z",
  "account_data": {
    "username": "user123",
    "email": "user@example.com",
    "role": "viewer",
    "created_at": "2024-01-01T00:00:00Z"
  },
  "consent_records": [...],
  "usage_data": {...}
}
```

### Right to Erasure (Article 17)

Request data deletion (30-day grace period):

```bash
POST /gdpr/delete
Authorization: Bearer {token}
Content-Type: application/json

{
  "reason": "No longer need the service",
  "confirm": true
}
```

**Response:**
```json
{
  "request_id": "delete_user123_1705316400.0",
  "user_id": "user123",
  "status": "grace_period",
  "scheduled_for": "2026-02-14T10:00:00Z",
  "grace_period_days": 30,
  "message": "Data deletion scheduled for 2026-02-14. You have 30 days to cancel..."
}
```

#### Cancel Deletion Request

```bash
POST /gdpr/delete/cancel?request_id=delete_user123_1705316400.0
Authorization: Bearer {token}
```

**Response:**
```json
{
  "success": true,
  "request_id": "delete_user123_1705316400.0",
  "message": "Data deletion request cancelled successfully"
}
```

### Right to Rectification (Article 16)

Update incorrect data:

```bash
POST /gdpr/rectify
Authorization: Bearer {token}
Content-Type: application/json

{
  "field": "email",
  "new_value": "newemail@example.com"
}
```

**Response:**
```json
{
  "success": true,
  "field": "email",
  "updated_at": "2026-01-15T10:00:00Z",
  "message": "Field 'email' updated successfully"
}
```

**Allowed Fields:**
- `email` - Email address
- `username` - Username

### Processing Activities

Get information about how data is processed:

```bash
GET /gdpr/processing-activities
Authorization: Bearer {token}
```

**Response:**
```json
{
  "user_id": "user123",
  "activities": [
    {
      "activity": "Service Delivery",
      "purpose": "Providing AI instruction services",
      "legal_basis": "Contract",
      "data_categories": ["Account data", "Usage data"],
      "recipients": ["Internal systems"],
      "retention": "While account is active"
    }
  ],
  "generated_at": "2026-01-15T10:00:00Z"
}
```

### Privacy Policy

Get current privacy policy information:

```bash
GET /gdpr/privacy-policy
```

**Response:**
```json
{
  "version": "1.0",
  "effective_date": "2026-01-15",
  "url": "/docs/security/privacy-policy.md",
  "last_updated": "2026-01-15"
}
```

### Compliance Information

Get UK GDPR compliance details:

```bash
GET /gdpr/compliance-info
```

**Response:**
```json
{
  "legislation": ["UK GDPR", "Data Protection Act 2018"],
  "data_controller": {
    "name": "Your Organization Name",
    "email": "privacy@example.com",
    "dpo_email": "dpo@example.com"
  },
  "user_rights": [...],
  "ico_contact": {...}
}
```

## Python SDK Example

```python
import requests

class GDPRClient:
    def __init__(self, base_url: str, token: str):
        self.base_url = base_url
        self.headers = {"Authorization": f"Bearer {token}"}
    
    def grant_consent(self, purpose: str, version: str = "1.0"):
        """Grant consent for a purpose"""
        response = requests.post(
            f"{self.base_url}/gdpr/consent/grant",
            headers=self.headers,
            json={
                "purpose": purpose,
                "granted": True,
                "version": version
            }
        )
        return response.json()
    
    def export_data(self, format: str = "json"):
        """Export all user data"""
        response = requests.get(
            f"{self.base_url}/gdpr/export",
            headers=self.headers,
            params={"format": format}
        )
        if format == "json":
            return response.json()
        return response.text
    
    def request_deletion(self, reason: str = None):
        """Request data deletion"""
        response = requests.post(
            f"{self.base_url}/gdpr/delete",
            headers=self.headers,
            json={
                "reason": reason,
                "confirm": True
            }
        )
        return response.json()
    
    def rectify_data(self, field: str, new_value: str):
        """Update incorrect data"""
        response = requests.post(
            f"{self.base_url}/gdpr/rectify",
            headers=self.headers,
            json={
                "field": field,
                "new_value": new_value
            }
        )
        return response.json()

# Usage
client = GDPRClient("http://localhost:8000", "your-jwt-token")

# Grant consent
consent = client.grant_consent("analytics")
print(f"Consent granted: {consent['success']}")

# Export data
data = client.export_data()
print(f"Exported {len(data)} bytes of data")

# Request deletion
deletion = client.request_deletion("No longer need service")
print(f"Deletion scheduled for: {deletion['scheduled_for']}")
```

## JavaScript/TypeScript Example

```typescript
class GDPRClient {
  constructor(
    private baseUrl: string,
    private token: string
  ) {}

  private async request(
    method: string,
    endpoint: string,
    body?: any
  ): Promise<any> {
    const response = await fetch(`${this.baseUrl}${endpoint}`, {
      method,
      headers: {
        'Authorization': `Bearer ${this.token}`,
        'Content-Type': 'application/json',
      },
      body: body ? JSON.stringify(body) : undefined,
    });
    return response.json();
  }

  async grantConsent(purpose: string, version: string = '1.0') {
    return this.request('POST', '/gdpr/consent/grant', {
      purpose,
      granted: true,
      version,
    });
  }

  async exportData(format: 'json' | 'csv' = 'json') {
    const response = await fetch(
      `${this.baseUrl}/gdpr/export?format=${format}`,
      {
        headers: {
          'Authorization': `Bearer ${this.token}`,
        },
      }
    );
    
    if (format === 'json') {
      return response.json();
    }
    return response.text();
  }

  async requestDeletion(reason?: string) {
    return this.request('POST', '/gdpr/delete', {
      reason,
      confirm: true,
    });
  }

  async rectifyData(field: string, newValue: string) {
    return this.request('POST', '/gdpr/rectify', {
      field,
      new_value: newValue,
    });
  }
}

// Usage
const client = new GDPRClient('http://localhost:8000', 'your-jwt-token');

// Grant consent
const consent = await client.grantConsent('analytics');
console.log('Consent granted:', consent.success);

// Export data
const data = await client.exportData();
console.log('Exported data:', data);

// Request deletion
const deletion = await client.requestDeletion('No longer need service');
console.log('Deletion scheduled:', deletion.scheduled_for);
```

## Error Handling

All endpoints return standard HTTP status codes:

- `200 OK` - Success
- `400 Bad Request` - Invalid request data
- `401 Unauthorized` - Missing or invalid authentication
- `403 Forbidden` - Insufficient permissions
- `404 Not Found` - Resource not found
- `500 Internal Server Error` - Server error

**Error Response Format:**
```json
{
  "error": "error_code",
  "message": "Human-readable error message",
  "details": {}
}
```

## Best Practices

### 1. Always Verify Identity

Before processing any user rights request:
- Verify the user's identity
- Use strong authentication
- Log the verification attempt

### 2. Respond Within 30 Days

UK GDPR requires response within one month:
- Track request timestamps
- Set up reminders
- Communicate delays if needed

### 3. Provide Clear Information

When responding to requests:
- Use plain language
- Explain what data is included
- Note any exceptions or retentions

### 4. Document Everything

Maintain records of:
- All requests received
- Actions taken
- Responses provided
- Any exceptions applied

### 5. Test Regularly

- Test all endpoints periodically
- Verify data export completeness
- Ensure deletion works correctly
- Check consent tracking accuracy

## Integration Checklist

- [ ] Import GDPR router into main application
- [ ] Initialize GDPRCompliance with database manager
- [ ] Set up audit logging
- [ ] Configure authentication
- [ ] Test all endpoints
- [ ] Update privacy policy with endpoint URLs
- [ ] Train staff on handling requests
- [ ] Set up monitoring and alerts
- [ ] Document integration for team
- [ ] Plan regular compliance reviews

## Support

For questions or issues:
- **Technical Support**: support@example.com
- **Privacy Questions**: privacy@example.com
- **Data Protection Officer**: dpo@example.com
- **Documentation**: See `/docs/security/gdpr-quick-start.md`

## Further Reading

- [UK GDPR Full Documentation](docs/security/gdpr-quick-start.md)
- [Privacy Policy](privacy-policy.md)
- [Security Guide](security.md)
- [Staff Training Guide](docs/training/uk-gdpr-staff-training.md)
