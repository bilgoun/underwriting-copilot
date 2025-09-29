# Bank Data Submission Guide
## Softmax Underwriting Copilot Integration

### Overview

This guide provides comprehensive instructions for Mongolian banks to integrate with the Softmax Underwriting Copilot API. The system provides automated loan underwriting analysis, credit memo generation, and risk assessment for consumer and collateral-backed loans.

---

## Quick Start

### 1. Authentication Setup

Your bank has been assigned unique credentials:

**For TDB (Trade and Development Bank):**
- API Key: `L8v82V-xS2lfZdSdztDgXdXBWqksp0liUTM3wDu237k`
- Tenant Secret: `BdB7adCijqySvhglFFYcaLAkpwsONRoRmdBJresEL3A`

**For TBF (TenGer Financial Group):**
- API Key: `BO43M365zFp7lc8LIcJAyN1KBBk07Q8vedQbi5WDPDg`
- Tenant Secret: `9mNlCWO2DUdJPXAMjKBXSuGk0NPHdIkDvCl_LhCMinQ`

### 2. API Endpoint

**Production Endpoint:** `https://uw-api.softmax.mn/v1/underwrite`

### 3. Integration Pattern

```
Bank System → Submit Loan Application → Softmax API → Background Processing → Webhook Callback
```

---

## Data Submission Process

### Step 1: Prepare Bank Statement PDF

**Requirements:**
- Upload bank statement PDF to your secure file storage
- Generate a time-limited signed URL (recommended: 1-hour expiration)
- Ensure PDF is accessible via HTTPS

**Supported Banks:**
- Golomt Bank
- Khan Bank
- State Bank of Mongolia
- TDB Bank
- Xac Bank

### Step 2: Submit Loan Application

**HTTP Request:**
```http
POST https://uw-api.softmax.mn/v1/underwrite
Content-Type: application/json
X-Api-Key: YOUR_API_KEY
X-Signature: HMAC_SIGNATURE
```

### Step 3: Monitor Job Status

**Check Status:**
```http
GET https://uw-api.softmax.mn/v1/jobs/{job_id}
X-Api-Key: YOUR_API_KEY
```

---

## Request Format

### Complete JSON Payload Example

```json
{
  "job_id": "TDB-2025-0001",
  "tenant_id": "TDB",
  "applicant": {
    "citizen_id": "УН98042314",
    "full_name": "Батбаяр Доржийн",
    "phone": "+976-99123456"
  },
  "loan": {
    "type": "consumer_loan",
    "amount": 50000000,
    "term_months": 36
  },
  "documents": {
    "bank_statement_url": "https://your-secure-storage.com/statements/signed-url?expires=1234567890",
    "bank_statement_period": {
      "from": "2024-01-01T00:00:00Z",
      "to": "2024-12-31T23:59:59Z"
    }
  },
  "consent_artifact": {
    "provider": "TDB_CONSENT_SYSTEM",
    "reference": "CONSENT-TDB-2025-001",
    "scopes": ["credit_check", "bank_statement", "collateral_evaluation"],
    "issued_at": "2024-12-31T10:00:00Z",
    "expires_at": "2025-12-31T10:00:00Z",
    "hash": "sha256:abc123def456..."
  },
  "collateral": {
    "type": "Vehicle",
    "plateNo": "УНН-1234",
    "brand": "Toyota",
    "model": "Prius",
    "yearMade": 2020,
    "declared_value": 25000000
  },
  "third_party_data": {
    "mongolbank_credit": {
      "score": 662,
      "status": "fair",
      "open_accounts": 3,
      "total_debt_mnt": 5785000
    },
    "social_security": {
      "employment_status": "active",
      "current_employer": "ТАВАН БОГД ФИНАНС ББСБ",
      "monthly_salary": 4200000,
      "employment_duration_months": 18
    }
  },
  "callback_url": "https://your-bank.mn/webhooks/underwriting-result"
}
```

