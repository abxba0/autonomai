# System Instructions

Generated: 2026-01-12T17:18:59.357768
Current Version: v20260111_125715

---

# System Instructions

Generated: 2026-01-12T17:17:57.812340
Current Version: v20260111_125715

---

# System Instructions

Generated: 2026-01-12T17:16:46.600949
Current Version: v20260111_125715

---

## Failure Log

### Recent Failures (Full Detail)

### Failure #20260112_171859 [AUTO_VALIDATION] - 2026-01-12T17:18:59.357717 - Severity: MODERATE
**Signature**: `8aaa02c723e6`
**Description**: Validation failed: GroundingValidator
**Validation Errors**: {
  "GroundingValidator": {
    "message": "Found 2 hallucinated value(s): status, result",
    "details": {
      "hallucinations": [
        {
          "field": "status",
          "value": "success",
          "reason": "Text value not found in source"
        },
        {
          "field": "result",
          "value": "Mock JSON response",
          "reason": "Text value not found in source"
        }
      ],
      "verified_fields": [],
      "total_fields": 2
    }
  }
}
**Last Output**: 
```
{"status": "success", "result": "Mock JSON response"}
```
**User Query**: 
Extract the following information from the document and return it as JSON:
- invoice_number
- date
- customer_name
- customer_email
- customer_phone
- item_name
- item_price
- quantity
- shipping
- tax
- total_amount
- payment_method
- tracking_number
- order_status

Document:

INVOICE #4582-2024
Date: March 15th, 2024

Customer Info:
Name: John Smith
Email: j.smith@example.com
Phone: (555) 123-4567

Order Details:
- Widget Pro Model X: $249.99 (qty: 2)
- Shipping & Handling: $15.50
- Tax (8.5%): $43.82
TOTAL: $559.30

Payment Method: Credit Card ending in 8742
Order Status: SHIPPED on 03/18/2024
Tracking: TRK-9384756ABC

Notes: Customer requested gift wrapping (+$5.00)
Delivery address verified. Expected delivery: March 22, 2024


Return ONLY valid JSON with the extracted data. Do not include any explanatory text.


---



---

## Version History

See `.versions/` directory for full history.
Latest version: v20260111_125715

