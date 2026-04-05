#!/bin/bash
set -e
cd "$HOME/Projects/trov-app"

# Kill stale metro
kill $(lsof -t -i:8081) 2>/dev/null || true
kill $(lsof -t -i:8082) 2>/dev/null || true
sleep 1

echo "→ Fixing expo-router version mismatch..."
npm install --legacy-peer-deps expo-router@~6.0.23

echo "→ Restarting in Expo Go mode..."
npx expo start --go --clear
