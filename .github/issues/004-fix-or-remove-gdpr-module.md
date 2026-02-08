# SECURITY: Fix or remove incomplete GDPR compliance module

**Labels:** `security`, `compliance`, `priority-1`

## Summary

`src/security/gdpr.py` claims to provide UK GDPR compliance but has **7 TODO comments** admitting critical functionality is unimplemented:

```
Line 336: # TODO: Replace with actual database query in production
Line 355: # TODO: Replace with actual database query in production
Line 368: # TODO: Replace with actual database query in production
Line 385: # TODO: Replace with actual audit log query in production
Line 558: # TODO: Implement in production with actual database manager
Line 569: # TODO: Implement in production with actual database manager
Line 577: # TODO: Implement in production with actual audit logger
```

The data export, data deletion, and audit trail features — the three most critical GDPR rights — are all stubbed. The module gives the **appearance** of compliance without the substance.

## Why this is worse than having no GDPR module

- A half-implemented compliance module creates a false sense of security
- If an auditor or data subject exercises their rights (SAR, right to erasure), the system will silently fail or return incomplete data
- Having a GDPR module that doesn't actually work is arguably worse than having none, because it implies compliance that doesn't exist
- Legal liability: representing GDPR compliance when the implementation is incomplete

## Proposed Fix — Pick One

### Option A: Remove it (recommended if not needed yet)
1. Delete `src/security/gdpr.py`
2. Remove all GDPR references from `web/api_secure.py` and other consumers
3. Add a note to README: "GDPR compliance module planned for future release"
4. Re-implement properly when there's an actual database backend

### Option B: Finish it (if compliance is a requirement)
1. Implement all 7 TODO items with real database queries via SQLAlchemy models
2. Add integration tests with a test database that verify:
   - Subject Access Requests return all stored personal data
   - Right to Erasure actually deletes data (not just marks it)
   - Audit log queries return real audit trail
3. Add data retention policies with automated cleanup
4. Have a compliance review before claiming GDPR readiness

## Files

- `src/security/gdpr.py` (lines 336, 355, 368, 385, 558, 569, 577)
- `web/api_secure.py` (GDPR endpoint consumers)
