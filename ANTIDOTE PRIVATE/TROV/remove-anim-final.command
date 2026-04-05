#!/bin/bash
cd "$HOME/Projects/trov-app"

# Kill any running expo server
kill $(lsof -t -i:8081) 2>/dev/null || true
kill $(lsof -t -i:8082) 2>/dev/null || true
sleep 1

echo "→ Removing react-native-reanimated from package.json..."
node -e "
const fs = require('fs');
const pkg = JSON.parse(fs.readFileSync('package.json', 'utf8'));
delete pkg.dependencies['react-native-reanimated'];
delete pkg.devDependencies?.['react-native-reanimated'];
fs.writeFileSync('package.json', JSON.stringify(pkg, null, 2));
console.log('Done - reanimated removed from package.json');
"

echo "→ Deleting reanimated from node_modules..."
rm -rf node_modules/react-native-reanimated
rm -rf node_modules/react-native-worklets
rm -rf node_modules/react-native-worklets-core

echo "→ Clearing Metro cache..."
rm -rf /tmp/metro-* 2>/dev/null
rm -rf "$TMPDIR/metro-*" 2>/dev/null
rm -rf "$TMPDIR/haste-*" 2>/dev/null

echo "→ Starting expo in Expo Go mode..."
npx expo start --go --clear
