#!/bin/bash
cd "$HOME/Projects/trov-app"

echo "→ Installing SDK-compatible package versions..."
npm install --legacy-peer-deps \
  expo-secure-store@~15.0.8 \
  react-native-gesture-handler@~2.28.0 \
  react-native-maps@~1.20.1 \
  react-native-reanimated@~4.1.1 \
  react-native-safe-area-context@~5.6.0 \
  react-native-screens@~4.16.0

echo ""
echo "✅ Versions fixed! Starting expo..."
echo ""
npx expo start
