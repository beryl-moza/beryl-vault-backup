#!/bin/bash
cd "$HOME/Projects/trov-app"

# Kill any existing expo/metro processes on 8081/8082
kill $(lsof -t -i:8081) 2>/dev/null || true
kill $(lsof -t -i:8082) 2>/dev/null || true
sleep 1

echo ""
echo "🚀 Launching TROV..."
echo ""
npx expo start --port 8081
