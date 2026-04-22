#!/bin/bash
# Usage: ./install.sh <linux-machine-ip> <remote-username>
set -e

REMOTE_USER="${2:-your_username}"
REMOTE_HOST="${1:-}"

if [ -z "$REMOTE_HOST" ]; then
    echo "Usage: ./install.sh <linux-machine-ip> <remote-username>"
    exit 1
fi

if [ ! -f "config.env" ]; then
    echo "ERROR: config.env not found."
    echo "Copy config.env.example to config.env and fill in your BOT_TOKEN and PASSPHRASE first."
    exit 1
fi

REMOTE="$REMOTE_USER@$REMOTE_HOST"

echo "==> Creating remote directory..."
ssh "$REMOTE" "mkdir -p /home/$REMOTE_USER/groceryai"

echo "==> Copying project files..."
scp bot.py config.env requirements.txt ShoppingTemplate.md "$REMOTE:/home/$REMOTE_USER/groceryai/"

echo "==> Setting up Python venv and installing dependencies..."
ssh "$REMOTE" "
    cd /home/$REMOTE_USER/groceryai
    python3 -m venv venv
    ./venv/bin/pip install --upgrade pip --quiet
    ./venv/bin/pip install -r requirements.txt --quiet
"

echo "==> Installing systemd service..."
scp groceryai.service "$REMOTE:/tmp/groceryai.service"
ssh "$REMOTE" "
    sudo mv /tmp/groceryai.service /etc/systemd/system/groceryai.service
    sudo systemctl daemon-reload
    sudo systemctl enable groceryai
    sudo systemctl start groceryai
"

echo ""
echo "==> Done! Check status with:"
echo "    ssh $REMOTE 'sudo systemctl status groceryai'"
echo ""
echo "==> View logs with:"
echo "    ssh $REMOTE 'sudo journalctl -u groceryai -f'"
