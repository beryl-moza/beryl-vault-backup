#!/bin/bash
cd "$HOME/Projects/trov-app"

# Kill any running expo server
kill $(lsof -t -i:8081) 2>/dev/null || true
kill $(lsof -t -i:8082) 2>/dev/null || true
sleep 1

echo "→ Force-deleting react-native-reanimated from node_modules..."
rm -rf node_modules/react-native-reanimated
rm -rf node_modules/react-native-worklets
rm -rf node_modules/react-native-worklets-core

echo "→ Clearing Metro cache..."
rm -rf /tmp/metro-*
rm -rf $TMPDIR/metro-*
rm -rf $TMPDIR/haste-*

echo "→ Starting expo in Expo Go mode..."
npx expo start --go --clear
