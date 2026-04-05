#!/bin/bash
cd "$HOME/Projects/trov-app"

# Kill stale metro processes
kill $(lsof -t -i:8081) 2>/dev/null || true
kill $(lsof -t -i:8082) 2>/dev/null || true
sleep 1

echo "→ Rewriting tailwind.config.js with NativeWind preset..."
cat > tailwind.config.js << 'EOF'
/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./app/**/*.{js,jsx,ts,tsx}", "./src/**/*.{js,jsx,ts,tsx}"],
  presets: [require('nativewind/preset')],
  theme: {
    extend: {
      colors: {
        brand: {
          orange: '#FF6B35',
          dark: '#0A0A0A',
          card: '#1A1A1A',
          border: '#2A2A2A',
          text: '#FFFFFF',
          muted: '#888888',
        }
      }
    },
  },
  plugins: [],
}
EOF

echo "→ Rewriting metro.config.js..."
cat > metro.config.js << 'EOF'
const { getDefaultConfig } = require("expo/metro-config");
const { withNativeWind } = require('nativewind/metro');

const config = getDefaultConfig(__dirname);

module.exports = withNativeWind(config, { input: './global.css' });
EOF

echo "→ Rewriting babel.config.js..."
cat > babel.config.js << 'EOF'
module.exports = function (api) {
  api.cache(true);
  return {
    presets: [
      ["babel-preset-expo", { jsxImportSource: "nativewind" }],
      "nativewind/babel",
    ],
  };
};
EOF

echo "→ Clearing Expo cache and starting..."
echo ""
npx expo start --clear
