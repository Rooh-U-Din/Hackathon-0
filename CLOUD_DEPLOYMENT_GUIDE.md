# Cloud Deployment Guide - Platinum Tier

## Overview

This guide walks through deploying the Personal AI Employee cloud agent on Oracle Cloud Free Tier VM for 24/7 operation.

---

## Prerequisites

### Required Accounts

1. **Oracle Cloud Account** (Free Tier)
   - Sign up at: https://www.oracle.com/cloud/free/
   - Free tier includes: Always Free VM, 50GB storage, 10TB bandwidth

2. **GitHub Account**
   - For vault synchronization
   - Create private repository for vault

3. **Domain Name** (Optional)
   - For HTTPS access to Odoo
   - Can use Let's Encrypt for free SSL

### Local Requirements

- SSH client
- Git installed
- Basic Linux knowledge

---

## Step 1: Create Oracle Cloud VM

### 1.1 Create VM Instance

1. Log in to Oracle Cloud Console
2. Navigate to: Compute → Instances → Create Instance

**Configuration:**
- **Name**: ai-employee-cloud
- **Image**: Ubuntu 22.04 LTS
- **Shape**: VM.Standard.E2.1.Micro (Always Free)
- **Boot Volume**: 50GB
- **Network**: Create new VCN or use existing
- **SSH Keys**: Upload your public key

3. Click "Create" and wait for provisioning (~2 minutes)

### 1.2 Configure Firewall

**Ingress Rules:**
```
Port 22   (SSH)
Port 80   (HTTP)
Port 443  (HTTPS)
Port 8069 (Odoo - optional, for remote access)
```

**In Oracle Console:**
1. Navigate to: Networking → Virtual Cloud Networks
2. Select your VCN → Security Lists → Default Security List
3. Add Ingress Rules for ports above

**On VM (UFW):**
```bash
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw allow 8069/tcp
sudo ufw enable
```

---

## Step 2: Initial VM Setup

### 2.1 Connect to VM

```bash
ssh ubuntu@<VM_PUBLIC_IP>
```

### 2.2 Update System

```bash
sudo apt update
sudo apt upgrade -y
sudo apt install -y git python3 python3-pip python3-venv nodejs npm docker.io docker-compose
```

### 2.3 Configure Docker

```bash
sudo usermod -aG docker ubuntu
sudo systemctl enable docker
sudo systemctl start docker

# Log out and back in for group changes
exit
ssh ubuntu@<VM_PUBLIC_IP>
```

---

## Step 3: Clone Repository

### 3.1 Set Up SSH Key for GitHub

```bash
# Generate SSH key
ssh-keygen -t ed25519 -C "cloud-agent@ai-employee"

# Display public key
cat ~/.ssh/id_ed25519.pub

# Add this key to GitHub: Settings → SSH and GPG keys → New SSH key
```

### 3.2 Clone Repository

```bash
cd ~
git clone git@github.com:YOUR_USERNAME/Hackathon-0.git
cd Hackathon-0
```

---

## Step 4: Set Up Vault Synchronization

### 4.1 Create Vault Repository

**On GitHub:**
1. Create new private repository: `ai-employee-vault`
2. Initialize with README

**On Cloud VM:**
```bash
# Clone vault repository
cd ~
git clone git@github.com:YOUR_USERNAME/ai-employee-vault.git AI_Employee_Vault

# Copy vault structure from main repo
cp -r ~/Hackathon-0/AI_Employee_Vault/* ~/AI_Employee_Vault/

# Initial commit
cd ~/AI_Employee_Vault
git add .
git commit -m "Initial vault structure"
git push origin main
```

### 4.2 Configure Vault Sync

```bash
cd ~/Hackathon-0/platinum/vault-sync

# Create environment file
cat > .env << 'EOF'
VAULT_PATH=/home/ubuntu/AI_Employee_Vault
VAULT_REMOTE=git@github.com:YOUR_USERNAME/ai-employee-vault.git
VAULT_BRANCH=main
SYNC_INTERVAL=300
EOF

# Test sync
python3 vault_sync.py --vault ~/AI_Employee_Vault --remote git@github.com:YOUR_USERNAME/ai-employee-vault.git --operation sync
```

---

## Step 5: Deploy Odoo Community Edition

### 5.1 Create Docker Compose File

