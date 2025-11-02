# HOA Deployment Guide

Production deployment guide for the HOA authentication system.

**Version**: 1.0.0

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Configuration](#configuration)
3. [Production Build](#production-build)
4. [Deployment Options](#deployment-options)
5. [Database Setup](#database-setup)
6. [SSL/TLS Configuration](#ssltls-configuration)
7. [Monitoring](#monitoring)
8. [Backup & Recovery](#backup--recovery)
9. [Security Hardening](#security-hardening)
10. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### Server Requirements

- **OS**: Ubuntu 22.04 LTS or similar Linux distribution
- **CPU**: 2+ cores recommended
- **RAM**: 2GB minimum, 4GB recommended
- **Disk**: 10GB minimum
- **Python**: 3.11 or higher
- **Domain**: Required for production WebAuthn (localhost not sufficient)
- **SSL Certificate**: Required (Let's Encrypt recommended)

### Software Requirements

```bash
# Install system dependencies
sudo apt update
sudo apt install -y python3.11 python3.11-venv python3-pip nginx postgresql

# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh
```

---

## Configuration

### Environment Variables

Create a production environment file:

```bash
# /opt/hoa/.env.production
HOA_HOST=0.0.0.0
HOA_PORT=8000
HOA_DATABASE_URL=postgresql://hoa_user:password@localhost/hoa_prod
HOA_SECRET_KEY=<generate-secure-key-here>
HOA_JWT_ALGORITHM=RS256
HOA_JWT_EXPIRATION_MINUTES=60
HOA_JWT_REFRESH_EXPIRATION_DAYS=30
HOA_ALLOWED_RPS=yourdomain.com|Your App|https://yourdomain.com;https://www.yourdomain.com
HOA_REQUIRE_AUTH_METHOD_APPROVAL=false
HOA_ALLOW_SELF_SERVICE_AUTH=true
HOA_ENVIRONMENT=production
HOA_LOG_LEVEL=INFO
HOA_SESSION_MAX_AGE_DAYS=14
HOA_SESSION_COOKIE_SECURE=true
HOA_SESSION_COOKIE_HTTPONLY=true
HOA_SESSION_COOKIE_SAMESITE=lax
HOA_CORS_ENABLED=true
HOA_CORS_ORIGINS='["https://yourdomain.com", "https://www.yourdomain.com"]'
```

### Generate Secrets

```bash
# Generate secret key
python3 -c "import secrets; print(secrets.token_urlsafe(32))"

# Generate admin token
python3 -c "import secrets; print(secrets.token_urlsafe(24))"
```

### Config File

Alternatively, use YAML config at `~/.config/hoa/config.yaml`:

```yaml
# ~/.config/hoa/config.yaml
host: 0.0.0.0
port: 8000
database-url: postgresql://hoa_user:password@localhost/hoa_prod
secret-key: your-secret-key-here
jwt-algorithm: RS256
jwt-expiration-minutes: 60
jwt-refresh-expiration-days: 30
allowed-rps: yourdomain.com|Your App|https://yourdomain.com;https://www.yourdomain.com
require-auth-method-approval: false
allow-self-service-auth: true
environment: production
log-level: INFO
session-max-age-days: 14
session-cookie-secure: true
session-cookie-httponly: true
session-cookie-samesite: lax
cors-enabled: true
cors-origins:
  - https://yourdomain.com
  - https://www.yourdomain.com
```

---

## Production Build

### 1. Clone Repository

```bash
sudo mkdir -p /opt/hoa
sudo chown $USER:$USER /opt/hoa
cd /opt/hoa
git clone https://github.com/yourusername/hoa.git .
```

### 2. Install Backend Dependencies

```bash
cd /opt/hoa
uv sync --frozen
```

### 3. Build Frontend

```bash
cd /opt/hoa/frontend
npm install -g yarn  # If not installed
yarn install
yarn build  # Outputs to ../hoa/static/
```

### 4. Create Service User

```bash
sudo useradd -r -s /bin/false hoa
sudo chown -R hoa:hoa /opt/hoa
```

---

## Deployment Options

### Option 1: Systemd Service (Recommended)

**1. Create systemd service file:**

```bash
sudo nano /etc/systemd/system/hoa.service
```

```ini
[Unit]
Description=HOA Authentication Service
After=network.target postgresql.service

[Service]
Type=simple
User=hoa
Group=hoa
WorkingDirectory=/opt/hoa
Environment="PATH=/opt/hoa/.venv/bin:/usr/local/bin:/usr/bin:/bin"
EnvironmentFile=/opt/hoa/.env.production
ExecStart=/opt/hoa/.venv/bin/uvicorn hoa.app:create_app --factory --host 0.0.0.0 --port 8000 --workers 4
Restart=always
RestartSec=10

# Security
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/opt/hoa

[Install]
WantedBy=multi-user.target
```

**2. Enable and start service:**

```bash
sudo systemctl daemon-reload
sudo systemctl enable hoa
sudo systemctl start hoa
sudo systemctl status hoa
```

**3. View logs:**

```bash
sudo journalctl -u hoa -f
```

### Option 2: Docker (Recommended for Containers)

**Dockerfile:**

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install uv
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.cargo/bin:$PATH"

# Copy application
COPY . /app

# Install dependencies
RUN uv sync --frozen

# Build frontend
RUN cd frontend && \
    npm install -g yarn && \
    yarn install && \
    yarn build

# Expose port
EXPOSE 8000

# Run application
CMD ["uv", "run", "uvicorn", "hoa.app:create_app", "--factory", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
```

**docker-compose.yml:**

```yaml
version: "3.8"

services:
  hoa:
    build: .
    ports:
      - "8000:8000"
    environment:
      - HOA_DATABASE_URL=postgresql://hoa_user:password@postgres:5432/hoa_prod
      - HOA_SECRET_KEY=${HOA_SECRET_KEY}
      - HOA_ALLOWED_RPS=${HOA_ALLOWED_RPS}
      - HOA_ENVIRONMENT=production
    depends_on:
      - postgres
    restart: unless-stopped

  postgres:
    image: postgres:15
    environment:
      - POSTGRES_DB=hoa_prod
      - POSTGRES_USER=hoa_user
      - POSTGRES_PASSWORD=password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: unless-stopped

  nginx:
    image: nginx:latest
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - /etc/letsencrypt:/etc/letsencrypt:ro
    depends_on:
      - hoa
    restart: unless-stopped

volumes:
  postgres_data:
```

**Build and run:**

```bash
docker-compose up -d
docker-compose logs -f
```

### Option 3: Manual with Gunicorn

```bash
# Install gunicorn
uv pip install gunicorn

# Run with gunicorn
cd /opt/hoa
gunicorn hoa.app:create_app \
  --factory \
  --bind 0.0.0.0:8000 \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --access-logfile - \
  --error-logfile -
```

---

## Database Setup

### PostgreSQL Setup

**1. Install PostgreSQL:**

```bash
sudo apt install postgresql postgresql-contrib
```

**2. Create database and user:**

```bash
sudo -u postgres psql

CREATE DATABASE hoa_prod;
CREATE USER hoa_user WITH PASSWORD 'secure_password';
GRANT ALL PRIVILEGES ON DATABASE hoa_prod TO hoa_user;
\q
```

**3. Configure PostgreSQL for production:**

```bash
sudo nano /etc/postgresql/14/main/postgresql.conf
```

```ini
# Tune for production
shared_buffers = 256MB
effective_cache_size = 1GB
maintenance_work_mem = 64MB
checkpoint_completion_target = 0.9
wal_buffers = 16MB
default_statistics_target = 100
random_page_cost = 1.1
effective_io_concurrency = 200
work_mem = 6MB
min_wal_size = 1GB
max_wal_size = 4GB
```

**4. Restart PostgreSQL:**

```bash
sudo systemctl restart postgresql
```

### Database Migrations

**Initial setup (creates tables):**

```bash
cd /opt/hoa
source .venv/bin/activate
python -c "from hoa.database import init_db; init_db()"
```

**Future migrations** (planned with Alembic):

```bash
# TODO: Add Alembic migration commands
```

---

## SSL/TLS Configuration

### Nginx Reverse Proxy

**1. Install Certbot:**

```bash
sudo apt install certbot python3-certbot-nginx
```

**2. Obtain SSL certificate:**

```bash
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com
```

**3. Configure Nginx:**

```bash
sudo nano /etc/nginx/sites-available/hoa
```

```nginx
# /etc/nginx/sites-available/hoa

upstream hoa_backend {
    server 127.0.0.1:8000;
}

# Redirect HTTP to HTTPS
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;
    return 301 https://$server_name$request_uri;
}

# HTTPS server
server {
    listen 443 ssl http2;
    server_name yourdomain.com www.yourdomain.com;

    # SSL Configuration
    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;

    # Security Headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options DENY always;
    add_header X-Content-Type-Options nosniff always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;

    # Client body size (for file uploads)
    client_max_body_size 10M;

    # Proxy settings
    location / {
        proxy_pass http://hoa_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # WebSocket support (if needed)
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";

        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # Static files (optional, if serving separately)
    location /static/ {
        alias /opt/hoa/hoa/static/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    # Health check endpoint
    location /api/health {
        proxy_pass http://hoa_backend;
        access_log off;
    }
}
```

**4. Enable site and restart Nginx:**

```bash
sudo ln -s /etc/nginx/sites-available/hoa /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

**5. Auto-renewal:**

Certbot automatically sets up renewal. Test it:

```bash
sudo certbot renew --dry-run
```

---

## Monitoring

### Health Checks

```bash
# Basic health check
curl https://yourdomain.com/api/health

# Detailed version info
curl https://yourdomain.com/api/version
```

### Systemd Service Monitoring

```bash
# Check status
sudo systemctl status hoa

# View logs
sudo journalctl -u hoa -f

# Restart service
sudo systemctl restart hoa
```

### Log Monitoring

**Application logs:**

```bash
# Systemd logs
sudo journalctl -u hoa -f

# File logs (if configured)
tail -f /var/log/hoa/hoa.log
```

**Nginx logs:**

```bash
# Access logs
tail -f /var/log/nginx/access.log

# Error logs
tail -f /var/log/nginx/error.log
```

### Monitoring Tools (Optional)

**Prometheus + Grafana:**

```bash
# TODO: Add Prometheus metrics endpoint
# TODO: Add Grafana dashboard
```

**Uptime Monitoring:**

- Use external service like UptimeRobot, Pingdom, or StatusCake
- Monitor `/api/health` endpoint

---

## Backup & Recovery

### Database Backups

**1. Automated backup script:**

```bash
#!/bin/bash
# /opt/hoa/scripts/backup.sh

BACKUP_DIR="/var/backups/hoa"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/hoa_backup_$DATE.sql.gz"

mkdir -p $BACKUP_DIR

# Backup database
pg_dump -U hoa_user hoa_prod | gzip > $BACKUP_FILE

# Keep only last 30 days
find $BACKUP_DIR -name "hoa_backup_*.sql.gz" -mtime +30 -delete

echo "Backup completed: $BACKUP_FILE"
```

**2. Schedule with cron:**

```bash
sudo crontab -e

# Add daily backup at 2 AM
0 2 * * * /opt/hoa/scripts/backup.sh >> /var/log/hoa/backup.log 2>&1
```

**3. Restore from backup:**

```bash
# Restore database
gunzip -c /var/backups/hoa/hoa_backup_YYYYMMDD_HHMMSS.sql.gz | \
  psql -U hoa_user hoa_prod
```

### Config Backups

```bash
# Backup config directory
tar -czf /var/backups/hoa/config_$(date +%Y%m%d).tar.gz ~/.config/hoa/
```

### Application Backups

```bash
# Backup entire application
tar -czf /var/backups/hoa/app_$(date +%Y%m%d).tar.gz /opt/hoa/
```

---

## Security Hardening

### Firewall Configuration

```bash
# Allow SSH, HTTP, HTTPS
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable

# Check status
sudo ufw status
```

### Application Hardening

**1. Secure file permissions:**

```bash
# Application files
sudo chown -R hoa:hoa /opt/hoa
sudo chmod -R 750 /opt/hoa

# Config files
sudo chmod 600 ~/.config/hoa/config.yaml
sudo chmod 600 /opt/hoa/.env.production
```

**2. Database security:**

```bash
# PostgreSQL authentication
sudo nano /etc/postgresql/14/main/pg_hba.conf

# Use password authentication
# local   all   hoa_user   md5
# host    all   hoa_user   127.0.0.1/32   md5
```

**3. Environment variables:**

```bash
# Never commit .env files to git
echo ".env*" >> .gitignore

# Use strong secrets
HOA_SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
```

### Security Best Practices

- ✅ Use HTTPS only (enforce with HSTS header)
- ✅ Set secure cookie flags (HttpOnly, Secure, SameSite)
- ✅ Use strong secret keys (32+ bytes)
- ✅ Enable CORS only for trusted origins
- ✅ Regularly update dependencies
- ✅ Monitor security advisories
- ✅ Use RS256 for JWT (not HS256 in production)
- ✅ Rate limiting (planned feature)
- ✅ Database encryption at rest (if supported)
- ✅ Regular security audits

---

## Troubleshooting

### Service Won't Start

```bash
# Check service status
sudo systemctl status hoa

# Check logs
sudo journalctl -u hoa -n 50

# Common issues:
# - Database connection failed
# - Port already in use
# - Permission denied
```

### Database Connection Errors

```bash
# Test database connection
psql -U hoa_user -h localhost hoa_prod

# Check PostgreSQL is running
sudo systemctl status postgresql

# Check connection string in config
```

### SSL Certificate Issues

```bash
# Test certificate
sudo certbot certificates

# Renew certificate
sudo certbot renew

# Check Nginx config
sudo nginx -t
```

### WebAuthn Not Working

**Common issues:**

- Not using HTTPS (required for production)
- RP ID doesn't match domain
- Origins not whitelisted in config
- Browser doesn't support WebAuthn

**Check configuration:**

```yaml
allowed-rps: yourdomain.com|Your App|https://yourdomain.com
```

### Performance Issues

```bash
# Check system resources
htop
df -h

# Check database performance
sudo -u postgres psql -c "SELECT * FROM pg_stat_activity;"

# Optimize database
sudo -u postgres vacuumdb --analyze --verbose hoa_prod
```

### Logs Show Errors

```bash
# Application logs
sudo journalctl -u hoa --since "1 hour ago"

# Nginx logs
sudo tail -f /var/log/nginx/error.log

# Database logs
sudo tail -f /var/log/postgresql/postgresql-14-main.log
```

---

## Updates and Maintenance

### Updating HOA

```bash
cd /opt/hoa

# Pull latest code
sudo -u hoa git pull origin main

# Update backend dependencies
sudo -u hoa uv sync --frozen

# Rebuild frontend
cd frontend
sudo -u hoa yarn install
sudo -u hoa yarn build
cd ..

# Restart service
sudo systemctl restart hoa

# Verify
curl https://yourdomain.com/api/health
```

### Database Migrations

```bash
# Backup first!
./scripts/backup.sh

# Run migrations (when Alembic is integrated)
# TODO: Add migration commands
```

### Security Updates

```bash
# Update system
sudo apt update && sudo apt upgrade

# Update Python dependencies
cd /opt/hoa
sudo -u hoa uv sync --upgrade

# Update frontend dependencies
cd frontend
sudo -u hoa yarn upgrade
sudo -u hoa yarn build
```

---

## Performance Tuning

### Uvicorn Workers

```bash
# Adjust workers based on CPU cores
--workers 4  # For 4-core server

# Formula: (2 x num_cores) + 1
```

### Database Connection Pooling

**SQLAlchemy configuration** (in `hoa/database.py`):

```python
engine = create_engine(
    DATABASE_URL,
    pool_size=20,           # Number of connections to keep
    max_overflow=10,        # Additional connections if needed
    pool_pre_ping=True,     # Verify connections before use
    pool_recycle=3600,      # Recycle connections after 1 hour
)
```

### Caching (Future Enhancement)

```bash
# Install Redis (for future caching)
sudo apt install redis-server
sudo systemctl enable redis-server
sudo systemctl start redis-server
```

---

## Additional Resources

- [API Reference](api.md)
- [Development Guide](development.md)
- [Architecture Documentation](../AGENTS.md)
- [FastAPI Deployment](https://fastapi.tiangolo.com/deployment/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [Nginx Documentation](https://nginx.org/en/docs/)

---

**Deployment Complete! 🚀**
