# External Data Submission Guide

This guide describes the payload format partner banks must use when sending loan underwriting jobs to Softmax Underwriting Copilot. Follow these conventions so that every dataset can be ingested without manual workarounds while avoiding unnecessary exposure of personally identifiable information (PII).

## 1. Packaging and Transport
- Bundle every job in a single ZIP archive named `job_<job_id>.zip` (example: `job_2025-09-27-0017.zip`).
- The ZIP must contain a single top level directory: `job_<job_id>/`.
- Encode all text files as UTF-8 without BOM.
- Encrypt the archive with PGP or AES-256 when sending over email or shared storage. When using SFTP, encryption is optional but recommended.
- Submit the archive via `POST https://uw-api.softmax.mn/jobs` using `multipart/form-data` with fields `metadata` (JSON manifest) and `payload` (ZIP file). If the API is unavailable, fall back to the secure SFTP drop point agreed during onboarding.

Recommended folder layout:
```
job_<job_id>/
  manifest.json
  borrower.json
  loan_request.json
  collateral.json
  bank_statements/
    <bank_code>_<account_reference>_<currency>.pdf
    metadata.json                # optional per-account metadata
  social_insurance/
    raw.json
  credit_bureau/
    raw.json
  attachments/                   # optional supporting docs
```

## 2. Required Control File: `manifest.json`
`manifest.json` keeps transport level metadata so we can reconcile submissions and trace ownership without storing raw PII.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `job_id` | string | yes | Unique identifier provided by the bank. Must match the archive name. |
| `submitted_at` | string (ISO 8601) | yes | Timestamp when the job bundle was generated. Example `2025-09-27T11:45:00+08:00`. |
| `institution_code` | string | yes | Short code registered with us (for example `PARTNER_BANK`). |
| `contact` | object | yes | Point of contact for clarifications. |
| `contact.name` | string | yes | Responsible analyst (use job title or alias; avoid personal names if policy requires). |
| `contact.email` | string | yes | Shared team inbox for follow ups. |
| `contact.phone` | string | no | Optional shared hotline. |
| `encryption` | object | no | How the payload was encrypted (PGP key id, algorithm). |
| `files_checksum` | array | no | Optional list of `{ "path": "relative/path", "sha256": "..." }`. |

### Sample `manifest.json`
```json
{
  "job_id": "2025-09-27-0017",
  "submitted_at": "2025-09-27T11:45:00+08:00",
  "institution_code": "PARTNER_BANK",
  "contact": {
    "name": "Underwriting Integrations Team",
    "email": "uw-integrations@partnerbank.mn"
  },
  "encryption": {
    "method": "pgp",
    "fingerprint": "8F2A 90B1 45AC 0D2E 1A77  9F2E 3A91 0C58 8F4D 1F21"
  }
}
```

## 3. Borrower Identity File: `borrower.json`
Captures the borrower data we need before scoring. When policy prevents shipping direct identifiers, use hashes or aliases while supplying the original documents in `attachments/`.

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `regnum` | string | yes | Citizen registration number (hash or token if redaction required). |
| `full_name` | string | yes | Full name in Cyrillic (token such as `CLIENT_A` acceptable if ID copy is attached). |
| `dob` | string (ISO date) | yes | Date of birth. |
| `primary_phone` | string | yes | Main mobile number or masked alias. |
| `email` | string | no | Shared contact inbox if applicant email may not be stored. |
| `employer` | object | no | Employer details matching social insurance source. |
| `employer.name` | string | no | Legal entity name. |
| `employer.regnum` | string | no | Employer registration number. |
| `household_size` | integer | no | Optional for affordability heuristics. |

## 4. Loan Request File: `loan_request.json`
This file describes the requested facility. Multiple facilities may be provided using an array; most partners submit a single loan object.

```json
{
  "currency": "MNT",
  "amount": 50000000,
  "term_months": 60,
  "product_type": "consumer_installment",
  "interest_rate_annual_pct": 18.0,
  "repayment_frequency": "monthly",
  "purpose": "home_improvement",
  "requested_disbursement_date": "2025-10-01"
}
```

### Required fields
- `currency`: ISO 4217 code (`MNT`, `USD`).
- `amount`: numeric, rounded to the smallest currency unit.
- `term_months`: integer greater than zero.
- `product_type`: string aligned with your internal catalog (examples: `consumer_installment`, `business_working_capital`).

### Optional fields
- `interest_rate_annual_pct`, `repayment_frequency`, `purpose`, `requested_disbursement_date`, `co_borrowers` (array), `comments`.

## 5. Bank Statements Directory: `bank_statements/`
- Provide one PDF per deposit account used for underwriting.
- File name pattern: `<bank_code>_<account_reference>_<currency>.pdf` (example: `KHAN_ACC001_MNT.pdf`). Use an internal account reference that maps back on your side rather than exposing the full account number when possible.
- Each PDF must contain at least the last 6 months of activity and include opening and closing balances.
- When multiple statements are needed because of page limits, append `_partN` before the extension (`KHAN_ACC001_MNT_part2.pdf`).
- Optional `metadata.json` per directory to list account level details that cannot be captured from the PDF.

Example `metadata.json`:
```json
{
  "accounts": [
    {
      "bank_code": "KHAN",
      "account_reference": "ACC001",
      "currency": "MNT",
      "account_type": "SAVINGS",
      "holder_alias": "CLIENT_A"
    }
  ]
}
```

## 6. Social Insurance Data: `social_insurance/raw.json`
- Provide the unmodified API response received from the General Authority of Social Insurance.
- Ensure the JSON includes the request block, response list data, and computed totals when available.
- If multiple sources or time ranges are provided, include them as an array under `responses` inside the same JSON.
- Make sure numeric fields remain numeric (do not export as strings).
- If PII must be redacted, hash identifiers but keep the hash stable across submissions so we can join records.

## 7. Credit Bureau Data: `credit_bureau/raw.json`
- Submit the complete JSON returned by the credit bureau vendor (e.g., Mongolian Credit Bureau, TransUnion).
- The object must at least include: `bureau`, `pull`, `subject`, `score`, `summary`, and `accounts` sections.
- Replace direct identifiers inside `subject` with aliases if your policy requires, but preserve structure (for example, `fullNameAlias`, `regnumHash`).
- If supporting PDFs are required by regulation, place them inside `credit_bureau/attachments/` with meaningful names.

## 8. Collateral Information: `collateral.json`
Provide sufficient structure for the market search and valuation engine.

```json
{
  "type": "real_estate",
  "name": "Alpha Zone 3 oroo 80 mkv",
  "size_m2": 80,
  "city": "Ulaanbaatar",
  "district": "Khan-Uul",
  "block": "Alpha Zone Tower B",
  "floor": 15,
  "parking": true,
  "documents": ["deed_placeholder.pdf"],
  "notes": "Include both Cyrillic and Latin aliases when available."
}
```

### Required fields
- `type`: one of `real_estate`, `vehicle`, `cash_deposit`, `other`.
- `name`: human readable identifier. For real estate, include building or project name plus unit type.
- `size_m2`: numeric for real estate. For vehicles, use `vehicle_spec` instead.

### Optional enrichments
- `aliases`: array of strings for alternative spellings (useful for search).
- `valuation_override_mnt`: numeric if the bank already has an internal value.
- `lien_status`: `free`, `encumbered`, etc.
- `documents`: list of filenames residing in `attachments/`.

## 9. Additional Attachments
Place supporting documents (IDs, business licenses, tax filings) under `attachments/`. Use descriptive English file names (for example `attachments/tax_return_2024.pdf`).

## 10. Submission Checklist
- [ ] Archive named `job_<job_id>.zip` with matching directory name.
- [ ] `manifest.json`, `borrower.json`, `loan_request.json`, and `collateral.json` present and validated against this guide.
- [ ] At least one bank statement PDF supplied; file names follow the specified pattern.
- [ ] Social insurance and credit bureau JSON files are raw, machine readable, and untruncated (with hashed aliases if required by policy).
- [ ] All JSON passes linting (`python -m json.tool <file>` can be used before submission).
- [ ] Encryption key shared with Softmax ahead of submission when using encrypted archives.

## 11. Support
For onboarding or schema questions, contact `integrations@softmax.mn`. Include the `job_id` in your email subject so that we can trace the relevant submission quickly.