```bash
cd ~/Hackathon-0/platinum/deployment

cat > docker-compose.yml << 'EOF'
version: '3.8'

services:
  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: odoo
      POSTGRES_USER: odoo
      POSTGRES_PASSWORD: odoo_password
    volumes:
      - odoo-db-data:/var/lib/postgresql/data
    restart: always

  odoo:
    image: odoo:19
    depends_on:
      - postgres
    ports:
      - "8069:8069"
    environment:
      HOST: postgres
      USER: odoo
      PASSWORD: odoo_password
    volumes:
      - odoo-data:/var/lib/odoo
      - odoo-config:/etc/odoo
    restart: always

volumes:
  odoo-db-data:
  odoo-data:
  odoo-config:
EOF
```

### 5.2 Start Odoo

```bash
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f odoo
```

### 5.3 Configure Odoo

1. Open browser: `http://<VM_PUBLIC_IP>:8069`
2. Create database: `odoo`
3. Install "Accounting" module
4. Create read-only user for cloud agent:
   - Username: `cloud_readonly`
   - Password: `secure_password`
   - Access Rights: Accounting / User (read-only)

---

## Step 6: Configure Cloud Agent

### 6.1 Install Python Dependencies

```bash
cd ~/Hackathon-0
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 6.2 Create Environment File

```bash
cd ~/Hackathon-0/platinum/cloud-agent

cat > .env << 'EOF'
# Agent Configuration
AGENT_MODE=cloud
VAULT_PATH=/home/ubuntu/AI_Employee_Vault
CHECK_INTERVAL=60

# Odoo Configuration (Read-Only)
ODOO_URL=http://localhost:8069
ODOO_DB=odoo
ODOO_USERNAME=cloud_readonly
ODOO_PASSWORD=secure_password

# Vault Sync
VAULT_SYNC_REMOTE=git@github.com:YOUR_USERNAME/ai-employee-vault.git
VAULT_SYNC_INTERVAL=300
EOF
```

### 6.3 Test Cloud Agent

```bash
source ~/Hackathon-0/venv/bin/activate
python3 cloud_agent.py --vault ~/AI_Employee_Vault
```

Press Ctrl+C after verifying it starts correctly.

---

## Step 7: Create Systemd Services

### 7.1 Cloud Agent Service

```bash
sudo tee /etc/systemd/system/cloud-agent.service << 'EOF'
[Unit]
Description=AI Employee Cloud Agent
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/Hackathon-0/platinum/cloud-agent
Environment="PATH=/home/ubuntu/Hackathon-0/venv/bin"
ExecStart=/home/ubuntu/Hackathon-0/venv/bin/python3 cloud_agent.py --vault /home/ubuntu/AI_Employee_Vault
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF
```

### 7.2 Vault Sync Service

```bash
sudo tee /etc/systemd/system/vault-sync.service << 'EOF'
[Unit]
Description=AI Employee Vault Sync
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/Hackathon-0/platinum/vault-sync
Environment="PATH=/home/ubuntu/Hackathon-0/venv/bin"
ExecStart=/home/ubuntu/Hackathon-0/venv/bin/python3 vault_sync.py --vault /home/ubuntu/AI_Employee_Vault --remote git@github.com:YOUR_USERNAME/ai-employee-vault.git --continuous --interval 300
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF
```

### 7.3 Enable and Start Services

```bash
# Reload systemd
sudo systemctl daemon-reload

# Enable services (start on boot)
sudo systemctl enable cloud-agent
sudo systemctl enable vault-sync

# Start services
sudo systemctl start cloud-agent
sudo systemctl start vault-sync

# Check status
sudo systemctl status cloud-agent
sudo systemctl status vault-sync

# View logs
sudo journalctl -u cloud-agent -f
sudo journalctl -u vault-sync -f
```

---

## Step 8: Configure HTTPS (Optional)

### 8.1 Install Nginx and Certbot

```bash
sudo apt install -y nginx certbot python3-certbot-nginx
```

### 8.2 Configure Nginx for Odoo

```bash
sudo tee /etc/nginx/sites-available/odoo << 'EOF'
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:8069;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
EOF

sudo ln -s /etc/nginx/sites-available/odoo /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### 8.3 Get SSL Certificate

```bash
sudo certbot --nginx -d your-domain.com
```

---

## Step 9: Health Monitoring

### 9.1 Create Health Check Script

```bash
cat > ~/health-check.sh << 'EOF'
#!/bin/bash

# Check cloud agent
if ! systemctl is-active --quiet cloud-agent; then
    echo "Cloud agent is down, restarting..."
    sudo systemctl restart cloud-agent
fi

# Check vault sync
if ! systemctl is-active --quiet vault-sync; then
    echo "Vault sync is down, restarting..."
    sudo systemctl restart vault-sync
fi

# Check Odoo
if ! docker ps | grep -q odoo; then
    echo "Odoo is down, restarting..."
    cd ~/Hackathon-0/platinum/deployment
    docker-compose restart odoo
fi

echo "Health check complete: $(date)"
EOF

chmod +x ~/health-check.sh
```

