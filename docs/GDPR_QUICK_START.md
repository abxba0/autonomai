# UK GDPR Compliance - Quick Start Guide

## For End Users

### Your Rights Under UK GDPR

As a user of this system, you have the following rights regarding your personal data:

#### 1. Right to Know What Data We Have (Right to Access)

**What it means:** You can request a copy of all your personal data.

**How to do it:**
- **Via API:** Send a request to `/gdpr/export`
- **Via Support:** Email dpo@example.com
- **Response time:** Within 30 days
- **Format:** JSON or CSV download

**Example request:**
```bash
curl -X GET "https://api.example.com/gdpr/export?format=json" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

#### 2. Right to Correct Your Data (Right to Rectification)

**What it means:** You can update incorrect or incomplete information.

**How to do it:**
- **Via API:** Send a request to `/gdpr/rectify`
- **Via Profile:** Update your profile settings
- **Via Support:** Email dpo@example.com

**Example request:**
```bash
curl -X POST "https://api.example.com/gdpr/rectify" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"field": "email", "new_value": "newemail@example.com"}'
```

#### 3. Right to Delete Your Data (Right to Erasure/"Right to be Forgotten")

**What it means:** You can request deletion of your personal data.

**Important:** 
- 30-day grace period before permanent deletion
- You can cancel during this period
- Some data (anonymized audit logs) kept for legal reasons

**How to do it:**
- **Via API:** Send a request to `/gdpr/delete`
- **Via Account Settings:** Use delete account option
- **Via Support:** Email dpo@example.com

**Example request:**
```bash
curl -X POST "https://api.example.com/gdpr/delete" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"reason": "No longer need service", "confirm": true}'
```

#### 4. Right to Download Your Data (Right to Data Portability)

**What it means:** Get your data in a format you can transfer to another service.

**How to do it:**
- **Via API:** Same as Right to Access (`/gdpr/export`)
- **Format:** JSON (computer-readable) or CSV (spreadsheet)

#### 5. Right to Control How We Use Your Data

**What it means:** You can:
- See what data processing you've consented to
- Withdraw consent at any time
- Object to processing based on our legitimate interests

**How to do it:**
- **Via API:** `/gdpr/consent/status` and `/gdpr/consent/withdraw`
- **Via Settings:** Manage your consent preferences
- **Via Support:** Email dpo@example.com

### Quick FAQs

**Q: How long does it take to get my data?**
A: We have 30 days to respond, but usually much faster via the API.

**Q: What if I accidentally request deletion?**
A: You have 30 days to cancel the deletion request.

**Q: Will you really delete all my data?**
A: Yes, except for anonymized audit logs we're legally required to keep for 7 years.

**Q: Is there a cost?**
A: No, your first request is free. Repeat requests may have reasonable fees.

**Q: Can I complain to someone?**
A: Yes! Contact the Information Commissioner's Office (ICO):
- Website: https://ico.org.uk
- Phone: 0303 123 1113

---

## For Developers

### Quick Integration (5 minutes)

#### 1. Install

```bash
pip install -r requirements.txt
pip install -e ".[web]"
```

#### 2. Import

```python
from fastapi import FastAPI
from web.api_gdpr import router as gdpr_router

app = FastAPI()
app.include_router(gdpr_router)
```

#### 3. Initialize

```python
from src.security import GDPRCompliance, AuditLogger

audit_logger = AuditLogger(log_file="audit.log")
gdpr = GDPRCompliance(audit_logger=audit_logger)
```

#### 4. Use

```python
# Check consent before processing
if gdpr.check_consent(user_id, ConsentPurpose.ANALYTICS):
    # Process analytics
    pass

# Export user data
data = gdpr.export_user_data(user_id, DataExportFormat.JSON)
```

#### 5. Test

```bash
# Run example server
python examples/gdpr_compliant_api.py

