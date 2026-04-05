#!/bin/bash
cd "$HOME/Projects/trov-app"

echo "→ Patching tailwind.config.js with NativeWind preset..."
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

echo "→ Done. Starting expo..."
npx expo start
