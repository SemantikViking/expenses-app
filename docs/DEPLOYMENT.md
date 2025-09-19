# Deployment Guide

This guide covers various deployment options for the Receipt Processor application.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Local Development](#local-development)
- [Production Deployment](#production-deployment)
- [Docker Deployment](#docker-deployment)
- [Cloud Deployment](#cloud-deployment)
- [Monitoring and Maintenance](#monitoring-and-maintenance)

## Prerequisites

### System Requirements

**Minimum Requirements:**
- Python 3.8 or higher
- 2GB RAM
- 1GB disk space
- Internet connection for AI services

**Recommended Requirements:**
- Python 3.11 or higher
- 4GB RAM
- 10GB disk space
- SSD storage
- Stable internet connection

### Dependencies

- Git
- Python virtual environment
- Docker (for containerized deployment)
- Nginx (for production web server)

## Local Development

### 1. Clone Repository

```bash
git clone https://github.com/receipt-processor/receipt-processor.git
cd receipt-processor
```

### 2. Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -e ".[dev]"
```

### 4. Configure Environment

```bash
cp .env.example .env
# Edit .env with your configuration
```

### 5. Run Application

```bash
# Start development server
make dev

# Or run directly
receipt-processor --help
```

## Production Deployment

### 1. System Setup

**Ubuntu/Debian:**
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python and dependencies
sudo apt install python3.11 python3.11-venv python3-pip git nginx -y

# Create application user
sudo useradd -m -s /bin/bash receipt-processor
sudo usermod -aG www-data receipt-processor
```

**CentOS/RHEL:**
```bash
# Update system
sudo yum update -y

# Install Python and dependencies
sudo yum install python311 python311-pip git nginx -y

# Create application user
sudo useradd -m -s /bin/bash receipt-processor
sudo usermod -aG nginx receipt-processor
```

### 2. Application Installation

```bash
# Switch to application user
sudo su - receipt-processor

# Clone repository
git clone https://github.com/receipt-processor/receipt-processor.git
cd receipt-processor

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Install application
pip install -e ".[prod]"

# Create directories
mkdir -p data logs config screenshots
```

### 3. Configuration

```bash
# Copy configuration
cp .env.example .env

# Edit configuration
nano .env
```

**Production Configuration:**
```env
# Environment
RECEIPT_PROCESSOR_ENV=production
LOG_LEVEL=INFO

# AI Configuration
AI_PROVIDER=openai
OPENAI_API_KEY=your_openai_api_key
CONFIDENCE_THRESHOLD=0.8

# Storage Configuration
DATA_DIR=/home/receipt-processor/data
LOG_DIR=/home/receipt-processor/logs
SCREENSHOT_DIR=/home/receipt-processor/screenshots

# Email Configuration
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your_email@gmail.com
SMTP_PASSWORD=your_app_password

# Security
SECRET_KEY=your_secret_key_here
```

### 4. System Service

Create systemd service file:

```bash
sudo nano /etc/systemd/system/receipt-processor.service
```

**Service Configuration:**
```ini
[Unit]
Description=Receipt Processor Service
After=network.target

[Service]
Type=simple
User=receipt-processor
Group=receipt-processor
WorkingDirectory=/home/receipt-processor/receipt-processor
Environment=PATH=/home/receipt-processor/receipt-processor/venv/bin
ExecStart=/home/receipt-processor/receipt-processor/venv/bin/receipt-processor daemon start
ExecStop=/home/receipt-processor/receipt-processor/venv/bin/receipt-processor daemon stop
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**Enable and Start Service:**
```bash
sudo systemctl daemon-reload
sudo systemctl enable receipt-processor
sudo systemctl start receipt-processor
sudo systemctl status receipt-processor
```

### 5. Nginx Configuration

```bash
sudo nano /etc/nginx/sites-available/receipt-processor
```

**Nginx Configuration:**
```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static/ {
        alias /home/receipt-processor/receipt-processor/static/;
    }

    location /media/ {
        alias /home/receipt-processor/receipt-processor/media/;
    }
}
```

**Enable Site:**
```bash
sudo ln -s /etc/nginx/sites-available/receipt-processor /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

## Docker Deployment

### 1. Using Docker Compose

**Create docker-compose.yml:**
```yaml
version: '3.8'

services:
  receipt-processor:
    image: receipt-processor:latest
    container_name: receipt-processor
    restart: unless-stopped
    environment:
      - RECEIPT_PROCESSOR_ENV=production
      - OPENAI_API_KEY=your_openai_api_key
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
      - ./config:/app/config
      - ./screenshots:/app/screenshots
    ports:
      - "8000:8000"
    healthcheck:
      test: ["CMD", "receipt-processor", "health"]
      interval: 30s
      timeout: 10s
      retries: 3

  nginx:
    image: nginx:alpine
    container_name: receipt-processor-nginx
    restart: unless-stopped
    ports:
      - "80:80"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
    depends_on:
      - receipt-processor
```

**Deploy:**
```bash
# Build and start services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### 2. Using Docker Run

```bash
# Build image
docker build -t receipt-processor .

# Run container
docker run -d \
  --name receipt-processor \
  -p 8000:8000 \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/logs:/app/logs \
  -v $(pwd)/screenshots:/app/screenshots \
  -e OPENAI_API_KEY=your_openai_api_key \
  receipt-processor
```

## Cloud Deployment

### 1. AWS Deployment

**Using EC2:**
```bash
# Launch EC2 instance (Ubuntu 22.04 LTS)
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker ubuntu

# Clone and deploy
git clone https://github.com/receipt-processor/receipt-processor.git
cd receipt-processor
docker-compose up -d
```

**Using ECS:**
```yaml
# task-definition.json
{
  "family": "receipt-processor",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "256",
  "memory": "512",
  "executionRoleArn": "arn:aws:iam::account:role/ecsTaskExecutionRole",
  "containerDefinitions": [
    {
      "name": "receipt-processor",
      "image": "receipt-processor:latest",
      "portMappings": [
        {
          "containerPort": 8000,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {
          "name": "RECEIPT_PROCESSOR_ENV",
          "value": "production"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/receipt-processor",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "ecs"
        }
      }
    }
  ]
}
```

### 2. Google Cloud Deployment

**Using Cloud Run:**
```bash
# Build and push to Container Registry
gcloud builds submit --tag gcr.io/PROJECT_ID/receipt-processor

# Deploy to Cloud Run
gcloud run deploy receipt-processor \
  --image gcr.io/PROJECT_ID/receipt-processor \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated
```

### 3. Azure Deployment

**Using Container Instances:**
```bash
# Create resource group
az group create --name receipt-processor-rg --location eastus

# Deploy container
az container create \
  --resource-group receipt-processor-rg \
  --name receipt-processor \
  --image receipt-processor:latest \
  --dns-name-label receipt-processor \
  --ports 8000
```

## Monitoring and Maintenance

### 1. Health Monitoring

**Health Check Endpoint:**
```bash
curl http://localhost:8000/health
```

**System Monitoring:**
```bash
# Check service status
sudo systemctl status receipt-processor

# View logs
sudo journalctl -u receipt-processor -f

# Check resource usage
htop
```

### 2. Log Management

**Log Rotation:**
```bash
# Configure logrotate
sudo nano /etc/logrotate.d/receipt-processor
```

**Logrotate Configuration:**
```
/home/receipt-processor/logs/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 receipt-processor receipt-processor
    postrotate
        systemctl reload receipt-processor
    endscript
}
```

### 3. Backup Strategy

**Database Backup:**
```bash
# Create backup script
nano backup.sh
```

**Backup Script:**
```bash
#!/bin/bash
BACKUP_DIR="/backup/receipt-processor"
DATE=$(date +%Y%m%d_%H%M%S)

# Create backup directory
mkdir -p $BACKUP_DIR

# Backup data
tar -czf $BACKUP_DIR/data_$DATE.tar.gz /home/receipt-processor/data

# Backup logs
tar -czf $BACKUP_DIR/logs_$DATE.tar.gz /home/receipt-processor/logs

# Clean old backups (keep 30 days)
find $BACKUP_DIR -name "*.tar.gz" -mtime +30 -delete
```

**Schedule Backup:**
```bash
# Add to crontab
crontab -e

# Add this line for daily backup at 2 AM
0 2 * * * /home/receipt-processor/backup.sh
```

### 4. Updates and Maintenance

**Update Application:**
```bash
# Switch to application user
sudo su - receipt-processor

# Navigate to application directory
cd receipt-processor

# Pull latest changes
git pull origin main

# Activate virtual environment
source venv/bin/activate

# Update dependencies
pip install -e ".[prod]"

# Restart service
sudo systemctl restart receipt-processor
```

**Rollback:**
```bash
# Check git log
git log --oneline

# Rollback to previous version
git checkout <commit-hash>

# Restart service
sudo systemctl restart receipt-processor
```

### 5. Security Considerations

**Firewall Configuration:**
```bash
# Configure UFW
sudo ufw enable
sudo ufw allow ssh
sudo ufw allow 80
sudo ufw allow 443
sudo ufw deny 8000  # Block direct access to app port
```

**SSL/TLS Configuration:**
```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx -y

# Obtain SSL certificate
sudo certbot --nginx -d your-domain.com

# Auto-renewal
sudo crontab -e
# Add: 0 12 * * * /usr/bin/certbot renew --quiet
```

**Security Headers:**
```nginx
# Add to nginx configuration
add_header X-Frame-Options DENY;
add_header X-Content-Type-Options nosniff;
add_header X-XSS-Protection "1; mode=block";
add_header Strict-Transport-Security "max-age=31536000; includeSubDomains";
```

## Troubleshooting

### Common Issues

**Service Won't Start:**
```bash
# Check logs
sudo journalctl -u receipt-processor -f

# Check configuration
receipt-processor config validate

# Test manually
receipt-processor --help
```

**Permission Issues:**
```bash
# Fix ownership
sudo chown -R receipt-processor:receipt-processor /home/receipt-processor

# Fix permissions
chmod 755 /home/receipt-processor
chmod 644 /home/receipt-processor/.env
```

**Port Already in Use:**
```bash
# Find process using port
sudo lsof -i :8000

# Kill process
sudo kill -9 <PID>
```

### Performance Optimization

**Resource Limits:**
```bash
# Set memory limits
echo "vm.max_map_count=262144" | sudo tee -a /etc/sysctl.conf
sudo sysctl -p
```

**Database Optimization:**
```bash
# Optimize SQLite (if using)
sqlite3 data/receipts.db "VACUUM; ANALYZE;"
```

This deployment guide provides comprehensive instructions for deploying the Receipt Processor application in various environments. Choose the deployment method that best fits your needs and infrastructure.
