#!/bin/bash
cd "$HOME/Projects/trov-app"

kill $(lsof -t -i:8081) 2>/dev/null || true
kill $(lsof -t -i:8082) 2>/dev/null || true
sleep 1

echo "→ Installing babel-preset-expo explicitly..."
npm install --save-dev --legacy-peer-deps babel-preset-expo

echo "→ Verifying install..."
ls node_modules/babel-preset-expo && echo "✅ babel-preset-expo found" || echo "❌ still missing"

echo "→ Starting expo..."
npx expo start --go --clear
