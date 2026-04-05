#!/bin/bash
# ═══════════════════════════════════════════════
# ARC Dashboard - Auto Deploy to Netlify
# ═══════════════════════════════════════════════
# Usage: bash deploy.sh
# Deploys the public/ folder to Netlify. No browser needed.

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ENV_FILE="$SCRIPT_DIR/.env"

if [ ! -f "$ENV_FILE" ]; then
  echo "ERROR: .env file not found at $ENV_FILE"
  exit 1
fi

source "$ENV_FILE"

if [ -z "$NETLIFY_AUTH_TOKEN" ] || [ -z "$NETLIFY_SITE_ID" ]; then
  echo "ERROR: NETLIFY_AUTH_TOKEN or NETLIFY_SITE_ID not set in .env"
  exit 1
fi

export PATH="/sessions/sweet-happy-albattani/.npm-global/bin:$PATH"
if ! command -v netlify &> /dev/null; then
  echo "Installing netlify-cli..."
  npm config set prefix /sessions/sweet-happy-albattani/.npm-global
  npm install -g netlify-cli
fi

echo "Deploying ARC Dashboard to Netlify..."
cd "$SCRIPT_DIR"
netlify deploy --prod --dir=public --site="$NETLIFY_SITE_ID" --auth="$NETLIFY_AUTH_TOKEN"

echo ""
echo "ARC Dashboard live at: https://arc-dashboard-antidote.netlify.app"
