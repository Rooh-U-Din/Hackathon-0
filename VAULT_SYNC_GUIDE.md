# Vault Synchronization Guide - Platinum Tier

## Overview

The vault synchronization system enables cloud-local coordination by keeping the AI_Employee_Vault in sync between your cloud VM and local machine using Git as the transport layer.

---

## Architecture

### Synchronization Flow

```
┌─────────────────────────────────────────────────────────────┐
│                    CLOUD VM (24/7)                          │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Cloud Agent                                         │  │
│  │  - Writes to /Updates/                               │  │
│  │  - Creates approval requests in /Pending_Approval/   │  │
│  │  - Moves tasks to /In_Progress/cloud/               │  │
│  └──────────────────────────────────────────────────────┘  │
│                           ↓                                 │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Vault Sync (every 5 minutes)                        │  │
│  │  - git pull --rebase                                 │  │
│  │  - git add tracked files                             │  │
│  │  - git commit                                        │  │
│  │  - git push                                          │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                           ↕
                    GitHub Repository
                    (Private, Encrypted)
                           ↕
┌─────────────────────────────────────────────────────────────┐
│                  LOCAL MACHINE (On-Demand)                  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Vault Sync (every 5 minutes)                        │  │
│  │  - git pull --rebase                                 │  │
│  │  - git add tracked files                             │  │
│  │  - git commit                                        │  │
│  │  - git push                                          │  │
│  └──────────────────────────────────────────────────────┘  │
│                           ↓                                 │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Local Agent                                         │  │
│  │  - Processes /Approved/ and /Rejected/               │  │
│  │  - Merges /Updates/ into Dashboard.md                │  │
│  │  - Executes approved actions via MCP                 │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

---

## Security Boundaries

### What Gets Synced

**Synced to Cloud:**
- Markdown files (*.md)
- Task files in /Inbox, /Needs_Action, /In_Progress
- Approval requests in /Pending_Approval, /Approved, /Rejected
- Completed tasks in /Done
- Logs in /Logs (activity logs, not secrets)
- Dashboard updates in /Updates

### What NEVER Gets Synced

**Excluded from Cloud (via .gitignore):**

```gitignore
# Secrets and credentials
.env
*.env
credentials.json
token.json
*.key
*.pem
*.p12
*.pfx

# Session files (local only)
*_session/
whatsapp_session/
linkedin_session/
twitter_session/
facebook_session/
instagram_session/

# Processed IDs (environment-specific)
.gmail_processed_ids.json
.linkedin_processed_ids.json
.twitter_processed_ids.json
.facebook_processed_ids.json
.instagram_processed_ids.json

# API keys and tokens
*_api_key.txt
*_token.txt
*_secret.txt

# Database files
*.db
*.sqlite
*.sqlite3

# Certificates
*.crt
*.cer

# Private keys
id_rsa
id_ed25519
*.ppk
```

---

## Setup Instructions

### 1. Create Private Vault Repository

**On GitHub:**

```bash
# Create new private repository
# Name: ai-employee-vault
# Visibility: Private
# Initialize: No (we'll push existing vault)
```

**Initialize Local Vault:**

```bash
cd ~/AI_Employee_Vault

# Initialize git
git init

# Add remote
git remote add origin git@github.com:YOUR_USERNAME/ai-employee-vault.git

# Create .gitignore
cat > .gitignore << 'EOF'
# Secrets and credentials
.env
*.env
credentials.json
token.json
*.key
*.pem

# Session files
*_session/
whatsapp_session/

# Processed IDs
.*_processed_ids.json

# API keys
*_api_key.txt
*_token.txt
EOF

# Initial commit
git add .
git commit -m "Initial vault structure"
git branch -M main
git push -u origin main
```

### 2. Configure Cloud VM

**SSH to Cloud VM:**

```bash
ssh ubuntu@<CLOUD_VM_IP>
```

**Clone Vault Repository:**

```bash
cd ~
git clone git@github.com:YOUR_USERNAME/ai-employee-vault.git AI_Employee_Vault
```

**Configure Vault Sync:**

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

**Create Systemd Service:**

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

# Enable and start
sudo systemctl daemon-reload
sudo systemctl enable vault-sync
sudo systemctl start vault-sync

# Check status
sudo systemctl status vault-sync
```

