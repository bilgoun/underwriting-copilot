# Complete Production Deployment Guide

## Step-by-Step Deployment Process

### Step 1: Push Code to GitHub

First, let's commit and push all the latest changes:

```bash
cd /Users/bilguundavaa/underwriting-copilot/softmax-underwriting-copilot

# Add all files
git add .

# Commit with descriptive message
git commit -m "Add frontend dashboard and production deployment configs"

# Push to main branch
git push origin main
```

### Step 2: DNS Configuration

In your DNS control panel (screenshot shows standard interface):

**Add A Record:**
- **Type**: A Record
- **Host/Name**: `console`
- **Points to**: `20.55.31.2`
- **TTL**: 3600 (or leave as Auto)

This creates: `console.softmax.mn` → `20.55.31.2`

**Verify DNS propagation:**
```bash
# Wait 5-10 minutes, then check:
dig console.softmax.mn
# Should return: 20.55.31.2
```

### Step 3: SSH into Production VM

```bash
ssh -i ~/Downloads/softmax-uw-worker-eastus-01-key.pem softmax@20.55.31.2
```

### Step 4: Pull Latest Code on VM

```bash
cd /opt/softmax-underwriting-copilot
git pull origin main
```

### Step 5: Install Node.js (if needed)

```bash
# Check if Node.js is installed
node --version

# If not, install Node.js 20.x LTS
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt-get install -y nodejs

# Verify
node --version  # Should be v20.x
npm --version   # Should be 10.x
```

### Step 6: Build Frontend

```bash
cd /opt/softmax-underwriting-copilot/frontend

# Install dependencies
npm install

# Build for production
npm run build

# Verify build
ls -lh dist/
```

### Step 7: Configure Nginx for Frontend

```bash
# Create Nginx configuration
sudo nano /etc/nginx/sites-available/console.softmax.mn
```

Paste this configuration:

```nginx
server {
    listen 80;
    server_name console.softmax.mn;

    root /opt/softmax-underwriting-copilot/frontend/dist;
    index index.html;

    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types text/plain text/css text/xml text/javascript application/javascript application/json;

    # Serve static files with caching
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # Serve index.html for all routes (SPA)
    location / {
        try_files $uri $uri/ /index.html;
    }

    # Proxy API requests to backend
    location /v1/ {
        proxy_pass http://localhost:8000/v1/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
    }

    # Proxy OAuth requests
    location /oauth/ {
        proxy_pass http://localhost:8000/oauth/;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Enable the site:

```bash
# Create symbolic link
sudo ln -s /etc/nginx/sites-available/console.softmax.mn /etc/nginx/sites-enabled/

# Test configuration
sudo nginx -t

# Should output: "syntax is ok" and "test is successful"

# Reload Nginx
sudo systemctl reload nginx
```

### Step 8: Setup SSL Certificate

```bash
# Install certbot (if not already installed)
sudo apt-get update
sudo apt-get install -y certbot python3-certbot-nginx

# Get SSL certificate for console.softmax.mn
sudo certbot --nginx -d console.softmax.mn

# Follow prompts:
# 1. Enter email address
# 2. Agree to terms
# 3. Choose redirect HTTP to HTTPS (option 2)
```

Certbot will automatically:
- Obtain SSL certificate from Let's Encrypt
- Update Nginx config to use HTTPS
- Setup auto-renewal (runs twice daily)

### Step 9: Create Production Admin Credentials

```bash
cd /opt/softmax-underwriting-copilot

# Generate production admin credentials
python3 scripts/create_tenant.py \
  --name "Softmax Admin Console" \
  --client-id "admin_prod" \
  --scope "dashboard:admin"

# Save the output credentials securely!
```

### Step 10: Verify Deployment

```bash
# Test HTTP (should redirect to HTTPS)
curl -I http://console.softmax.mn

# Test HTTPS
curl -I https://console.softmax.mn

# Check Nginx logs
sudo tail -f /var/log/nginx/access.log
```

### Step 11: Load Simulation Data (Optional)

To see data in the dashboard:

```bash
cd /opt/softmax-underwriting-copilot

# Run simulation to create test data
python3 scripts/run_simulations.py

# This will create jobs in the database that appear in dashboard
```

### Step 12: Access Dashboard

Open browser and navigate to:
```
https://console.softmax.mn
```

Login with admin credentials from Step 9.

## Production Checklist

- [ ] Code pushed to GitHub
- [ ] DNS A record added for console.softmax.mn
- [ ] DNS propagated (dig console.softmax.mn returns 20.55.31.2)
- [ ] Latest code pulled on VM
- [ ] Node.js installed (v20.x)
- [ ] Frontend built successfully
- [ ] Nginx configured for console.softmax.mn
- [ ] SSL certificate installed
- [ ] HTTPS redirect working
- [ ] Admin credentials generated
- [ ] Dashboard accessible at https://console.softmax.mn
- [ ] Login working
- [ ] API proxy working (/v1/ and /oauth/)

## Maintenance Commands

### Update Frontend
```bash
cd /opt/softmax-underwriting-copilot
git pull origin main
cd frontend
npm install
npm run build
sudo systemctl reload nginx
```

### View Logs
```bash
# Frontend/Nginx access logs
sudo tail -f /var/log/nginx/access.log

# Frontend/Nginx error logs
sudo tail -f /var/log/nginx/error.log

# Backend API logs
sudo journalctl -u softmax-uw-worker -f
```

### SSL Certificate Renewal
```bash
# Test renewal (dry run)
sudo certbot renew --dry-run

# Renewal happens automatically, check status
sudo certbot certificates
```

## Troubleshooting

### Frontend shows blank page
- Check browser console for errors
- Verify dist/ folder exists and has files
- Check Nginx error logs

### API requests failing
- Verify backend is running: `sudo systemctl status softmax-uw-worker`
- Check if port 8000 is open: `lsof -i:8000`
- Test API directly: `curl http://localhost:8000/healthz`

### SSL issues
- Verify certificate: `sudo certbot certificates`
- Renew if needed: `sudo certbot renew`
- Check Nginx SSL config

### DNS not resolving
- Check DNS record: `dig console.softmax.mn`
- Wait for propagation (can take 5-60 minutes)
- Try from different network/device

## Security Notes

1. **Credentials**: Store admin credentials securely (password manager)
2. **Firewall**: Ensure only ports 80, 443, and 22 are open
3. **Updates**: Keep system packages updated
4. **Backups**: Database is in `/var/lib/postgresql/` - backup regularly
5. **Monitoring**: Check logs regularly for suspicious activity