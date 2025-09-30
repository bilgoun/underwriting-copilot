# Admin Credentials

Your admin credentials have been generated and saved.

## Credentials

```
Client ID:     admin_rMCt7uSuDHDMgppth5w6oQ
Client Secret: 79qTxaw-MKz1lh7xx4AjTFDRxkPqfV8B3i-223YeLhY
API Key:       sk_admin_uNfqklcZPqqg8jX5nIIa2tMb_wirXfevqOC-73rDYU8
Scope:         dashboard:admin
```

## How to Start the System

### 1. Start the API Server

```bash
cd /Users/bilguundavaa/underwriting-copilot/softmax-underwriting-copilot
./START_API_SERVER.sh
```

Or manually:
```bash
cd /Users/bilguundavaa/underwriting-copilot/softmax-underwriting-copilot
export DATABASE_URL="sqlite+pysqlite:///:memory:"
uvicorn app.main:app --reload --port 8000
```

### 2. Start the Frontend Dashboard

In a new terminal:
```bash
cd /Users/bilguundavaa/underwriting-copilot/softmax-underwriting-copilot/frontend
npm run dev
```

### 3. Access the Dashboard

Open your browser to: http://localhost:3000

## How to Use OAuth Credentials

### Get an Access Token

```bash
curl -X POST http://localhost:8000/oauth/token \
  -H "Content-Type: application/json" \
  -d '{
    "grant_type": "client_credentials",
    "client_id": "admin_rMCt7uSuDHDMgppth5w6oQ",
    "client_secret": "79qTxaw-MKz1lh7xx4AjTFDRxkPqfV8B3i-223YeLhY",
    "scope": "dashboard:admin"
  }'
```

### Use the Access Token

```bash
# Get all jobs
curl -X GET http://localhost:8000/v1/admin/jobs \
  -H "Authorization: Bearer <access_token>"

# Get specific job
curl -X GET http://localhost:8000/v1/admin/jobs/<job_id> \
  -H "Authorization: Bearer <access_token>"
```

### Or Use API Key Directly

```bash
curl -X GET http://localhost:8000/v1/admin/jobs \
  -H "Authorization: Bearer sk_admin_uNfqklcZPqqg8jX5nIIa2tMb_wirXfevqOC-73rDYU8"
```

## Dashboard Roles

### Admin User (scope: dashboard:admin)
- Full access to all underwriting jobs
- Can view sensitive data including:
  - Raw applicant input
  - Processed LLM features
  - Credit bureau data
  - All decision details

### Bank User (scope: dashboard:read)
- Limited access to their tenant's jobs only
- Cannot view:
  - LLM processed features
  - Other tenants' data

## Important Notes

1. **Database**: The API server is configured to use an in-memory SQLite database for testing. Data will be lost when the server stops.

2. **Production Database**: To use PostgreSQL in production, set:
   ```bash
   export DATABASE_URL="postgresql+psycopg://user:pass@host:5432/dbname"
   ```

3. **Credentials**: These credentials are saved in `ADMIN_CREDENTIALS.txt`. Keep them secure!

4. **Simulation Data**: To view simulation data in the dashboard, you'll need to:
   - Load the simulation results into the database, OR
   - Run the simulation script with the API server running

## Troubleshooting

### "Module 'app' not found"
Make sure you're in the correct directory:
```bash
cd /Users/bilguundavaa/underwriting-copilot/softmax-underwriting-copilot
```

### "Address already in use"
Kill the process using port 8000:
```bash
lsof -ti:8000 | xargs kill -9
```

### Database connection errors
Use in-memory SQLite for local testing:
```bash
export DATABASE_URL="sqlite+pysqlite:///:memory:"
```

## API Documentation

Once the server is running, access the interactive API docs:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc