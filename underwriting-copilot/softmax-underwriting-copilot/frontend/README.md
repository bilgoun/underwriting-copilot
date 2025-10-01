# Softmax Underwriting Dashboard - Frontend

React + TypeScript frontend for the Softmax Underwriting Copilot system. Provides separate dashboards for bank users and administrators with role-based access control.

## Features

- **Bank Dashboard**: View job metrics, recent jobs, and detailed results (raw_input and llm_output only)
- **Admin Dashboard**: View all tenants, system-wide metrics, and full job details including llm_input
- **OAuth2 Authentication**: Client credentials flow with role-based scopes
- **Real-time Updates**: Auto-refresh using React Query
- **Responsive UI**: Modern, clean interface built with inline styles

## Tech Stack

- **React 18** - UI framework
- **TypeScript** - Type safety
- **Vite** - Build tool and dev server
- **React Router 6** - Client-side routing
- **React Query** (@tanstack/react-query) - Server state management
- **Axios** - HTTP client
- **Lucide React** - Icon library

## Getting Started

### Prerequisites

- Node.js 18+ and npm
- Backend API running at `http://localhost:8000`

### Installation

```bash
cd frontend
npm install
```

### Development

```bash
npm run dev
```

The dev server will start at `http://localhost:5173` with hot module replacement.

### Build for Production

```bash
npm run build
```

The production build will be output to `frontend/dist/`.

### Preview Production Build

```bash
npm run preview
```

## Project Structure

```
frontend/
├── src/
│   ├── api/
│   │   └── client.ts           # API client and type definitions
│   ├── pages/
│   │   ├── Login.tsx            # OAuth2 login page
│   │   ├── BankDashboard.tsx    # Bank user dashboard
│   │   └── AdminDashboard.tsx   # Admin dashboard
│   ├── utils/
│   │   └── auth.ts              # Authentication hooks and state
│   ├── App.tsx                  # Root component with routing
│   ├── main.tsx                 # Application entry point
│   └── index.css                # Global styles
├── index.html                   # HTML template
├── vite.config.ts               # Vite configuration
├── tsconfig.json                # TypeScript configuration
├── package.json                 # Dependencies and scripts
└── README.md                    # This file
```

## Authentication

### Login Credentials

The system uses OAuth2 client credentials flow with two roles:

**Bank User**:
- Scope: `dashboard:read`
- Can view: raw_input, llm_output, job summaries, metrics

**Admin User**:
- Scope: `dashboard:admin`
- Can view: Everything including llm_input (processed features)

### How It Works

1. User selects role (bank/admin)
2. Enters client_id and client_secret
3. System requests OAuth token with appropriate scope
4. Token stored in localStorage
5. Token included in all API requests via Authorization header
6. Protected routes enforce role-based access

## API Integration

### Base URL Configuration

The frontend expects the API to be available at `/v1`. In development, Vite proxies requests to `http://localhost:8000`.

To change the API URL, modify `vite.config.ts`:

```typescript
export default defineConfig({
  server: {
    proxy: {
      '/v1': {
        target: 'https://your-api-domain.com',
        changeOrigin: true,
      },
    },
  },
})
```

### API Endpoints Used

- `POST /v1/oauth/token` - Get OAuth access token
- `GET /v1/dashboard/tenant/summary` - Bank metrics
- `GET /v1/dashboard/tenant/jobs` - Bank job list
- `GET /v1/dashboard/tenant/jobs/{job_id}` - Bank job detail
- `GET /v1/dashboard/admin/tenants` - Admin tenant overview
- `GET /v1/dashboard/admin/jobs` - Admin job list (all tenants)
- `GET /v1/dashboard/admin/jobs/{job_id}` - Admin job detail (full access)

## Data Visibility

### Bank Dashboard Shows:
- ✅ Job ID, status, decision
- ✅ Raw input (original data from bank)
- ✅ LLM output (credit memo)
- ✅ Audit trail
- ❌ LLM input (processed features - hidden)

### Admin Dashboard Shows:
- ✅ Everything banks can see
- ✅ LLM input (processed features)
- ✅ System-wide metrics
- ✅ All tenant data
- ✅ Cross-tenant job access

## Deployment

### Production Build

1. Build the frontend:
```bash
npm run build
```

2. Deploy the `dist/` directory to your web server or CDN

### Deployment Options

**Option 1: Serve with API (recommended)**
```bash
# Copy built files to API's static directory
cp -r dist/* ../api/static/
```

Then configure your API server to serve static files from `/static/`.

**Option 2: Separate Static Hosting**

Deploy to Netlify, Vercel, or any static host. Update API URL in `vite.config.ts` or use environment variables.

**Option 3: Nginx**

```nginx
server {
    listen 80;
    server_name console.softmax.mn;

    root /var/www/dashboard/dist;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    location /v1 {
        proxy_pass http://api-backend:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### Environment Variables

For production builds with different API URLs, you can use Vite's environment variables:

```bash
# .env.production
VITE_API_BASE_URL=https://api.softmax.mn
```

Then update `api/client.ts`:
```typescript
const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/v1',
})
```

## Troubleshooting

### CORS Errors

If you see CORS errors in development, make sure:
1. Backend API allows requests from `http://localhost:5173`
2. Vite proxy is correctly configured in `vite.config.ts`

### Authentication Issues

If login fails:
1. Check that OAuth endpoint is accessible at `/v1/oauth/token`
2. Verify client credentials are correct
3. Check browser console for detailed error messages
4. Ensure backend has correct OAuth configuration

### 404 Errors on Refresh

If you get 404 errors when refreshing routes:
1. Configure server to serve `index.html` for all routes
2. See Nginx example above for proper configuration

### Data Not Loading

If dashboards show no data:
1. Check Network tab in browser dev tools
2. Verify API endpoints are responding
3. Check that access token is valid and not expired
4. Ensure correct role/scope for the endpoint

## Development Tips

### Hot Module Replacement

Vite provides instant HMR. Changes to React components will update instantly without losing state.

### TypeScript

All API types are defined in `src/api/client.ts`. TypeScript will catch type mismatches at compile time.

### React Query DevTools

To enable React Query DevTools for debugging:

```bash
npm install @tanstack/react-query-devtools
```

Add to `src/main.tsx`:
```typescript
import { ReactQueryDevtools } from '@tanstack/react-query-devtools'

// In your root component
<ReactQueryDevtools initialIsOpen={false} />
```

### Code Organization

- **Components**: Keep reusable components in separate files
- **Hooks**: Extract custom hooks to `src/hooks/`
- **Utils**: Add utility functions to `src/utils/`
- **Types**: API types in `src/api/types.ts`

## Security Considerations

- **Token Storage**: Tokens stored in localStorage (consider httpOnly cookies for production)
- **XSS Protection**: React escapes all rendered values by default
- **HTTPS**: Always use HTTPS in production
- **Token Expiry**: Implement token refresh or re-authentication on expiry

## Performance Optimization

The frontend is optimized for performance:
- **Code Splitting**: React Router lazy loading (can be added)
- **Caching**: React Query caches API responses
- **Auto-refresh**: Smart polling intervals (30s for metrics, 10s for jobs)
- **Minimal Dependencies**: Only essential libraries included

## License

Proprietary - Softmax LLC