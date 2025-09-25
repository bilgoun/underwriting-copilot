# Softmax Underwriting Copilot - Complete System Documentation

## Overview

**Softmax Underwriting Copilot** is a production-ready loan underwriting system that processes loan applications from Mongolian banks. The system receives comprehensive loan applicant data (bank statements, credit bureau reports, social insurance data, collateral information), processes it through an intelligent pipeline, and generates detailed credit memos using LLM technology.

### Key Features
- **FastAPI REST API** with OAuth2 authentication and HMAC signature verification
- **Celery + Redis** asynchronous worker pipeline for heavy processing tasks
- **Bank Statement PDF Parser** that extracts financial transactions and calculates average monthly income
- **Collateral Valuation System** with ML model integration for cars and web search for real estate
- **LLM-Powered Credit Memo Generation** (currently sandbox mode with placeholder for production LLM)
- **PostgreSQL** persistence with encrypted JSON storage
- **Production-ready deployment** with Docker, Kubernetes, and systemd configurations

## System Architecture

```
Banks/Partners → API Gateway → FastAPI → Celery Workers → LLM/ML Models
                     ↓              ↓           ↓
               PostgreSQL    Redis Queue   File Storage
                     ↓              ↓           ↓
               Encrypted Data  Background Jobs  PDFs/Results
```

### Data Flow
1. **Bank submits loan application** via API with:
   - Bank statement PDF URL
   - Credit bureau data
   - Social insurance records
   - Loan request details
   - Collateral information
2. **API validates and queues** the request
3. **Celery worker processes**:
   - Downloads and parses bank statement PDF
   - Calculates average monthly income from transactions
   - Evaluates collateral value (ML model for cars, web search for real estate)
   - Fuses all data into structured features
   - Generates credit memo via LLM
4. **Results delivered** via webhook callback

## Directory Structure

```
softmax-underwriting-copilot/
├── app/                         # Main application code
│   ├── config.py               # Environment-driven settings
│   ├── main.py                 # FastAPI application entry point
│   ├── models.py               # SQLAlchemy database models
│   ├── schemas.py              # Pydantic request/response schemas
│   ├── db.py                   # Database operations and encryption
│   ├── security.py             # Authentication and HMAC verification
│   ├── routes/                 # API endpoints
│   │   ├── ingest.py          # POST /v1/underwrite
│   │   ├── jobs.py            # GET /v1/jobs/{job_id}
│   │   ├── auth.py            # OAuth2 token endpoint
│   │   └── webhooks.py        # Webhook testing
│   ├── pipeline/               # Core processing pipeline
│   │   ├── parser_adapter.py  # Bank statement PDF parser
│   │   ├── bank_parser/       # Bank-specific parsers (Golomt, Khan, etc.)
│   │   ├── collateral.py      # Collateral valuation logic
│   │   ├── market_search.py   # Real estate web search functionality
│   │   ├── fuse.py            # Data fusion and feature engineering
│   │   ├── llm.py             # LLM integration (sandbox mode)
│   │   ├── rules.py           # Business rules and guardrails
│   │   └── sanitizer.py       # Data sanitization
│   ├── workers/                # Background job processing
│   │   ├── celery_app.py      # Celery configuration
│   │   ├── tasks.py           # Main underwriting task
│   │   └── polling_worker.py  # Fallback when Redis unavailable
│   └── utils/                  # Utility modules
│       ├── pdf.py             # PDF validation
│       ├── storage.py         # File download/storage
│       └── webhooks.py        # Webhook emission
├── mockdata/                   # Sample data for testing
│   ├── *.pdf                  # Bank statement samples
│   ├── api_submission_example.json
│   ├── Creditbureaumock.json
│   ├── SocialInsurancemock.json
│   └── loanrequest.json
├── scripts/                    # Deployment and testing scripts
│   ├── bootstrap_db.sh        # Database initialization
│   ├── gen_hmac_secret.py     # Generate HMAC secrets
│   └── load_test.py           # Performance testing
├── infra/                      # Infrastructure configurations
│   ├── cloud-init/           # Azure VM setup
│   ├── systemd/              # Service definitions
│   └── nginx/                # Nginx configurations
├── k8s/                       # Kubernetes manifests
├── tests/                     # Unit and integration tests
├── docker-compose.yaml        # Local development setup
└── requirements.txt           # Python dependencies
```

## Core Components Deep Dive

### 1. Bank Statement Parser (`app/pipeline/bank_parser/`)

**Purpose**: Extracts transaction data from PDF bank statements from major Mongolian banks.

**Key Files**:
- `registry.py` - Registry pattern for bank detection
- `DataHandler.py` - Bank-specific parsers (Golomt, Khan, State Bank, etc.)
- `AnalyzeDescription.py` - Transaction description NLP analysis
- `MonthlyBalances.py` - Monthly aggregation and suspicious transaction detection
- `PredictIncExp.py` - Income/expense regression analysis

