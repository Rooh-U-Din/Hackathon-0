#!/bin/bash
set -e

# AI Employee Cloud Deployment Script
# Automates deployment on Oracle Cloud Free Tier VM

echo "╔════════════════════════════════════════════════════════════╗"
echo "║     AI Employee - Platinum Tier Cloud Deployment          ║"
echo "║     Cloud-Local Hybrid Architecture                        ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
REPO_URL="${REPO_URL:-git@github.com:YOUR_USERNAME/Hackathon-0.git}"
VAULT_REMOTE="${VAULT_REMOTE:-git@github.com:YOUR_USERNAME/ai-employee-vault.git}"
INSTALL_DIR="/home/ubuntu/Hackathon-0"
VAULT_DIR="/home/ubuntu/AI_Employee_Vault"
VENV_DIR="$INSTALL_DIR/venv"

# Functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_root() {
    if [ "$EUID" -eq 0 ]; then
        log_error "Please do not run this script as root"
        exit 1
    fi
}

check_os() {
    if [ ! -f /etc/os-release ]; then
        log_error "Cannot detect OS"
        exit 1
    fi

    . /etc/os-release
    if [ "$ID" != "ubuntu" ]; then
        log_error "This script is designed for Ubuntu"
        exit 1
    fi

    log_info "Detected: $PRETTY_NAME"
}

install_dependencies() {
    log_info "Installing system dependencies..."

    sudo apt update
    sudo apt install -y \
        git \
        python3 \
        python3-pip \
        python3-venv \
        docker.io \
        docker-compose \
        nginx \
        certbot \
        python3-certbot-nginx \
        ufw \
        fail2ban

    log_info "Dependencies installed"
}

configure_docker() {
    log_info "Configuring Docker..."

    # Add user to docker group
    sudo usermod -aG docker $USER

    # Enable and start Docker
    sudo systemctl enable docker
    sudo systemctl start docker

    log_info "Docker configured"
}

configure_firewall() {
    log_info "Configuring firewall..."

    # Allow SSH, HTTP, HTTPS, Odoo
    sudo ufw allow 22/tcp
    sudo ufw allow 80/tcp
    sudo ufw allow 443/tcp
    sudo ufw allow 8069/tcp

    # Enable firewall
    sudo ufw --force enable

    log_info "Firewall configured"
}

clone_repository() {
    log_info "Cloning repository..."

    if [ -d "$INSTALL_DIR" ]; then
        log_warn "Repository already exists, pulling latest changes"
        cd "$INSTALL_DIR"
        git pull
    else
        git clone "$REPO_URL" "$INSTALL_DIR"
    fi

    log_info "Repository cloned"
}

clone_vault() {
    log_info "Cloning vault repository..."

    if [ -d "$VAULT_DIR" ]; then
        log_warn "Vault already exists, pulling latest changes"
        cd "$VAULT_DIR"
        git pull
    else
        git clone "$VAULT_REMOTE" "$VAULT_DIR"
    fi

    log_info "Vault cloned"
}

setup_python_env() {
    log_info "Setting up Python environment..."

    cd "$INSTALL_DIR"

    # Create virtual environment
    python3 -m venv "$VENV_DIR"

    # Activate and install dependencies
    source "$VENV_DIR/bin/activate"
    pip install --upgrade pip

    if [ -f requirements.txt ]; then
        pip install -r requirements.txt
    else
        log_warn "requirements.txt not found, skipping Python dependencies"
    fi

    log_info "Python environment ready"
}

setup_cloud_agent() {
    log_info "Setting up cloud agent..."

    cd "$INSTALL_DIR/platinum/cloud-agent"

    # Create .env if it doesn't exist
    if [ ! -f .env ]; then
        cat > .env << EOF
# Agent Configuration
AGENT_MODE=cloud
VAULT_PATH=$VAULT_DIR
CHECK_INTERVAL=60

# Odoo Configuration (Read-Only)
ODOO_URL=http://localhost:8069
ODOO_DB=odoo
ODOO_USERNAME=cloud_readonly
ODOO_PASSWORD=readonly_password_change_me

# Vault Sync
VAULT_SYNC_REMOTE=$VAULT_REMOTE
VAULT_SYNC_INTERVAL=300
EOF
        log_warn "Created .env file - PLEASE UPDATE WITH REAL CREDENTIALS"
    fi

    log_info "Cloud agent configured"
}

setup_vault_sync() {
    log_info "Setting up vault sync..."

    cd "$INSTALL_DIR/platinum/vault-sync"

    # Create .env if it doesn't exist
    if [ ! -f .env ]; then
        cat > .env << EOF
VAULT_PATH=$VAULT_DIR
VAULT_REMOTE=$VAULT_REMOTE
VAULT_BRANCH=main
SYNC_INTERVAL=300
EOF
    fi

    log_info "Vault sync configured"
}

deploy_odoo() {
    log_info "Deploying Odoo..."

    cd "$INSTALL_DIR/platinum/deployment"

    # Create .env for docker-compose if it doesn't exist
    if [ ! -f .env ]; then
        cat > .env << EOF
POSTGRES_PASSWORD=$(openssl rand -base64 32)
EOF
    fi

    # Start Odoo
    docker-compose up -d

    # Wait for Odoo to be ready
    log_info "Waiting for Odoo to start (this may take 2-3 minutes)..."
    sleep 60

    # Check if Odoo is running
    if docker-compose ps | grep -q "Up"; then
        log_info "Odoo is running"
    else
        log_error "Odoo failed to start"
        docker-compose logs odoo
        exit 1
    fi

    log_info "Odoo deployed"
}

