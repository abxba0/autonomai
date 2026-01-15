# Privacy Policy

**Effective Date:** 15 January 2026  
**Last Updated:** 15 January 2026  
**Version:** 1.0

## Introduction

This Privacy Policy explains how the Self-Optimizing Instruction Library ("we", "our", or "the System") collects, uses, stores, and protects your personal data in compliance with the UK General Data Protection Regulation (UK GDPR) and the Data Protection Act 2018.

By using our service, you agree to the collection and use of information in accordance with this policy.

## Who We Are

**Data Controller**: [Your Organization Name]  
**Contact Email**: privacy@example.com  
**Data Protection Officer**: dpo@example.com  
**Address**: [Your Address]

For questions about this Privacy Policy or your personal data, please contact our Data Protection Officer.

## What Data We Collect

### 1. Account Information
When you register for an account, we collect:
- **Username**: Your chosen username for the system
- **Email Address**: For account verification and important communications
- **Password**: Stored as a secure hash (we never store plain text passwords)
- **Account Role**: Your access level (Admin, Editor, Viewer, or API Client)
- **Account Creation Date**: When you created your account
- **Last Login Date**: When you last accessed the system

### 2. Authentication Data
To keep your account secure, we collect:
- **API Keys**: For programmatic access (stored as secure hashes)
- **Session Tokens**: Temporary tokens for maintaining your login session
- **Login History**: Records of successful and failed login attempts

### 3. Usage Data
To provide and improve our service, we collect:
- **Queries**: The questions and requests you submit to the system
- **Responses**: The AI-generated responses provided to you
- **Feedback**: Corrections and feedback you provide to improve the system
- **Conversation Context**: Historical conversation data to provide context-aware responses
- **System Interactions**: Your use of system features and functionality

### 4. Technical Data
For security and system optimization, we collect:
- **IP Address**: Your internet protocol address
- **User Agent**: Information about your browser or application
- **Request Timestamps**: When you interact with the system
- **Performance Metrics**: System response times and error rates

### 5. Security Data
To protect your account and our system, we collect:
- **Security Events**: Failed login attempts, suspicious activities
- **Audit Logs**: Records of data access and system changes
- **Rate Limiting Data**: To prevent abuse of the service

## How We Use Your Data

### Legal Basis for Processing

We process your personal data under the following legal bases:

1. **Contract (Article 6(1)(b))**: To provide our service to you
2. **Consent (Article 6(1)(a))**: Where you have given explicit consent
3. **Legitimate Interests (Article 6(1)(f))**: For security, fraud prevention, and system improvement
4. **Legal Obligation (Article 6(1)(c))**: To comply with legal requirements

### Purposes of Processing

We use your personal data for:

1. **Service Delivery**
   - Providing access to the self-optimizing AI system
   - Generating responses to your queries
   - Maintaining your account and preferences
   - Communicating important service updates

2. **System Improvement**
   - Learning from failures to optimize instructions
   - Improving response quality based on feedback
   - Developing new features and capabilities
   - Conducting research and analytics

3. **Security & Fraud Prevention**
   - Protecting your account from unauthorized access
   - Detecting and preventing system abuse
   - Monitoring for security threats
   - Investigating security incidents

4. **Legal Compliance**
   - Meeting regulatory requirements
   - Responding to legal requests
   - Maintaining audit trails
   - Enforcing our terms of service

5. **Customer Support**
   - Responding to your inquiries
   - Troubleshooting technical issues
   - Providing assistance and guidance

## Third-Party Data Sharing

### AI Model Providers

To provide AI services, we share your queries with third-party AI providers:

| Provider | Purpose | Location | Data Shared |
|----------|---------|----------|-------------|
| Anthropic Claude | AI Model Inference | USA | Queries, context |
| OpenAI GPT | AI Model Inference | USA | Queries, context |
| Google Gemini | AI Model Inference | Global | Queries, context |
| Deepseek | AI Model Inference | China | Queries, context |
| Openrouter | AI Model Routing | Varies | Queries, context |

**Your Control**: You can opt out of specific providers through system configuration.

**Data Processing Agreements**: We maintain data processing agreements with all providers.

**Retention**: Each provider has their own data retention policy (typically 0-30 days for API data).

### International Data Transfers

Some of our AI providers are located outside the UK. We ensure adequate protection through:
- Standard Contractual Clauses (UK SCCs)
- Data Processing Agreements
- Additional security measures where required
- Adequacy assessments for data protection

### Other Third Parties

We do not sell, rent, or trade your personal data with any other third parties. We may share data with:
- **Legal Authorities**: When required by law or to protect rights
- **Service Providers**: For hosting and infrastructure (with data processing agreements)
- **Professional Advisors**: Lawyers, accountants (under confidentiality obligations)

## How Long We Keep Your Data

We retain personal data only as long as necessary:

