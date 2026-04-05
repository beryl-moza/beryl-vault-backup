#!/bin/bash
cd "$HOME/Projects/trov-app"

kill $(lsof -t -i:8081) 2>/dev/null || true
kill $(lsof -t -i:8082) 2>/dev/null || true
sleep 1

echo "→ Downgrading react-native-reanimated to v3 (self-contained, no external worklets)..."
npm install --legacy-peer-deps react-native-reanimated@~3.16.0

echo "→ Starting expo..."
npx expo start --go --clear
