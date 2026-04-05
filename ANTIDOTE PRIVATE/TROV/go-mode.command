#!/bin/bash
cd "$HOME/Projects/trov-app"

# Kill stale metro
kill $(lsof -t -i:8081) 2>/dev/null || true
kill $(lsof -t -i:8082) 2>/dev/null || true
sleep 1

echo "→ Starting in Expo Go mode..."
npx expo start --go --clear
