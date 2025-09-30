# Frontend Deployment Guide

## Prerequisites on Production VM

SSH into your Azure VM:
```bash
ssh -i ~/Downloads/softmax-uw-worker-eastus-01-key.pem softmax@20.55.31.2
```

## 1. Install Node.js (if not already installed)

```bash
# Install Node.js 20.x LTS
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt-get install -y nodejs

# Verify installation
node --version  # Should be v20.x
npm --version   # Should be 10.x
```

## 2. Clone/Update Repository on VM

```bash
# If not already cloned
cd /opt
sudo git clone https://github.com/YOUR_ORG/softmax-underwriting-copilot.git

# Or update existing
cd /opt/softmax-underwriting-copilot
sudo git pull origin main

# Set permissions
sudo chown -R softmax:softmax /opt/softmax-underwriting-copilot
```

## 3. Build Frontend

```bash
cd /opt/softmax-underwriting-copilot/frontend

# Install dependencies
npm install

# Build for production (this creates frontend/dist)
npm run build
```

## 4. Configure Nginx for Frontend

Create Nginx configuration for console.softmax.mn:

```bash
sudo nano /etc/nginx/sites-available/console.softmax.mn
```

Add this configuration:

```nginx
server {
    listen 80;
    server_name console.softmax.mn;

    root /opt/softmax-underwriting-copilot/frontend/dist;
    index index.html;

    # Serve static files
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

# Reload Nginx
sudo systemctl reload nginx
```

## 5. Setup SSL Certificate with Let's Encrypt

```bash
# Install certbot if not already installed
sudo apt-get update
sudo apt-get install -y certbot python3-certbot-nginx

# Get SSL certificate
sudo certbot --nginx -d console.softmax.mn

# Certbot will automatically:
# 1. Obtain the certificate
# 2. Update Nginx configuration for HTTPS
# 3. Setup auto-renewal
```

## 6. Update Frontend Production Config

Edit the Vite config to use environment variable for API URL:

```bash
cd /opt/softmax-underwriting-copilot/frontend
nano vite.config.ts
```

The proxy configuration should work for production since Nginx will handle routing.

## 7. Verify Deployment

Test the deployment:

```bash
# Check Nginx is running
sudo systemctl status nginx

# Check if files are served
curl -I http://console.softmax.mn

# After DNS propagates and SSL is setup
curl -I https://console.softmax.mn
```

## 8. Setup Automatic Deployment (Optional)

Create a deployment script:

```bash
sudo nano /opt/scripts/deploy-frontend.sh
```

Add:

```bash
#!/bin/bash
set -e

echo "🚀 Deploying frontend..."

cd /opt/softmax-underwriting-copilot

# Pull latest code
git pull origin main

# Build frontend
cd frontend
npm install
npm run build

# Restart Nginx to clear any caches
sudo systemctl reload nginx

echo "✅ Frontend deployed successfully!"
```

Make it executable:

```bash
sudo chmod +x /opt/scripts/deploy-frontend.sh
```

## Troubleshooting

### DNS not propagating
```bash
# Check DNS propagation
dig console.softmax.mn
nslookup console.softmax.mn
```

### Nginx errors
```bash
# Check Nginx error logs
sudo tail -f /var/log/nginx/error.log

# Check Nginx access logs
sudo tail -f /var/log/nginx/access.log
```

### Build errors
```bash
# Clear node modules and rebuild
cd /opt/softmax-underwriting-copilot/frontend
rm -rf node_modules package-lock.json
npm install
npm run build
```