### 3. Configure Local Machine

**Clone Vault Repository:**

```bash
cd ~
git clone git@github.com:YOUR_USERNAME/ai-employee-vault.git AI_Employee_Vault
```

**Set Up Periodic Sync (Cron):**

```bash
crontab -e

# Add this line (sync every 5 minutes)
*/5 * * * * cd ~/AI_Employee_Vault && git pull --rebase >> ~/vault_sync.log 2>&1
```

**Or Use Vault Sync Script:**

```bash
cd ~/Hackathon-0/platinum/vault-sync

# Create environment file
cat > .env << 'EOF'
VAULT_PATH=/home/YOUR_USERNAME/AI_Employee_Vault
VAULT_REMOTE=git@github.com:YOUR_USERNAME/ai-employee-vault.git
VAULT_BRANCH=main
SYNC_INTERVAL=300
EOF

# Run in background
nohup python3 vault_sync.py --vault ~/AI_Employee_Vault --remote git@github.com:YOUR_USERNAME/ai-employee-vault.git --continuous --interval 300 > ~/vault_sync.log 2>&1 &
```

---

## Conflict Resolution

### Automatic Resolution

The vault sync uses `git pull --rebase` to automatically resolve most conflicts:

1. **Stash local changes** (if any)
2. **Fetch remote changes**
3. **Rebase local commits** on top of remote
4. **Pop stashed changes**
5. **Auto-merge** if possible

### Manual Resolution

If automatic resolution fails:

```bash
cd ~/AI_Employee_Vault

# Check status
git status

# View conflicts
git diff

# Option 1: Accept remote changes
git checkout --theirs <file>
git add <file>
git rebase --continue

# Option 2: Accept local changes
git checkout --ours <file>
git add <file>
git rebase --continue

# Option 3: Abort and retry
git rebase --abort
git pull --rebase
```

### Preventing Conflicts

**Design Patterns:**

1. **Single-Writer Rule**: Only Local writes to Dashboard.md
2. **Domain Ownership**: Cloud writes to /Updates/, Local merges
3. **Claim-by-Move**: First to move file owns it
4. **Append-Only Logs**: Never edit existing log entries

---

## Monitoring

### Check Sync Status

**On Cloud VM:**

```bash
# View sync logs
sudo journalctl -u vault-sync -f

# Check last sync time
cd ~/AI_Employee_Vault
git log -1 --format="%ai %s"

# Check for uncommitted changes
git status
```

**On Local Machine:**

```bash
# View sync logs
tail -f ~/vault_sync.log

# Check last sync time
cd ~/AI_Employee_Vault
git log -1 --format="%ai %s"

# Check for uncommitted changes
git status
```

### Sync Health Metrics

**Check in Vault Logs:**

```bash
cat ~/AI_Employee_Vault/Logs/vault_sync.json
```

**Example Output:**

```json
{
  "timestamp": "2026-02-27T10:30:00Z",
  "operation": "sync",
  "pull_status": "success",
  "push_status": "success",
  "conflicts": 0,
  "files_changed": 3,
  "duration_seconds": 2.5
}
```

---

## Troubleshooting

### Problem: Sync Conflicts

**Symptoms:**
- Vault sync fails with merge conflicts
- Files stuck in conflicted state

**Solution:**

```bash
cd ~/AI_Employee_Vault

# Check conflict files
git status | grep "both modified"

# For each conflict:
# 1. View the conflict
git diff <file>

# 2. Resolve manually or choose a side
git checkout --theirs <file>  # Use remote version
# OR
git checkout --ours <file>    # Use local version

# 3. Mark as resolved
git add <file>

# 4. Continue rebase
git rebase --continue

# 5. Push resolved changes
git push
```

