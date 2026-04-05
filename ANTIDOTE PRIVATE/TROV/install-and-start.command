#!/bin/bash
cd "$HOME/Projects/trov-app"

# Kill metro
kill $(lsof -t -i:8081) 2>/dev/null || true
kill $(lsof -t -i:8082) 2>/dev/null || true
sleep 1

echo "→ Installing ALL missing packages (this may take 1-2 min)..."
npm install --legacy-peer-deps

echo ""
echo "✅ Install done. Starting expo..."
npx expo start --go --clear
