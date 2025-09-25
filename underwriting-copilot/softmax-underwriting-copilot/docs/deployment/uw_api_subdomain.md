# Underwriting API Subdomain Deployment

This note describes the recommended setup for serving the underwriting API on a dedicated subdomain (`uw-api.softmax.mn`) while keeping the existing Django + React stack at `softmax.mn` untouched.

## 1. DNS and Certificates
1. Create an `A`/`AAAA` record for `uw-api.softmax.mn` pointing at the public IP of the underwriting VM or the load balancer in front of it.
2. Issue a TLS certificate for the subdomain (Let's Encrypt, ACM, etc.). Automate renewal (`certbot`, `lego`, or cloud-native tooling).

## 2. Reverse Proxy (Nginx example)
Use the provided `infra/nginx/uw-api.softmax.mn.conf` as a template. It terminates TLS and proxies traffic to the FastAPI app listening on `127.0.0.1:9000`.

```
server {
    listen 443 ssl http2;
    server_name uw-api.softmax.mn;

    ssl_certificate     /etc/ssl/uw-api/fullchain.pem;
    ssl_certificate_key /etc/ssl/uw-api/privkey.pem;

    include snippets/proxy-hardening.conf;

    location / {
        proxy_pass http://127.0.0.1:9000;
        include snippets/proxy-fastapi.conf;
    }
}
```

Reload Nginx after copying the file: `sudo ln -s /opt/softmax/infra/nginx/uw-api.softmax.mn.conf /etc/nginx/sites-enabled/uw-api.softmax.mn.conf && sudo nginx -s reload`.

## 3. Application Service
Install the API on the underwriting VM under `/opt/softmax` and enable the `softmax-uw-api.service` systemd unit provided in `infra/systemd/softmax-uw-api.service`:

```
sudo cp infra/systemd/softmax-uw-api.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now softmax-uw-api.service
```

The service launches Uvicorn on `0.0.0.0:9000` using the virtualenv located at `/opt/venv`. Adjust the path if your deployment varies.

## 4. Network Segmentation
- Expose only ports 80/443 to the internet; keep 9000 bound to localhost.
- Open firewall access from the underwriting VM to Redis/Postgres/LLM endpoints as needed.
- Optionally allow inbound traffic to 443 only from upstream load balancers.

## 5. Request Flow
1. Partner systems or your Django frontend POST to `https://uw-api.softmax.mn/jobs`.
2. Nginx handles TLS and forwards to FastAPI running on the underwriting VM.
3. FastAPI persists the job and enqueues processing via Celery workers (if configured).
4. Results are pushed back through callbacks or fetched via the jobs API without touching the Django stack.

## 6. Health and Monitoring
- `GET https://uw-api.softmax.mn/health` (via existing FastAPI health route) can be wired into uptime checks.
- Forward access/error logs from Nginx and Uvicorn to your logging stack.

## 7. Rollback Plan
Because the subdomain is isolated, you can revert DNS to `softmax.mn` or point the record back to the Django host if issues arise. Keep change windows short and monitor metrics during cutover.

---

Adjust paths, user accounts, and TLS cert references for your environment before deploying.
