#!/bin/bash
cd "$HOME/Projects/trov-app"

kill $(lsof -t -i:8081) 2>/dev/null || true
kill $(lsof -t -i:8082) 2>/dev/null || true
sleep 1

echo "→ Removing react-native-reanimated (not needed yet, causing babel crash)..."
npm uninstall react-native-reanimated

echo "→ Starting expo..."
npx expo start --go --clear