### Required Fields

| Field | Type | Description |
|-------|------|-------------|
| `job_id` | string | Your internal loan application ID |
| `tenant_id` | string | Your bank code (TDB or TBF) |
| `applicant` | object | Borrower information |
| `loan` | object | Loan request details |
| `documents.bank_statement_url` | URL | Secure PDF download link |
| `consent_artifact` | object | Customer consent record |
| `collateral` | object | Collateral details (if applicable) |
| `third_party_data` | object | Credit bureau & social insurance data |
| `callback_url` | URL | Your webhook endpoint |

---

## HMAC Signature Authentication

### Signature Generation (Python Example)

```python
import json
import hmac
import hashlib
import base64
import requests

def create_signature(payload, tenant_secret):
    # Convert payload to JSON bytes
    body = json.dumps(payload, separators=(',', ':'), ensure_ascii=False).encode()

    # Create HMAC-SHA256 signature
    signature = base64.b64encode(
        hmac.new(tenant_secret.encode(), body, hashlib.sha256).digest()
    ).decode()

    return signature, body

# Usage
payload = {...}  # Your loan application data
signature, body = create_signature(payload, "YOUR_TENANT_SECRET")

response = requests.post(
    'https://uw-api.softmax.mn/v1/underwrite',
    data=body,
    headers={
        'X-Api-Key': 'YOUR_API_KEY',
        'X-Signature': signature,
        'Content-Type': 'application/json'
    }
)
```

### Signature Generation (JavaScript Example)

```javascript
const crypto = require('crypto');
const axios = require('axios');

function createSignature(payload, tenantSecret) {
    const body = JSON.stringify(payload);
    const signature = crypto
        .createHmac('sha256', tenantSecret)
        .update(body)
        .digest('base64');
    return { signature, body };
}

// Usage
const payload = {...};  // Your loan application data
const { signature, body } = createSignature(payload, 'YOUR_TENANT_SECRET');

const response = await axios.post('https://uw-api.softmax.mn/v1/underwrite', body, {
    headers: {
        'X-Api-Key': 'YOUR_API_KEY',
        'X-Signature': signature,
        'Content-Type': 'application/json'
    }
});
```

---

## Response Format

### Immediate Response (202 Accepted)

```json
{
  "job_id": "uwo_1234567890abcdef",
  "status": "queued"
}
```

### Job Status Response

```json
{
  "job_id": "uwo_1234567890abcdef",
  "status": "completed",
  "client_job_id": "TDB-2025-0001",
  "decision": "APPROVE",
  "risk_score": 0.25,
  "interest_rate_suggestion": 12.5,
  "memo_markdown": "# Credit Analysis Report\n\n## Executive Summary\n\n**Borrower:** Батбаяр Доржийн\n**Loan Amount:** ₮50,000,000\n**Recommendation:** **APPROVE**\n\n## Income Analysis\n\n**Bank Statement Summary:**\n- Average Monthly Income: ₮4,200,000\n- Transaction Volume: 2,384 transactions\n- Income Stability: High (coefficient of variation: 0.15)\n\n**Social Insurance Verification:**\n- Current Employer: ТАВАН БОГД ФИНАНС ББСБ\n- Employment Duration: 18 months\n- Salary Verification: ₮4,200,000 monthly\n\n## Credit Risk Assessment\n\n**Credit Bureau Analysis:**\n- Credit Score: 662 (Fair)\n- Open Accounts: 3\n- Total Outstanding Debt: ₮5,785,000\n- Payment History: 1 late payment (< 30 days) in last 12 months\n\n**Debt-to-Income Ratio:** 13.8% (Excellent)\n\n## Collateral Evaluation\n\n**Vehicle Details:**\n- 2020 Toyota Prius\n- Estimated Market Value: ₮28,500,000\n- Loan-to-Value Ratio: 87.7% (Acceptable)\n\n## Risk Factors\n\n**Positive Factors:**\n- Stable employment (18+ months)\n- Strong income-to-loan ratio (1:12)\n- Low debt burden\n- Valuable collateral\n\n**Risk Considerations:**\n- Recent credit inquiry (within 6 months)\n- Vehicle depreciation risk\n\n## Final Recommendation\n\n**APPROVE** with suggested interest rate of **12.5%** APR.\n\n**Risk Score:** Low (0.25/1.00)\n\n**Recommended Terms:**\n- Principal: ₮50,000,000\n- Term: 36 months\n- Monthly Payment: ₮1,756,000\n- Interest Rate: 12.5% APR\n\n*Generated by Softmax Underwriting Copilot*",
  "memo_pdf_url": "https://softmax-reports.s3.amazonaws.com/reports/TDB-2025-0001.pdf"
}
```