### 9.2 Add to Crontab

```bash
crontab -e

# Add this line:
*/5 * * * * /home/ubuntu/health-check.sh >> /home/ubuntu/health-check.log 2>&1
```

---

## Step 10: Local Machine Setup

### 10.1 Clone Vault Repository

```bash
# On your local machine
cd ~/
git clone git@github.com:YOUR_USERNAME/ai-employee-vault.git AI_Employee_Vault
```

### 10.2 Configure Local Agent

```bash
cd ~/Hackathon-0/platinum/local-agent

cat > .env << 'EOF'
# Agent Configuration
AGENT_MODE=local
VAULT_PATH=/home/YOUR_USERNAME/AI_Employee_Vault

# Odoo Configuration (Full Access)
ODOO_URL=http://<CLOUD_VM_IP>:8069
ODOO_DB=odoo
ODOO_USERNAME=admin
ODOO_PASSWORD=admin_password

# WhatsApp Session (Local Only)
WHATSAPP_SESSION_PATH=./whatsapp_session

# Payment Credentials (Local Only)
PAYMENT_API_KEY=your_key_here
EOF
```

### 10.3 Set Up Periodic Sync

```bash
# Add to crontab
crontab -e

# Pull vault changes every 5 minutes
*/5 * * * * cd ~/AI_Employee_Vault && git pull --rebase

# Run local agent every 15 minutes
*/15 * * * * cd ~/Hackathon-0 && python3 platinum/local-agent/local_agent.py --once
```

---

## Step 11: Test End-to-End

### 11.1 Run Platinum Demo

```bash
# On local machine
python3 platinum/demo/platinum_demo.py --vault ~/AI_Employee_Vault
```

### 11.2 Verify Cloud Operation

```bash
# On cloud VM
sudo journalctl -u cloud-agent -n 50

# Check vault sync
sudo journalctl -u vault-sync -n 50

# Check Odoo
docker-compose logs odoo --tail=50
```

---

## Troubleshooting

### Cloud Agent Not Starting

```bash
# Check logs
sudo journalctl -u cloud-agent -xe

# Test manually
cd ~/Hackathon-0/platinum/cloud-agent
source ~/Hackathon-0/venv/bin/activate
python3 cloud_agent.py --vault ~/AI_Employee_Vault
```

### Vault Sync Conflicts

```bash
cd ~/AI_Employee_Vault
git status
git rebase --abort
git pull --rebase
```

### Odoo Connection Failed

```bash
# Check Odoo is running
docker-compose ps

# Check logs
docker-compose logs odoo

# Restart Odoo
docker-compose restart odoo
```

### High Memory Usage

```bash
# Check memory
free -h

# Restart services
sudo systemctl restart cloud-agent
docker-compose restart
```

---

## Maintenance

### Daily Tasks

- Check service status: `sudo systemctl status cloud-agent vault-sync`
- Review logs: `sudo journalctl -u cloud-agent -since today`
- Monitor disk space: `df -h`

### Weekly Tasks

- Review audit logs
- Check for system updates: `sudo apt update && sudo apt upgrade`
- Backup Odoo database: `docker-compose exec postgres pg_dump odoo > backup.sql`

### Monthly Tasks

- Rotate logs: `sudo journalctl --vacuum-time=30d`
- Review and optimize vault size
- Update dependencies: `pip install --upgrade -r requirements.txt`

---

## Cost Optimization

### Oracle Cloud Free Tier Limits

- **Compute**: 2 VMs (ARM or x86)
- **Storage**: 200GB total
- **Bandwidth**: 10TB/month outbound
- **Always Free**: No expiration

### Staying Within Limits

- Use single VM for all services
- Monitor bandwidth usage
- Compress logs regularly
- Use efficient sync intervals

---

## Security Best Practices

1. **SSH Key Only**: Disable password authentication
2. **Firewall**: Only open required ports
3. **Updates**: Keep system updated
4. **Secrets**: Never commit to git
5. **Backups**: Regular Odoo database backups
6. **Monitoring**: Set up alerts for failures

---

## Next Steps

After successful deployment:

1. Monitor for 24 hours to ensure stability
2. Test offline handling (turn off local machine)
3. Verify approvals work when local returns
4. Set up additional monitoring (optional)
5. Configure backup automation

---

**Cloud Deployment Complete!**

Your AI Employee is now running 24/7 on the cloud, ready to handle tasks even when your local machine is offline.
