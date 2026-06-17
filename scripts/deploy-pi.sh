#!/bin/bash
#
# deploy-pi.sh — run on the PRODUCTION Raspberry Pi.
# One command: pull latest code -> update + restart FastAPI backend (app-ui)
#              -> build + restart Svelte frontend (ui).
#
# First-time setup on the Pi:
#   git clone https://github.com/SystemsCyber/sss2-gui-v2.git
#   cd sss2-gui-v2
#   python3 -m venv app-ui/venv
#   # install the two systemd units (see scripts/systemd/) then:
#   sudo systemctl enable sss2-backend.service sss2-frontend.service
#   ./scripts/deploy-pi.sh
#
set -euo pipefail

# ===== Config (override via env if your names/paths differ) =====
REMOTE="${REMOTE:-origin}"                       # remote that points at sss2-gui-v2 (clone default: origin)
BRANCH="${BRANCH:-main}"
BACKEND_SERVICE="${BACKEND_SERVICE:-sss2-backend.service}"
FRONTEND_SERVICE="${FRONTEND_SERVICE:-sss2-frontend.service}"

# Where the browser reaches the FastAPI backend.
#   "/api"  -> default; use this when a reverse proxy (nginx/caddy) routes /api to
#              the backend on the same host/domain as the UI. No CORS needed.
#   absolute URL (e.g. https://sss2.example.com or http://192.168.1.50:8000)
#              -> browser calls the backend directly. CORS is already enabled in main.py.
# Baked into the UI at build time (Vite inlines import.meta.env.VITE_API_BASE).
export VITE_API_BASE="${VITE_API_BASE:-/api}"

echo "--------------------------------------"
echo "SSS2-GUI deployment (Raspberry Pi)"
echo "--------------------------------------"

# Move to repo root (this script lives in scripts/)
cd "$(dirname "$0")/.."
ROOT="$(pwd)"
echo "Repo : $ROOT"
echo "API  : VITE_API_BASE=$VITE_API_BASE"

# 1) Pull latest code
echo "==> Pulling latest from $REMOTE/$BRANCH..."
git pull "$REMOTE" "$BRANCH"

# 2) Backend (FastAPI / app-ui) — update Python deps
echo "==> Updating backend dependencies..."
if [ ! -d app-ui/venv ]; then
  echo "    Creating venv at app-ui/venv..."
  python3 -m venv app-ui/venv
fi
# shellcheck disable=SC1091
source app-ui/venv/bin/activate
pip install --upgrade pip >/dev/null
pip install -r app-ui/requirements.txt
deactivate

# 3) Restart backend service
echo "==> Restarting $BACKEND_SERVICE..."
sudo systemctl restart "$BACKEND_SERVICE"

# 4) Frontend (Svelte / ui) — build standalone Node server (adapter-node -> ./build)
echo "==> Building frontend..."
cd "$ROOT/ui"
# npm ci is faster/reproducible but needs package-lock in sync; fall back to install.
npm ci || npm install
npm run build
cd "$ROOT"

# 5) Restart frontend service
echo "==> Restarting $FRONTEND_SERVICE..."
sudo systemctl restart "$FRONTEND_SERVICE"

echo "--------------------------------------"
echo "Deployment complete."
echo "  backend ($BACKEND_SERVICE) : $(systemctl is-active "$BACKEND_SERVICE" || true)"
echo "  frontend($FRONTEND_SERVICE): $(systemctl is-active "$FRONTEND_SERVICE" || true)"
echo "--------------------------------------"
