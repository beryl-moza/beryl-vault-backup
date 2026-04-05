#!/bin/bash
cd "$HOME/Projects/trov-app"

kill $(lsof -t -i:8081) 2>/dev/null || true
kill $(lsof -t -i:8082) 2>/dev/null || true
sleep 1

echo "→ Auto-fixing ALL package versions for this SDK (this takes 1-3 min)..."
npx expo install --fix

echo ""
echo "✅ Versions fixed. Starting expo..."
npx expo start --go --clear