**Process**:
1. PDF text extraction using pdfplumber
2. Bank detection based on PDF content patterns
3. Transaction parsing with date, amount, description extraction
4. Income calculation from credit transactions
5. Expense analysis from debit transactions

### 2. Collateral Valuation (`app/pipeline/collateral.py`)

**Purpose**: Determines market value of collateral assets.

**For Vehicles**:
- Calls external ML API at `https://softmax.mn/api/predict-price/`
- Uses car details (make, model, year, mileage, condition)
- Returns estimated value with confidence score

**For Real Estate**:
- Web search using SerpAPI/Tavily APIs
- Searches Mongolian real estate sites
- Price parsing with size normalization (price per m²)
- Statistical analysis of comparable properties

### 3. Market Search (`app/pipeline/market_search.py`)

**Purpose**: Real estate market analysis through web scraping.

**Features**:
- **Multi-provider search**: SerpAPI and Tavily integration
- **Cyrillic/Latin transliteration** for Mongolian search terms
- **Price extraction**: Regex patterns for MNT amounts
- **Size normalization**: Square meter parsing and validation
- **Quality filtering**: Removes rental listings, validates price ranges
- **Statistical analysis**: Median, mean, confidence scoring

**Search Strategy**:
```python
# Example search queries generated
"байр борлуулах" + location + size
"apartment for sale" + location
"real estate" + location + "Mongolia"
```

### 4. LLM Integration (`app/pipeline/llm.py`)

**Current State**: Sandbox mode with structured mock responses.

**Production Ready For**:
- Azure OpenAI integration (placeholder implemented)
- Input: Structured JSON with all fused features
- Output: Markdown credit memo with decision and recommendations
- System prompt optimized for Mongolian banking context

### 5. Data Fusion (`app/pipeline/fuse.py`)

**Purpose**: Combines all data sources into structured features for LLM.

**Inputs**:
- Bank statement analysis (income, expenses, transaction patterns)
- Credit bureau data (score, payment history, existing loans)
- Social insurance records (employment history, salary verification)
- Collateral valuation (market value, confidence, risk assessment)
- Legal checks and other third-party data

**Output**: Mongolian-labeled JSON structure ready for LLM processing.

## API Endpoints

### Core Underwriting API
- `POST /v1/underwrite` - Submit loan application for processing
- `GET /v1/jobs/{job_id}` - Check job status and retrieve results
- `POST /v1/jobs/pull` - Polling fallback for workers
- `POST /v1/jobs/complete` - Complete job via polling

### Authentication & Webhooks
- `POST /oauth/token` - OAuth2 client credentials flow
- `POST /v1/webhooks/test` - Test webhook delivery

### Health & Monitoring
- `GET /healthz` - Health check
- `GET /readyz` - Readiness check
- `GET /metrics` - Prometheus metrics

## Data Models

### Canonical Payload Schema
```json
{
  "job_id": "JOB-2025-0001",
  "tenant_id": "PARTNER_BANK",
  "applicant": {
    "citizen_id": "УН98042314",
    "full_name": "Итгэл Даваа",
    "phone": "+976-99123456"
  },
  "loan": {
    "type": "consumer_loan",
    "amount": 50000000,
    "term_months": 36
  },
  "documents": {
    "bank_statement_url": "https://example.com/statement.pdf",
    "bank_statement_period": {
      "from": "2024-01-01T00:00:00Z",
      "to": "2024-12-31T23:59:59Z"
    }
  },
  "collateral": {
    "type": "Vehicle",
    "plateNo": "УНН-1234",
    "brand": "Lexus",
    "model": "RX",
    "yearMade": 2015,
    "declared_value": 32000000
  },
  "third_party_data": {
    "mongolbank_credit": { /* Credit bureau data */ },
    "social_security": { /* Social insurance records */ },
    "legal_checks": { /* Legal verification data */ }
  },
  "callback_url": "https://partner.bank/webhooks/underwriting"
}
```

## VM Setup and Deployment

### Azure VM Configuration
**VM Type**: F16s v2 (16 vCPUs, 32 GB RAM)
**IP**: `20.55.31.2`
**SSH Access**: `ssh -i ~/Downloads/softmax-uw-worker-eastus-01-key.pem softmax@20.55.31.2`

### Subdomain Configuration
**API Endpoint**: `https://uw-api.softmax.mn`
**Nginx Configuration**: Reverse proxy to localhost:8000
**SSL**: Let's Encrypt certificate (auto-renewal enabled)

### Service Configuration
```bash
# Systemd service at /etc/systemd/system/softmax-uw-worker.service
[Unit]
Description=Softmax Underwriting Celery Worker
After=network-online.target

[Service]
User=softmax
WorkingDirectory=/opt/softmax
Environment=TMPDIR=/mnt/softmax_tmp
EnvironmentFile=/etc/softmax/worker.env
ExecStart=/opt/venv/bin/celery -A app.workers.celery_app.celery_app worker -l INFO -c 12
Restart=always

[Install]
WantedBy=multi-user.target
```

