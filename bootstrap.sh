#!/usr/bin/env bash
# bootstrap.sh - SEEM Sovereign Agent One-Command Installer

set -euo pipefail

DRY_RUN=false
NO_DAEMON=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --dry-run)   DRY_RUN=true; shift ;;
        --no-daemon) NO_DAEMON=true; shift ;;
        *) echo "Unknown option: $1"; exit 1 ;;
    esac
done

echo "SEEM 2.0 Sovereign Agent Bootstrap (Genesis v1.0.0)"
echo "Date: $(date)"
echo "Dry run: $DRY_RUN"

# 1. Environment + Torch check
command -v python3 >/dev/null || { echo "Python3 required"; exit 1; }
command -v git >/dev/null     || { echo "git required"; exit 1; }
command -v jq >/dev/null      || { echo "jq required – installing..."; sudo apt-get update && sudo apt-get install -y jq; }

python3 -c "
import sys
if sys.version_info < (3, 10):
    print('Python 3.10+ required'); sys.exit(1)
import torch
print('Torch OK on', torch.device('cuda' if torch.cuda.is_available() else 'cpu'))
" || {
    echo "Torch installation required. Run: pip3 install --user torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu"
    exit 1
}

# 2. Clone / update
REPO_URL="https://github.com/beyond-repair/SEEM-2.0-Self-Evolving-Emergent-Mind.git"
if [[ ! -f "seem.py" ]]; then
    echo "Cloning SEEM repo..."
    $DRY_RUN || git clone "$REPO_URL" .
else
    echo "Repo already present. Pulling latest..."
    $DRY_RUN || git pull
fi

# 3. Core structure
mkdir -p core plugins scripts systemd twins
$DRY_RUN || touch core/__init__.py

# 4. Dependencies
echo "Installing Python dependencies..."
$DRY_RUN || pip3 install --user -r requirements.txt

# 5. Config
if [[ ! -f "config.json" ]]; then
    echo "Creating config.json template..."
    $DRY_RUN || cat > config.json <<'EOF'
{
  "api_key": "your-secure-vsa-key-123",
  "daemon_port": 5555,
  "cloud_remote": "dropbox:SEEM-backups",
  "rclone_path": "~/.config/rclone/rclone.conf"
}
EOF
    echo "→ IMPORTANT: Edit config.json with your real API key!"
fi

# 6. Systemd (dynamic absolute paths)
INSTALL_DIR=$(pwd)
USER_NAME=$(whoami)
$DRY_RUN || cat > /tmp/seem-agent.service <<EOF
[Unit]
Description=SEEM Sovereign Cognitive Microservice
After=network.target

[Service]
ExecStart=/usr/bin/python3 $INSTALL_DIR/seem.py daemon
WorkingDirectory=$INSTALL_DIR
Restart=always
RestartSec=5
User=$USER_NAME
Environment="API_KEY=$(jq -r .api_key config.json 2>/dev/null || echo 'your-secure-vsa-key-123')"
Environment="PYTHONUNBUFFERED=1"

[Install]
WantedBy=multi-user.target
EOF

$DRY_RUN || sudo mv /tmp/seem-agent.service /etc/systemd/system/
$DRY_RUN || sudo systemctl daemon-reload

if ! $NO_DAEMON; then
    $DRY_RUN || sudo systemctl enable --now seem-agent.service
fi

# 7. rclone check
if [[ ! -f "$HOME/.config/rclone/rclone.conf" ]]; then
    echo "rclone not configured yet. Run: rclone config"
else
    echo "rclone found. Latest backups:"
    $DRY_RUN || rclone ls "$(jq -r .cloud_remote config.json)"
fi

echo ""
echo "Genesis complete! Core modules in ./core/"
echo "Next steps:"
echo "  1. Edit config.json with your real API key"
echo "  2. Configure rclone if using cloud backup"
echo "  3. Run: python telegram_bot.py  (in another terminal)"
echo "  4. Text your bot: /start"
echo "  5. Create first twin: seem init brian_new"
echo "  6. (Optional) sudo systemctl status seem-agent.service"