### Status Values

| Status | Description |
|--------|-------------|
| `queued` | Job accepted and waiting to process |
| `processing` | Analyzing documents and data |
| `completed` | Analysis finished successfully |
| `failed` | Processing failed (check error details) |

---

## Webhook Integration

### Webhook Payload

When analysis completes, we'll POST to your `callback_url`:

```json
{
  "job_id": "uwo_1234567890abcdef",
  "client_job_id": "TDB-2025-0001",
  "status": "completed",
  "decision": "APPROVE",
  "risk_score": 0.25,
  "interest_rate_suggestion": 12.5,
  "timestamp": "2025-09-26T14:30:00Z",
  "processing_time_seconds": 45
}
```

### Webhook Endpoint Requirements

Your webhook endpoint should:
- Accept POST requests
- Return HTTP 200 status for successful receipt
- Handle potential duplicate deliveries (idempotent)
- Respond within 30 seconds
- Use HTTPS

### Example Webhook Handler (Python/Flask)

```python
from flask import Flask, request, jsonify
import logging

app = Flask(__name__)

@app.route('/webhooks/underwriting-result', methods=['POST'])
def handle_underwriting_result():
    try:
        data = request.get_json()
        job_id = data['job_id']
        client_job_id = data['client_job_id']
        decision = data['decision']

        # Update your loan application status
        update_loan_status(client_job_id, decision, data)

        # Log the result
        logging.info(f"Underwriting completed for {client_job_id}: {decision}")

        return jsonify({"status": "received"}), 200

    except Exception as e:
        logging.error(f"Webhook processing failed: {e}")
        return jsonify({"error": "processing failed"}), 500
```

---

## Error Handling

### Common HTTP Status Codes

| Code | Meaning | Action |
|------|---------|---------|
| 202 | Accepted | Job queued successfully |
| 400 | Bad Request | Check payload format |
| 401 | Unauthorized | Verify API key and signature |
| 422 | Validation Error | Fix missing/invalid fields |
| 429 | Rate Limited | Slow down request rate |
| 500 | Server Error | Retry after delay |

### Validation Error Example

```json
{
  "detail": [
    {
      "type": "missing",
      "loc": ["body", "consent_artifact"],
      "msg": "Field required"
    }
  ]
}
```

---

## Data Security & Privacy

### Security Measures

- **Encryption in Transit:** All API calls use TLS 1.3
- **Data Encryption at Rest:** Sensitive data encrypted with AES-256
- **HMAC Authentication:** Request integrity verification
- **Access Logging:** All API access logged for audit
- **Data Retention:** Customer data deleted after 90 days

### PII Handling

- Citizen IDs are masked in logs and reports
- Personal information is encrypted in database
- PDF files are automatically deleted after processing
- Credit memos exclude raw personal data

---

## Rate Limits & Performance

### Rate Limits

- **Per Tenant:** 60 requests per minute
- **Burst Capacity:** Up to 100 requests in 60 seconds
- **Daily Limit:** 5,000 requests per day

### Performance Expectations

- **API Response Time:** < 1 second (submission)
- **Processing Time:** 30-120 seconds (typical)
- **Availability:** 99.9% uptime SLA
- **Webhook Delivery:** 30-second timeout