### Environment Variables
Key production environment variables:
```bash
DATABASE_URL=postgresql+psycopg://user:pass@host:5432/softmax
REDIS_URL=rediss://redis.host:6380/0
ENCRYPTION_KEY=<32-byte-base64-key>
SANDBOX_MODE=false
COLLATERAL_API_KEY=<secret-api-key>
SOFTMAX_COLLATERAL_URL=https://softmax.mn
SERPAPI_API_KEY=<serpapi-key>
TAVILY_API_KEY=<tavily-key>
```

## Security Features

### Authentication
- **OAuth2 Client Credentials** flow for API access
- **API Key** authentication for simple integrations
- **HMAC Signature Verification** for request integrity
- **Rate Limiting** per tenant

### Data Protection
- **Fernet Encryption** for sensitive data at rest
- **HTTPS Only** communication
- **Field-level Encryption** for PII in database
- **Audit Trail** for all operations

### Input Validation
- **PDF Validation** before processing
- **Signature Verification** on all inbound requests
- **Schema Validation** with Pydantic
- **SQL Injection Prevention** with SQLAlchemy ORM

## Monitoring and Observability

### Metrics (Prometheus)
- `jobs_created_total` - Total jobs submitted
- `jobs_failed_total` - Failed job count
- `underwrite_duration_seconds` - End-to-end processing time
- `webhook_attempts_total` - Webhook delivery attempts
- `webhook_failures_total` - Failed webhook deliveries

### Logging
- **Structured JSON logs** with structlog
- **Request ID propagation** for tracing
- **PII redaction** in logs
- **Multi-level logging** (DEBUG, INFO, WARNING, ERROR)

## Testing

### Unit Tests
```bash
export ENCRYPTION_KEY=$(python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())")
export DATABASE_URL=sqlite+pysqlite:///:memory:
export SANDBOX_MODE=true
pytest -q
```

### Load Testing
```bash
python scripts/load_test.py --api http://localhost:8080/v1/underwrite \
  --jobs 100 --api-key <key> --tenant-secret <secret> --tenant-id <tenant>
```

### Integration Testing
- Bank statement parsing with real PDF samples
- Collateral API integration testing
- Webhook delivery verification
- End-to-end pipeline testing

## Production Readiness

### Performance Targets
- **p95 latency**: < 20 seconds end-to-end
- **Failure rate**: < 0.5%
- **Throughput**: 100+ concurrent jobs
- **Availability**: 99.9% uptime

### Deployment Architecture
- **GCP**: API service on Cloud Run with managed databases
- **Azure**: F16s v2 worker VM for CPU-intensive parsing
- **Cross-cloud**: Redis TLS and PostgreSQL connectivity
- **Load balancing**: Multiple worker instances for scaling

### Operational Procedures
- **Database backups**: Automated with encryption
- **Secret rotation**: Environment variable updates
- **Service updates**: Blue/green deployment strategy
- **Incident response**: Structured logging and alerting

## Future Enhancements

### Planned Features
1. **Real LLM Integration** (Azure OpenAI/Anthropic Claude)
2. **Advanced ML Models** for risk scoring
3. **Multi-language Support** (English/Mongolian)
4. **Real-time Processing** with WebSocket updates
5. **Advanced Analytics** and reporting dashboards

### Technical Improvements
1. **Caching Layer** (Redis) for frequent calculations
2. **Message Queuing** improvements with dead letter queues
3. **Microservices Architecture** for better scalability
4. **API Versioning** strategy for backward compatibility
5. **Container Orchestration** with Kubernetes

## Troubleshooting Guide

### Common Issues
1. **Bank Parser Fails**: Check PDF format compatibility, ensure dependencies installed
2. **Collateral API 403**: Verify API key and IP allowlist
3. **Redis Connection**: Check network connectivity and TLS configuration
4. **Database Encryption**: Ensure ENCRYPTION_KEY is properly set
5. **Webhook Delivery**: Verify callback URL accessibility and signature verification

### Debug Commands
```bash
# Check worker status
sudo systemctl status softmax-uw-worker

# View worker logs
sudo journalctl -u softmax-uw-worker -f

# Test PDF parsing
python -c "from app.pipeline.parser_adapter import parse; print(parse('/path/to/statement.pdf'))"

# Verify database connection
python -c "from app.db import engine; print(engine.connect())"
```

## Contact and Maintenance

This system is designed for **24/7 production operation** supporting Mongolian financial institutions. For operational issues or feature requests, refer to the monitoring dashboards and structured logs for diagnostic information.

**Key Principles**:
- **Security First**: All sensitive data encrypted at rest and in transit
- **Reliability**: Comprehensive error handling and recovery mechanisms
- **Scalability**: Designed to handle increasing transaction volumes
- **Maintainability**: Clean architecture with comprehensive documentation
- **Observability**: Full visibility into system performance and health