### Problem: Secrets Accidentally Synced

**Symptoms:**
- .env or credentials.json in git history
- Security warning in logs

**Solution:**

```bash
cd ~/AI_Employee_Vault

# Remove from current commit
git rm --cached credentials.json
git commit --amend

# Remove from history (DANGEROUS - rewrites history)
git filter-branch --force --index-filter \
  'git rm --cached --ignore-unmatch credentials.json' \
  --prune-empty --tag-name-filter cat -- --all

# Force push (coordinate with other machines first!)
git push origin --force --all

# Update .gitignore to prevent recurrence
echo "credentials.json" >> .gitignore
git add .gitignore
git commit -m "Update .gitignore to exclude credentials"
git push
```

### Problem: Sync Service Not Running

**Symptoms:**
- No recent commits from cloud
- Vault not updating

**Solution:**

```bash
# Check service status
sudo systemctl status vault-sync

# View recent logs
sudo journalctl -u vault-sync -n 50

# Restart service
sudo systemctl restart vault-sync

# If still failing, test manually
cd ~/Hackathon-0/platinum/vault-sync
source ~/Hackathon-0/venv/bin/activate
python3 vault_sync.py --vault ~/AI_Employee_Vault --remote git@github.com:YOUR_USERNAME/ai-employee-vault.git --operation sync
```

### Problem: High Sync Frequency

**Symptoms:**
- Too many commits
- High bandwidth usage
- GitHub rate limiting

**Solution:**

```bash
# Increase sync interval (e.g., 10 minutes)
sudo nano /etc/systemd/system/vault-sync.service

# Change:
# --interval 300
# To:
# --interval 600

# Reload and restart
sudo systemctl daemon-reload
sudo systemctl restart vault-sync
```

---

## Best Practices

### 1. Commit Messages

Use descriptive commit messages:

```bash
# Good
"Cloud: Created 3 email draft approvals"
"Local: Executed 2 approved social posts"
"Cloud: Updated dashboard with task status"

# Bad
"Update"
"Changes"
"Sync"
```

### 2. Sync Intervals

**Recommended:**
- Cloud: 5 minutes (300 seconds)
- Local: 5 minutes (300 seconds)

**Adjust based on:**
- Task volume (more tasks = shorter interval)
- Bandwidth constraints (limited = longer interval)
- Urgency requirements (urgent = shorter interval)

### 3. Vault Size Management

**Keep vault lean:**

```bash
# Archive old logs monthly
cd ~/AI_Employee_Vault/Logs
mkdir Archive/$(date +%Y-%m)
mv $(date -d "30 days ago" +%Y-%m-*)* Archive/$(date +%Y-%m)/

# Compress archives
tar -czf Archive/$(date +%Y-%m).tar.gz Archive/$(date +%Y-%m)/
rm -rf Archive/$(date +%Y-%m)/

# Commit cleanup
git add .
git commit -m "Archive logs from $(date -d "30 days ago" +%Y-%m)"
git push
```

### 4. Security Audits

**Monthly security check:**

```bash
# Check for accidentally committed secrets
cd ~/AI_Employee_Vault
git log --all --full-history -- "*.env" "credentials.json" "token.json"

# Should return empty
# If not, follow "Secrets Accidentally Synced" procedure
```

---

## Performance Optimization

### Reduce Sync Overhead

**1. Use Shallow Clones:**

```bash
git clone --depth 1 git@github.com:YOUR_USERNAME/ai-employee-vault.git AI_Employee_Vault
```

**2. Exclude Large Files:**

```gitignore
# Add to .gitignore
*.log
*.tmp
*.cache
```

**3. Compress Logs:**

```bash
# Before committing large logs
gzip AI_Employee_Vault/Logs/*.json
```

### Monitor Bandwidth

```bash
# Check repository size
cd ~/AI_Employee_Vault
du -sh .git

# Check recent sync sizes
git log --stat -5
```

---

## Advanced Configuration

### Custom Sync Strategy

**Edit vault_sync.py:**

