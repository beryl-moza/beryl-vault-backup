#!/bin/bash
cd "$HOME/Projects/trov-app"
echo "→ Fixing Tailwind to v3 for NativeWind compatibility..."
npm install tailwindcss@3 --legacy-peer-deps
echo "→ Done. Starting expo..."
npx expo start