| Data Type | Retention Period | Reason |
|-----------|-----------------|--------|
| Active Accounts | While account is active | Service provision |
| Inactive Accounts | 24 months | Re-engagement opportunity |
| Audit Logs | 7 years | Legal requirement |
| Query History | 90 days | System optimization |
| Session Data | 30 days | Security |
| Backup Data | 30 days | Disaster recovery |

After these periods, data is either deleted or anonymized so it can no longer identify you.

## Your Rights Under UK GDPR

You have the following rights regarding your personal data:

### 1. Right to Access (Article 15)
You can request a copy of all personal data we hold about you.

**How to exercise**: Contact dpo@example.com or use the `/gdpr/access` API endpoint.

**Response time**: Within 30 days (free of charge for the first request).

### 2. Right to Rectification (Article 16)
You can request correction of inaccurate or incomplete data.

**How to exercise**: Update your profile or contact dpo@example.com.

**Response time**: Within 30 days.

### 3. Right to Erasure (Article 17)
You can request deletion of your personal data ("right to be forgotten").

**How to exercise**: Contact dpo@example.com or use the `/gdpr/delete` API endpoint.

**Response time**: Within 30 days.

**Exceptions**: We may retain data where legally required (e.g., audit logs for 7 years).

### 4. Right to Restrict Processing (Article 18)
You can request that we stop processing your data while disputes are resolved.

**How to exercise**: Contact dpo@example.com.

### 5. Right to Data Portability (Article 20)
You can receive your data in a machine-readable format and transfer it to another service.

**How to exercise**: Use the `/gdpr/export` API endpoint or contact dpo@example.com.

**Format**: JSON or CSV.

### 6. Right to Object (Article 21)
You can object to processing based on legitimate interests.

**How to exercise**: Contact dpo@example.com or use system settings.

### 7. Right to Withdraw Consent
Where processing is based on consent, you can withdraw it at any time.

**How to exercise**: Use the consent management endpoints or contact dpo@example.com.

### 8. Right to Lodge a Complaint
You can complain to the Information Commissioner's Office (ICO):

**ICO Contact**:
- Website: https://ico.org.uk
- Helpline: 0303 123 1113
- Address: Wycliffe House, Water Lane, Wilmslow, Cheshire SK9 5AF

## Data Security

We implement appropriate technical and organizational measures to protect your personal data:

### Technical Measures
- **Encryption**: TLS 1.3 for data in transit, AES-256 for backups
- **Hashing**: Secure password and API key hashing (bcrypt/argon2)
- **Access Controls**: Role-based access with least privilege principle
- **Authentication**: Strong password requirements, optional MFA
- **Monitoring**: 24/7 security monitoring and anomaly detection
- **Rate Limiting**: Protection against brute force and abuse

### Organizational Measures
- **Staff Training**: Regular data protection training for all staff
- **Access Reviews**: Regular review of who has access to personal data
- **Policies**: Comprehensive data protection and security policies
- **Audits**: Regular internal and external security audits
- **Incident Response**: Documented breach notification procedures

### Data Breach Notification

In the event of a data breach that affects your rights:
- We will notify the ICO within 72 hours of discovery
- We will notify you without undue delay if there is a high risk to your rights
- We will provide information about the breach and steps we're taking

## Cookies and Tracking

We use cookies and similar technologies for:

### Essential Cookies
- **Session Management**: To keep you logged in
- **Security**: To protect against attacks
- **Functionality**: To remember your preferences

These cookies are necessary for the service and cannot be disabled.

### Optional Cookies
- **Analytics**: To understand how the system is used (with your consent)
- **Performance**: To optimize system performance

You can control optional cookies through your browser settings.

## Children's Privacy

Our service is not intended for children under 13. We do not knowingly collect personal data from children. If you believe we have collected data from a child, please contact us immediately at dpo@example.com.

## Automated Decision-Making

Our system uses AI models to generate responses to your queries. While these responses are generated automatically:
- You are not subject to solely automated decisions with legal or significant effects
- You can always request human review of any decision
- You can provide feedback to improve future responses

## Changes to This Policy

We may update this Privacy Policy from time to time. We will:
- Notify you of significant changes via email or system notification
- Post the updated policy with a new "Last Updated" date
- Maintain an archive of previous versions

Your continued use of the service after changes constitutes acceptance of the updated policy.

## Data Protection Officer

For any questions about this policy or your personal data:

**Data Protection Officer**  
Email: dpo@example.com  
Address: [Your Address]

We aim to respond to all inquiries within 7 business days.

## Contact Us

If you have questions about this Privacy Policy:

- **Email**: privacy@example.com
- **Data Protection Officer**: dpo@example.com
- **Support**: support@example.com
- **Website**: [Your Website]

## Legal Information

This Privacy Policy is governed by UK law and complies with:
- UK General Data Protection Regulation (UK GDPR)
- Data Protection Act 2018
- Privacy and Electronic Communications Regulations (PECR)

---

**Document Version**: 1.0  
**Effective Date**: 15 January 2026  
**Next Review**: 15 July 2026