```python
# Custom conflict resolution
def resolve_conflict(self, file_path: Path):
    if file_path.name == 'Dashboard.md':
        # Always prefer local version
        subprocess.run(['git', 'checkout', '--ours', str(file_path)])
    else:
        # Default: prefer remote
        subprocess.run(['git', 'checkout', '--theirs', str(file_path)])
```

### Webhook Integration

**Trigger immediate sync on push:**

```bash
# On GitHub, add webhook:
# URL: https://your-cloud-vm.com/webhook/vault-sync
# Events: push

# On cloud VM, add webhook handler:
# (Requires web server setup)
```

---

## Maintenance

### Daily Tasks

- Check sync logs for errors
- Verify last sync timestamp
- Monitor vault size

### Weekly Tasks

- Review conflict resolution logs
- Check for uncommitted changes
- Verify .gitignore effectiveness

### Monthly Tasks

- Archive old logs
- Security audit for leaked secrets
- Update sync intervals if needed
- Review and optimize vault size

---

## Integration with Agents

### Cloud Agent Integration

```python
# cloud_agent.py
from vault_sync import VaultSync

sync = VaultSync(vault_path, remote_url)

# Before processing cycle
sync.pull()

# After creating drafts
sync.push()
```

### Local Agent Integration

```python
# local_agent.py
from vault_sync import VaultSync

sync = VaultSync(vault_path, remote_url)

# Before processing approvals
sync.pull()

# After executing actions
sync.push()
```

---

## Disaster Recovery

### Backup Strategy

**1. GitHub as Primary Backup:**
- All vault data in private repository
- Full history preserved

**2. Local Backups:**

```bash
# Daily backup
tar -czf ~/backups/vault_$(date +%Y%m%d).tar.gz ~/AI_Employee_Vault

# Keep 30 days
find ~/backups -name "vault_*.tar.gz" -mtime +30 -delete
```

**3. Cloud VM Backups:**

```bash
# Oracle Cloud: Enable automatic backups
# Backup frequency: Daily
# Retention: 7 days
```

### Recovery Procedures

**Scenario 1: Corrupted Local Vault**

```bash
# Delete and re-clone
rm -rf ~/AI_Employee_Vault
git clone git@github.com:YOUR_USERNAME/ai-employee-vault.git AI_Employee_Vault
```

**Scenario 2: Corrupted Cloud Vault**

```bash
# SSH to cloud VM
ssh ubuntu@<CLOUD_VM_IP>

# Delete and re-clone
rm -rf ~/AI_Employee_Vault
git clone git@github.com:YOUR_USERNAME/ai-employee-vault.git AI_Employee_Vault

# Restart services
sudo systemctl restart vault-sync
sudo systemctl restart cloud-agent
```

**Scenario 3: Lost GitHub Repository**

```bash
# Restore from local backup
cd ~/backups
tar -xzf vault_YYYYMMDD.tar.gz

# Create new repository
# Push backup to new repository
cd ~/AI_Employee_Vault
git remote set-url origin git@github.com:YOUR_USERNAME/new-vault.git
git push -u origin main
```

---

## Conclusion

The vault synchronization system is the backbone of the cloud-local hybrid architecture. By following this guide, you can:

- Set up secure, reliable vault synchronization
- Handle conflicts gracefully
- Monitor sync health
- Troubleshoot common issues
- Maintain optimal performance

**Key Takeaways:**

✅ Security boundaries enforced via .gitignore
✅ Automatic conflict resolution with rebase
✅ 5-minute sync interval for near-real-time coordination
✅ Single-writer patterns prevent conflicts
✅ Complete audit trail in Git history

---

**Next Steps:**

1. Set up vault repository on GitHub
2. Configure cloud VM vault sync
3. Configure local machine vault sync
4. Test end-to-end synchronization
5. Monitor for 24 hours to ensure stability

For deployment instructions, see: `CLOUD_DEPLOYMENT_GUIDE.md`
For security details, see: `SECURITY_ARCHITECTURE.md`