---

## Testing & Validation

### Test Mode

Use test data for integration:

```json
{
  "job_id": "TEST-2025-001",
  "applicant": {
    "citizen_id": "TEST12345678",
    "full_name": "Test Applicant",
    "phone": "+976-99999999"
  },
  "documents": {
    "bank_statement_url": "https://your-test-storage.com/test-statement.pdf"
  }
}
```

### Validation Checklist

- [ ] HMAC signature generates correctly
- [ ] PDF URLs are accessible from Softmax servers
- [ ] Webhook endpoint responds with HTTP 200
- [ ] Error handling implemented for all status codes
- [ ] Retry logic for failed requests
- [ ] Logging for audit trail

---

## Sample Integration Code

### Complete Integration Example (Python)

```python
import json
import hmac
import hashlib
import base64
import requests
import time
from typing import Dict, Any

class SoftmaxUnderwritingClient:
    def __init__(self, api_key: str, tenant_secret: str):
        self.api_key = api_key
        self.tenant_secret = tenant_secret
        self.base_url = "https://uw-api.softmax.mn"

    def create_signature(self, payload: Dict[str, Any]) -> tuple[str, bytes]:
        body = json.dumps(payload, separators=(',', ':'), ensure_ascii=False).encode()
        signature = base64.b64encode(
            hmac.new(self.tenant_secret.encode(), body, hashlib.sha256).digest()
        ).decode()
        return signature, body

    def submit_loan_application(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        signature, body = self.create_signature(payload)

        response = requests.post(
            f"{self.base_url}/v1/underwrite",
            data=body,
            headers={
                'X-Api-Key': self.api_key,
                'X-Signature': signature,
                'Content-Type': 'application/json'
            },
            timeout=30
        )

        if response.status_code == 202:
            return response.json()
        else:
            raise Exception(f"API Error {response.status_code}: {response.text}")

    def get_job_status(self, job_id: str) -> Dict[str, Any]:
        response = requests.get(
            f"{self.base_url}/v1/jobs/{job_id}",
            headers={'X-Api-Key': self.api_key},
            timeout=10
        )

        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Status Error {response.status_code}: {response.text}")

    def process_loan_application(self, loan_data: Dict[str, Any]) -> Dict[str, Any]:
        # Submit application
        result = self.submit_loan_application(loan_data)
        job_id = result['job_id']

        # Poll for completion
        max_attempts = 30  # 5 minutes max
        for attempt in range(max_attempts):
            status = self.get_job_status(job_id)

            if status['status'] == 'completed':
                return status
            elif status['status'] == 'failed':
                raise Exception(f"Job failed: {status}")

            time.sleep(10)  # Wait 10 seconds

        raise Exception("Job processing timeout")

# Usage
client = SoftmaxUnderwritingClient(
    api_key="YOUR_API_KEY",
    tenant_secret="YOUR_TENANT_SECRET"
)

loan_application = {
    # ... your loan application data
}

try:
    result = client.process_loan_application(loan_application)
    print(f"Decision: {result['decision']}")
    print(f"Risk Score: {result['risk_score']}")
    print(f"Suggested Rate: {result['interest_rate_suggestion']}%")
except Exception as e:
    print(f"Error: {e}")
```

---

## Support & Contact

### Technical Support

- **Email:** support@softmax.mn
- **Phone:** +976-7777-0000
- **Hours:** 9:00-18:00 (Mongolia Time)
- **SLA:** 4-hour response for production issues

### Documentation Updates

This guide is versioned and updated regularly. Check for updates at:
`https://docs.softmax.mn/underwriting-api/`

### Integration Assistance

Our team provides free integration assistance:
- API walkthrough sessions
- Code review and optimization
- Load testing support
- Production go-live support

---

**Last Updated:** September 26, 2025
**API Version:** v1
**Document Version:** 1.0
