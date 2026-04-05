#!/bin/bash
cd "$HOME/Projects/trov-app"

echo "→ Setting expo-router as entry point in package.json..."
node -e "
const fs = require('fs');
const pkg = JSON.parse(fs.readFileSync('package.json', 'utf8'));
pkg.main = 'expo-router/entry';
fs.writeFileSync('package.json', JSON.stringify(pkg, null, 2));
console.log('Done - main set to expo-router/entry');
"

echo "→ Removing any root-level App.tsx / App.js that could override routing..."
rm -f App.tsx App.js App.ts

echo "→ Restarting expo..."
kill $(lsof -t -i:8081) 2>/dev/null || true
sleep 1
npx expo start --go --clear
