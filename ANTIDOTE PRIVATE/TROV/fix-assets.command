#!/bin/bash
set -e
cd "$HOME/Projects/trov-app"

# Kill stale metro
kill $(lsof -t -i:8081) 2>/dev/null || true
kill $(lsof -t -i:8082) 2>/dev/null || true
sleep 1

echo "→ Creating missing assets folder..."
mkdir -p assets

# Create minimal valid PNG files using Node (already installed with Expo)
node -e "
const fs = require('fs');
// Minimal 1x1 white PNG
const png = Buffer.from('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwADhQGAWjR9awAAAABJRU5ErkJggg==', 'base64');
fs.writeFileSync('assets/splash.png', png);
fs.writeFileSync('assets/icon.png', png);
fs.writeFileSync('assets/adaptive-icon.png', png);
fs.writeFileSync('assets/favicon.png', png);
console.log('✅ Assets created');
"

echo "→ Starting in Expo Go mode..."
npx expo start --go --clear