# Visit http://localhost:8000/docs
```

### Available Endpoints

- `POST /gdpr/consent/grant` - Grant consent
- `POST /gdpr/consent/withdraw` - Withdraw consent  
- `GET /gdpr/consent/status` - Check consent
- `POST /gdpr/access` - Request data access
- `GET /gdpr/export` - Export data immediately
- `POST /gdpr/delete` - Request deletion
- `POST /gdpr/rectify` - Correct data
- `GET /gdpr/processing-activities` - Get processing info
- `GET /gdpr/privacy-policy` - Get privacy policy
- `GET /gdpr/compliance-info` - Get compliance details

### Documentation

- **Full API Docs:** [`docs/gdpr-api-integration.md`](gdpr-api-integration.md)
- **Compliance Guide:** [`docs/uk-gdpr-compliance.md`](uk-gdpr-compliance.md)
- **Privacy Policy:** [`docs/PRIVACY_POLICY.md`](PRIVACY_POLICY.md)
- **Implementation Checklist:** [`docs/uk-gdpr-compliance-checklist.md`](uk-gdpr-compliance-checklist.md)

---

## For System Administrators

### Deployment Checklist (30 minutes)

#### 1. Pre-Flight

- [ ] Review [`docs/uk-gdpr-compliance-checklist.md`](uk-gdpr-compliance-checklist.md)
- [ ] Update organization details in all docs
- [ ] Generate strong SECRET_KEY
- [ ] Configure database (PostgreSQL recommended for production)

#### 2. Security

- [ ] Enable HTTPS/TLS
- [ ] Configure CORS with specific origins
- [ ] Set up rate limiting
- [ ] Enable audit logging to persistent storage
- [ ] Configure backup encryption

#### 3. Data Protection

- [ ] Review and set retention periods
- [ ] Configure automated deletion tasks
- [ ] Set up audit log rotation
- [ ] Test data export functionality
- [ ] Verify deletion works correctly

#### 4. Third-Party

- [ ] Sign Data Processing Agreements with AI providers:
  - [ ] Anthropic
  - [ ] OpenAI
  - [ ] Google
  - [ ] Deepseek (additional due diligence)
  - [ ] Openrouter
- [ ] Document international transfer safeguards
- [ ] Configure provider opt-out options

#### 5. Operations

- [ ] Train staff (use [`docs/training/uk-gdpr-staff-training.md`](training/uk-gdpr-staff-training.md))
- [ ] Set up monitoring dashboard
- [ ] Configure response time tracking
- [ ] Test breach notification procedures
- [ ] Schedule regular compliance reviews

#### 6. Legal

- [ ] Appoint Data Protection Officer (if required)
- [ ] Register with ICO (if required)
- [ ] Complete Data Protection Impact Assessment
- [ ] Update privacy policy with final details
- [ ] Inform existing users of their rights

### Monitoring

Key metrics to track:
- GDPR request response times (must be < 30 days)
- Number of requests by type
- Consent grant/withdrawal trends
- Data deletion requests
- Audit log completeness

### Emergency Contacts

- **Data Protection Officer:** dpo@example.com
- **Security Team:** security@example.com
- **ICO Helpline:** 0303 123 1113

---

## Support & Resources

### Documentation
- [UK GDPR Compliance Guide](uk-gdpr-compliance.md) - Complete compliance documentation
- [API Integration Guide](gdpr-api-integration.md) - Developer integration guide
- [Privacy Policy](PRIVACY_POLICY.md) - User-facing privacy policy
- [Staff Training Guide](training/uk-gdpr-staff-training.md) - Training materials
- [Compliance Checklist](uk-gdpr-compliance-checklist.md) - Implementation checklist

### External Resources
- [ICO Guide to UK GDPR](https://ico.org.uk/for-organisations/guide-to-data-protection/)
- [UK GDPR Text](https://www.legislation.gov.uk/uksi/2019/419/contents)
- [Data Protection Act 2018](https://www.legislation.gov.uk/ukpga/2018/12/contents)

### Getting Help

**For Users:**
- Data requests: dpo@example.com
- Privacy questions: privacy@example.com
- Support: support@example.com

**For Developers:**
- Technical documentation: `/docs/`
- API reference: `/docs` (when server running)
- Example code: `/examples/gdpr_compliant_api.py`

**For Organizations:**
- Compliance questions: dpo@example.com
- Legal questions: legal@example.com
- ICO guidance: 0303 123 1113

---

## Version Information

- **UK GDPR Implementation Version:** 1.0
- **Last Updated:** 2026-01-15
- **Next Review:** 2026-07-15
- **Status:** Production Ready ✅

## What's Included

✅ All 8 UK GDPR user rights  
✅ Consent management system  
✅ Data export (JSON & CSV)  
✅ 30-day deletion grace period  
✅ Comprehensive audit logging  
✅ Privacy by design  
✅ Complete documentation  
✅ Integration examples  
✅ Staff training materials  
✅ Deployment checklist  

## Next Steps

1. **Users:** Exercise your rights via the API or contact dpo@example.com
2. **Developers:** Review [`docs/gdpr-api-integration.md`](gdpr-api-integration.md) and integrate
3. **Administrators:** Complete [`docs/uk-gdpr-compliance-checklist.md`](uk-gdpr-compliance-checklist.md)
4. **Organizations:** Customize documents and conduct staff training

---

**Questions?** Contact dpo@example.com or visit https://ico.org.uk for ICO guidance.