install_systemd_services() {
    log_info "Installing systemd services..."

    # Install cloud-agent service
    sudo cp "$INSTALL_DIR/platinum/deployment/systemd/cloud-agent.service" /etc/systemd/system/

    # Install vault-sync service
    sudo cp "$INSTALL_DIR/platinum/deployment/systemd/vault-sync.service" /etc/systemd/system/

    # Reload systemd
    sudo systemctl daemon-reload

    log_info "Systemd services installed"
}

start_services() {
    log_info "Starting services..."

    # Enable services
    sudo systemctl enable cloud-agent
    sudo systemctl enable vault-sync

    # Start services
    sudo systemctl start cloud-agent
    sudo systemctl start vault-sync

    # Check status
    sleep 5

    if sudo systemctl is-active --quiet cloud-agent; then
        log_info "Cloud agent is running"
    else
        log_error "Cloud agent failed to start"
        sudo journalctl -u cloud-agent -n 20
    fi

    if sudo systemctl is-active --quiet vault-sync; then
        log_info "Vault sync is running"
    else
        log_error "Vault sync failed to start"
        sudo journalctl -u vault-sync -n 20
    fi

    log_info "Services started"
}

setup_nginx() {
    log_info "Setting up Nginx reverse proxy..."

    # Create Nginx config
    sudo tee /etc/nginx/sites-available/odoo > /dev/null << 'EOF'
server {
    listen 80;
    server_name _;

    location / {
        proxy_pass http://localhost:8069;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # WebSocket support
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";

        # Timeouts
        proxy_connect_timeout 300s;
        proxy_send_timeout 300s;
        proxy_read_timeout 300s;
    }
}
EOF

    # Enable site
    sudo ln -sf /etc/nginx/sites-available/odoo /etc/nginx/sites-enabled/
    sudo rm -f /etc/nginx/sites-enabled/default

    # Test and reload Nginx
    sudo nginx -t
    sudo systemctl restart nginx

    log_info "Nginx configured"
}

create_health_check() {
    log_info "Creating health check script..."

    cat > /home/ubuntu/health-check.sh << 'EOF'
#!/bin/bash

# Check cloud agent
if ! systemctl is-active --quiet cloud-agent; then
    echo "$(date): Cloud agent is down, restarting..."
    sudo systemctl restart cloud-agent
fi

# Check vault sync
if ! systemctl is-active --quiet vault-sync; then
    echo "$(date): Vault sync is down, restarting..."
    sudo systemctl restart vault-sync
fi

# Check Odoo
if ! docker ps | grep -q odoo-app; then
    echo "$(date): Odoo is down, restarting..."
    cd /home/ubuntu/Hackathon-0/platinum/deployment
    docker-compose restart odoo
fi

echo "$(date): Health check complete"
EOF

    chmod +x /home/ubuntu/health-check.sh

    # Add to crontab
    (crontab -l 2>/dev/null; echo "*/5 * * * * /home/ubuntu/health-check.sh >> /home/ubuntu/health-check.log 2>&1") | crontab -

    log_info "Health check configured"
}

print_summary() {
    echo ""
    echo "╔════════════════════════════════════════════════════════════╗"
    echo "║              Deployment Complete!                          ║"
    echo "╚════════════════════════════════════════════════════════════╝"
    echo ""
    echo "Services Status:"
    echo "  • Cloud Agent:  $(sudo systemctl is-active cloud-agent)"
    echo "  • Vault Sync:   $(sudo systemctl is-active vault-sync)"
    echo "  • Odoo:         $(docker ps --filter name=odoo-app --format '{{.Status}}' | cut -d' ' -f1)"
    echo ""
    echo "Access Points:"
    echo "  • Odoo: http://$(curl -s ifconfig.me):8069"
    echo ""
    echo "Next Steps:"
    echo "  1. Configure Odoo database at http://$(curl -s ifconfig.me):8069"
    echo "  2. Create read-only user 'cloud_readonly' in Odoo"
    echo "  3. Update credentials in:"
    echo "     - $INSTALL_DIR/platinum/cloud-agent/.env"
    echo "  4. Restart cloud agent: sudo systemctl restart cloud-agent"
    echo "  5. (Optional) Set up HTTPS with: sudo certbot --nginx"
    echo ""
    echo "Monitoring:"
    echo "  • Cloud agent logs: sudo journalctl -u cloud-agent -f"
    echo "  • Vault sync logs:  sudo journalctl -u vault-sync -f"
    echo "  • Odoo logs:        docker-compose logs -f odoo"
    echo "  • Health check:     tail -f /home/ubuntu/health-check.log"
    echo ""
    echo "Documentation:"
    echo "  • Cloud Deployment: $INSTALL_DIR/CLOUD_DEPLOYMENT_GUIDE.md"
    echo "  • Vault Sync:       $INSTALL_DIR/VAULT_SYNC_GUIDE.md"
    echo "  • Security:         $INSTALL_DIR/SECURITY_ARCHITECTURE.md"
    echo ""
}

# Main execution
main() {
    log_info "Starting deployment..."

    check_root
    check_os
    install_dependencies
    configure_docker
    configure_firewall
    clone_repository
    clone_vault
    setup_python_env
    setup_cloud_agent
    setup_vault_sync
    deploy_odoo
    install_systemd_services
    start_services
    setup_nginx
    create_health_check
    print_summary

    log_info "Deployment complete!"
}

# Run main
main
