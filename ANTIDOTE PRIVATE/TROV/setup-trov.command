#!/bin/bash
set -e

# ─────────────────────────────────────────────
# TROV APP — One-shot setup script
# Run from anywhere. Does everything.
# ─────────────────────────────────────────────

SUPABASE_URL="https://znqrbidasvayhfkrknxb.supabase.co"
SUPABASE_ANON_KEY="sb_publishable_Nb_sxBZIxk3ZB_S7tZ4SVw_RyYe272M"
PROJECT_DIR="$HOME/Projects/trov-app"

echo ""
echo "🏗  Setting up TROV app at $PROJECT_DIR"
echo ""

# ── 1. Create project dir ──────────────────────
rm -rf "$PROJECT_DIR"
mkdir -p "$PROJECT_DIR"
cd "$PROJECT_DIR"

# ── 2. Scaffold Expo project ───────────────────
echo "→ Scaffolding Expo project..."
npx --yes create-expo-app@latest . --template blank-typescript

# ── 3. Install all dependencies ────────────────
echo "→ Installing base packages (npm install)..."
npm install --legacy-peer-deps

echo "→ Installing additional packages..."
npm install --legacy-peer-deps \
  expo-router \
  expo-secure-store \
  expo-local-authentication \
  expo-location \
  expo-notifications \
  expo-status-bar \
  expo-linking \
  expo-constants \
  react-native-screens \
  react-native-safe-area-context \
  react-native-gesture-handler \
  react-native-reanimated \
  react-native-maps \
  @expo/vector-icons \
  @supabase/supabase-js \
  zustand \
  @tanstack/react-query \
  nativewind \
  tailwindcss

# ── 4. Create .env ─────────────────────────────
echo "→ Writing .env..."
cat > .env << EOF
EXPO_PUBLIC_SUPABASE_URL=$SUPABASE_URL
EXPO_PUBLIC_SUPABASE_ANON_KEY=$SUPABASE_ANON_KEY
EOF

cat > .env.example << EOF
EXPO_PUBLIC_SUPABASE_URL=your-supabase-url
EXPO_PUBLIC_SUPABASE_ANON_KEY=your-anon-key
EOF

# ── 5. Update app.json ─────────────────────────
echo "→ Configuring app.json..."
cat > app.json << 'EOF'
{
  "expo": {
    "name": "TROV",
    "slug": "trov-app",
    "version": "1.0.0",
    "orientation": "portrait",
    "icon": "./assets/icon.png",
    "userInterfaceStyle": "light",
    "splash": {
      "image": "./assets/splash.png",
      "resizeMode": "contain",
      "backgroundColor": "#0A0A0A"
    },
    "scheme": "trov",
    "ios": {
      "supportsTablet": false,
      "bundleIdentifier": "com.antidotegroup.trov",
      "infoPlist": {
        "NSLocationWhenInUseUsageDescription": "TROV uses your location to show nearby collectibles events.",
        "NSLocationAlwaysUsageDescription": "TROV uses your location to alert you about nearby events.",
        "NSFaceIDUsageDescription": "Use Face ID to sign in quickly."
      }
    },
    "android": {
      "adaptiveIcon": {
        "foregroundImage": "./assets/adaptive-icon.png",
        "backgroundColor": "#0A0A0A"
      }
    },
    "web": {
      "favicon": "./assets/favicon.png"
    },
    "plugins": [
      "expo-router",
      "expo-secure-store",
      "expo-local-authentication",
      [
        "expo-location",
        {
          "locationAlwaysAndWhenInUsePermission": "TROV uses your location to find nearby events."
        }
      ],
      [
        "expo-notifications",
        {
          "icon": "./assets/notification-icon.png",
          "color": "#FF6B35"
        }
      ]
    ],
    "experiments": {
      "typedRoutes": true
    }
  }
}
EOF

# ── 6. NativeWind config ───────────────────────
echo "→ Setting up NativeWind..."
cat > tailwind.config.js << 'EOF'
/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./app/**/*.{js,jsx,ts,tsx}", "./src/**/*.{js,jsx,ts,tsx}"],
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

cat > metro.config.js << 'EOF'
const { getDefaultConfig } = require("expo/metro-config");
const { withNativeWind } = require('nativewind/metro');

const config = getDefaultConfig(__dirname);

module.exports = withNativeWind(config, { input: './global.css' });
EOF

cat > global.css << 'EOF'
@tailwind base;
@tailwind components;
@tailwind utilities;
EOF

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

# ── 7. Create folder structure ─────────────────
echo "→ Creating project structure..."
mkdir -p src/{components,hooks,utils,lib,types,stores}
mkdir -p app/\(tabs\) app/\(auth\)

# ── 8. Supabase client ─────────────────────────
echo "→ Creating Supabase client..."
cat > src/lib/supabase.ts << 'EOF'
import { createClient } from '@supabase/supabase-js'
import * as SecureStore from 'expo-secure-store'

const ExpoSecureStoreAdapter = {
  getItem: (key: string) => SecureStore.getItemAsync(key),
  setItem: (key: string, value: string) => SecureStore.setItemAsync(key, value),
  removeItem: (key: string) => SecureStore.deleteItemAsync(key),
}

const supabaseUrl = process.env.EXPO_PUBLIC_SUPABASE_URL!
const supabaseAnonKey = process.env.EXPO_PUBLIC_SUPABASE_ANON_KEY!

export const supabase = createClient(supabaseUrl, supabaseAnonKey, {
  auth: {
    storage: ExpoSecureStoreAdapter,
    autoRefreshToken: true,
    persistSession: true,
    detectSessionInUrl: false,
  },
})
EOF

# ── 9. Types ────────────────────────────────────
cat > src/types/index.ts << 'EOF'
export interface Event {
  id: string
  title: string
  description: string | null
  date: string
  end_date: string | null
  location_name: string
  address: string
  city: string
  state: string
  zip: string
  latitude: number
  longitude: number
  category: string
  subcategory: string | null
  image_url: string | null
  source_url: string | null
  is_featured: boolean
  status: 'active' | 'cancelled' | 'pending'
  created_at: string
}

export interface UserProfile {
  id: string
  email: string
  username: string | null
  display_name: string | null
  avatar_url: string | null
  bio: string | null
  city: string | null
  state: string | null
  zip: string | null
  onboarding_completed: boolean
}

export interface SavedEvent {
  id: string
  user_id: string
  event_id: string
  event?: Event
  created_at: string
}
EOF

# ── 10. Auth store (Zustand) ───────────────────
cat > src/stores/authStore.ts << 'EOF'
import { create } from 'zustand'
import { supabase } from '../lib/supabase'
import type { UserProfile } from '../types'

interface AuthState {
  user: UserProfile | null
  session: any | null
  loading: boolean
  setSession: (session: any) => void
  setUser: (user: UserProfile | null) => void
  signOut: () => Promise<void>
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  session: null,
  loading: true,
  setSession: (session) => set({ session, loading: false }),
  setUser: (user) => set({ user }),
  signOut: async () => {
    await supabase.auth.signOut()
    set({ user: null, session: null })
  },
}))
EOF

# ── 11. Root layout ────────────────────────────
cat > app/_layout.tsx << 'EOF'
import { useEffect } from 'react'
import { Stack } from 'expo-router'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { supabase } from '../src/lib/supabase'
import { useAuthStore } from '../src/stores/authStore'
import '../global.css'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60 * 5, // 5 minutes
      retry: 2,
    },
  },
})

export default function RootLayout() {
  const { setSession } = useAuthStore()

  useEffect(() => {
    supabase.auth.getSession().then(({ data: { session } }) => {
      setSession(session)
    })

    const { data: { subscription } } = supabase.auth.onAuthStateChange((_event, session) => {
      setSession(session)
    })

    return () => subscription.unsubscribe()
  }, [])

  return (
    <QueryClientProvider client={queryClient}>
      <Stack screenOptions={{ headerShown: false }}>
        <Stack.Screen name="(tabs)" />
        <Stack.Screen name="(auth)" />
      </Stack>
    </QueryClientProvider>
  )
}
EOF

# ── 12. Tab layout ─────────────────────────────
cat > "app/(tabs)/_layout.tsx" << 'EOF'
import { Tabs } from 'expo-router'
import { Ionicons } from '@expo/vector-icons'

export default function TabLayout() {
  return (
    <Tabs
      screenOptions={{
        headerShown: false,
        tabBarStyle: {
          backgroundColor: '#0A0A0A',
          borderTopColor: '#2A2A2A',
          paddingBottom: 8,
          height: 80,
        },
        tabBarActiveTintColor: '#FF6B35',
        tabBarInactiveTintColor: '#888888',
        tabBarLabelStyle: {
          fontSize: 11,
          fontWeight: '600',
        },
      }}
    >
      <Tabs.Screen
        name="index"
        options={{
          title: 'Home',
          tabBarIcon: ({ color, size }) => (
            <Ionicons name="home" size={size} color={color} />
          ),
        }}
      />
      <Tabs.Screen
        name="explore"
        options={{
          title: 'Explore',
          tabBarIcon: ({ color, size }) => (
            <Ionicons name="map" size={size} color={color} />
          ),
        }}
      />
      <Tabs.Screen
        name="saved"
        options={{
          title: 'Saved',
          tabBarIcon: ({ color, size }) => (
            <Ionicons name="bookmark" size={size} color={color} />
          ),
        }}
      />
      <Tabs.Screen
        name="profile"
        options={{
          title: 'Profile',
          tabBarIcon: ({ color, size }) => (
            <Ionicons name="person" size={size} color={color} />
          ),
        }}
      />
    </Tabs>
  )
}
EOF

# ── 13. Home screen ────────────────────────────
cat > "app/(tabs)/index.tsx" << 'EOF'
import { View, Text, ScrollView, TouchableOpacity, Image, ActivityIndicator } from 'react-native'
import { SafeAreaView } from 'react-native-safe-area-context'
import { Ionicons } from '@expo/vector-icons'
import { useQuery } from '@tanstack/react-query'
import { supabase } from '../../src/lib/supabase'
import type { Event } from '../../src/types'

function useEvents() {
  return useQuery({
    queryKey: ['events'],
    queryFn: async () => {
      const { data, error } = await supabase
        .from('events')
        .select('*')
        .eq('status', 'active')
        .order('date', { ascending: true })
        .limit(20)
      if (error) throw error
      return data as Event[]
    },
  })
}

function EventCard({ event }: { event: Event }) {
  const date = new Date(event.date)
  const month = date.toLocaleString('default', { month: 'short' }).toUpperCase()
  const day = date.getDate()

  return (
    <TouchableOpacity
      className="bg-[#1A1A1A] rounded-2xl mb-4 overflow-hidden border border-[#2A2A2A]"
      activeOpacity={0.8}
    >
      {event.image_url ? (
        <Image source={{ uri: event.image_url }} className="w-full h-48" resizeMode="cover" />
      ) : (
        <View className="w-full h-48 bg-[#2A2A2A] items-center justify-center">
          <Ionicons name="calendar-outline" size={48} color="#444" />
        </View>
      )}
      <View className="p-4">
        <View className="flex-row items-start justify-between">
          <View className="flex-1 mr-3">
            <Text className="text-white font-bold text-lg leading-tight" numberOfLines={2}>
              {event.title}
            </Text>
            <Text className="text-[#888] text-sm mt-1">
              {event.location_name} · {event.city}, {event.state}
            </Text>
          </View>
          <View className="bg-[#FF6B35] rounded-xl px-3 py-2 items-center min-w-[52px]">
            <Text className="text-white text-xs font-bold">{month}</Text>
            <Text className="text-white text-xl font-bold leading-tight">{day}</Text>
          </View>
        </View>
        <View className="flex-row items-center mt-3 flex-wrap gap-2">
          <View className="bg-[#2A2A2A] rounded-full px-3 py-1">
            <Text className="text-[#FF6B35] text-xs font-semibold">{event.category}</Text>
          </View>
          {event.is_featured && (
            <View className="bg-[#FF6B35]/20 rounded-full px-3 py-1">
              <Text className="text-[#FF6B35] text-xs font-semibold">⭐ Featured</Text>
            </View>
          )}
        </View>
      </View>
    </TouchableOpacity>
  )
}

export default function HomeScreen() {
  const { data: events, isLoading, error } = useEvents()

  return (
    <SafeAreaView className="flex-1 bg-[#0A0A0A]">
      <ScrollView className="flex-1" showsVerticalScrollIndicator={false}>
        {/* Header */}
        <View className="px-5 pt-4 pb-2 flex-row items-center justify-between">
          <View>
            <Text className="text-[#888] text-sm">Welcome back</Text>
            <Text className="text-white text-2xl font-bold">Discover Events</Text>
          </View>
          <TouchableOpacity className="bg-[#1A1A1A] p-3 rounded-full border border-[#2A2A2A]">
            <Ionicons name="notifications-outline" size={22} color="#FF6B35" />
          </TouchableOpacity>
        </View>

        {/* Search bar */}
        <TouchableOpacity className="mx-5 mt-3 mb-5 bg-[#1A1A1A] border border-[#2A2A2A] rounded-2xl flex-row items-center px-4 py-3">
          <Ionicons name="search" size={18} color="#888" />
          <Text className="text-[#888] ml-2 text-base">Search events, athletes...</Text>
        </TouchableOpacity>

        {/* Category pills */}
        <ScrollView horizontal showsHorizontalScrollIndicator={false} className="mb-5" contentContainerStyle={{ paddingHorizontal: 20, gap: 8 }}>
          {['All', 'Card Shows', 'Autographs', 'Athlete Appearances', 'Auctions', 'Meetups'].map((cat) => (
            <TouchableOpacity
              key={cat}
              className={`px-4 py-2 rounded-full border ${cat === 'All' ? 'bg-[#FF6B35] border-[#FF6B35]' : 'bg-[#1A1A1A] border-[#2A2A2A]'}`}
            >
              <Text className={`text-sm font-semibold ${cat === 'All' ? 'text-white' : 'text-[#888]'}`}>{cat}</Text>
            </TouchableOpacity>
          ))}
        </ScrollView>

        {/* Events */}
        <View className="px-5">
          {isLoading && (
            <View className="items-center py-20">
              <ActivityIndicator size="large" color="#FF6B35" />
              <Text className="text-[#888] mt-3">Loading events...</Text>
            </View>
          )}
          {error && (
            <View className="items-center py-20">
              <Ionicons name="cloud-offline-outline" size={48} color="#444" />
              <Text className="text-white font-semibold mt-3">Couldn't load events</Text>
              <Text className="text-[#888] mt-1 text-center">Check your connection and try again</Text>
            </View>
          )}
          {events?.map((event) => (
            <EventCard key={event.id} event={event} />
          ))}
          {events?.length === 0 && !isLoading && (
            <View className="items-center py-20">
              <Ionicons name="calendar-outline" size={48} color="#444" />
              <Text className="text-white font-semibold mt-3">No events yet</Text>
              <Text className="text-[#888] mt-1">Check back soon</Text>
            </View>
          )}
        </View>
      </ScrollView>
    </SafeAreaView>
  )
}
EOF

# ── 14. Explore screen ─────────────────────────
cat > "app/(tabs)/explore.tsx" << 'EOF'
import { View, Text, TouchableOpacity } from 'react-native'
import { SafeAreaView } from 'react-native-safe-area-context'
import { Ionicons } from '@expo/vector-icons'

export default function ExploreScreen() {
  return (
    <SafeAreaView className="flex-1 bg-[#0A0A0A]">
      <View className="px-5 pt-4 pb-4">
        <Text className="text-white text-2xl font-bold">Explore</Text>
        <Text className="text-[#888] text-sm mt-1">Events near you</Text>
      </View>

      {/* Search */}
      <TouchableOpacity className="mx-5 mb-4 bg-[#1A1A1A] border border-[#2A2A2A] rounded-2xl flex-row items-center px-4 py-3">
        <Ionicons name="search" size={18} color="#888" />
        <Text className="text-[#888] ml-2 text-base">Search by city, zip, or venue...</Text>
      </TouchableOpacity>

      {/* Map placeholder */}
      <View className="flex-1 mx-5 mb-5 bg-[#1A1A1A] rounded-2xl border border-[#2A2A2A] items-center justify-center">
        <Ionicons name="map-outline" size={64} color="#2A2A2A" />
        <Text className="text-[#888] mt-3 font-semibold">Map coming soon</Text>
        <Text className="text-[#555] text-sm mt-1">Events will appear as pins</Text>
      </View>
    </SafeAreaView>
  )
}
EOF

# ── 15. Saved screen ───────────────────────────
cat > "app/(tabs)/saved.tsx" << 'EOF'
import { View, Text, TouchableOpacity } from 'react-native'
import { SafeAreaView } from 'react-native-safe-area-context'
import { Ionicons } from '@expo/vector-icons'

export default function SavedScreen() {
  return (
    <SafeAreaView className="flex-1 bg-[#0A0A0A]">
      <View className="px-5 pt-4 pb-4">
        <Text className="text-white text-2xl font-bold">Saved</Text>
        <Text className="text-[#888] text-sm mt-1">Events you're watching</Text>
      </View>
      <View className="flex-1 items-center justify-center pb-20">
        <View className="bg-[#1A1A1A] p-6 rounded-full mb-4 border border-[#2A2A2A]">
          <Ionicons name="bookmark-outline" size={48} color="#FF6B35" />
        </View>
        <Text className="text-white text-xl font-bold">No saved events yet</Text>
        <Text className="text-[#888] text-sm mt-2 text-center px-10">
          Tap the bookmark icon on any event to save it here
        </Text>
        <TouchableOpacity className="mt-6 bg-[#FF6B35] px-6 py-3 rounded-full">
          <Text className="text-white font-bold">Browse Events</Text>
        </TouchableOpacity>
      </View>
    </SafeAreaView>
  )
}
EOF

# ── 16. Profile screen ─────────────────────────
cat > "app/(tabs)/profile.tsx" << 'EOF'
import { View, Text, TouchableOpacity, Image } from 'react-native'
import { SafeAreaView } from 'react-native-safe-area-context'
import { ScrollView } from 'react-native'
import { Ionicons } from '@expo/vector-icons'

const menuItems = [
  { icon: 'notifications-outline', label: 'Notification Preferences' },
  { icon: 'heart-outline', label: 'My Interests' },
  { icon: 'location-outline', label: 'My Location' },
  { icon: 'shield-checkmark-outline', label: 'Privacy & Security' },
  { icon: 'help-circle-outline', label: 'Help & Support' },
  { icon: 'log-out-outline', label: 'Sign Out', danger: true },
]

export default function ProfileScreen() {
  return (
    <SafeAreaView className="flex-1 bg-[#0A0A0A]">
      <ScrollView className="flex-1" showsVerticalScrollIndicator={false}>
        <View className="px-5 pt-4 pb-6">
          <Text className="text-white text-2xl font-bold">Profile</Text>
        </View>

        {/* Avatar + name */}
        <View className="items-center pb-8">
          <View className="w-24 h-24 rounded-full bg-[#2A2A2A] items-center justify-center border-2 border-[#FF6B35] mb-3">
            <Ionicons name="person" size={40} color="#888" />
          </View>
          <Text className="text-white text-xl font-bold">Sign in to get started</Text>
          <Text className="text-[#888] text-sm mt-1">Personalize your experience</Text>
          <TouchableOpacity className="mt-4 bg-[#FF6B35] px-8 py-3 rounded-full">
            <Text className="text-white font-bold text-base">Sign In</Text>
          </TouchableOpacity>
        </View>

        {/* Menu */}
        <View className="mx-5 bg-[#1A1A1A] rounded-2xl border border-[#2A2A2A] overflow-hidden">
          {menuItems.map((item, index) => (
            <TouchableOpacity
              key={item.label}
              className={`flex-row items-center px-5 py-4 ${index < menuItems.length - 1 ? 'border-b border-[#2A2A2A]' : ''}`}
              activeOpacity={0.7}
            >
              <Ionicons
                name={item.icon as any}
                size={20}
                color={item.danger ? '#FF4444' : '#888'}
              />
              <Text className={`ml-3 text-base font-medium flex-1 ${item.danger ? 'text-[#FF4444]' : 'text-white'}`}>
                {item.label}
              </Text>
              {!item.danger && <Ionicons name="chevron-forward" size={16} color="#444" />}
            </TouchableOpacity>
          ))}
        </View>

        <Text className="text-center text-[#444] text-xs mt-6 mb-4">TROV v1.0.0</Text>
      </ScrollView>
    </SafeAreaView>
  )
}
EOF

# ── 17. .gitignore ─────────────────────────────
cat > .gitignore << 'EOF'
node_modules/
.expo/
dist/
npm-debug.*
*.jks
*.p8
*.p12
*.key
*.mobileprovision
*.orig.*
web-build/
.env
.env.local
.DS_Store
EOF

# ── 18. CLAUDE.md ──────────────────────────────
cat > CLAUDE.md << 'EOF'
# TROV — iOS App (Expo/React Native + Supabase)

## What This Is
Collectibles event discovery app. Users customize interests → get push alerts for matching card shows, signings, meetups in NYC/NJ.

## Tech Stack
- Expo SDK (managed workflow, NO ejection)
- TypeScript strict mode
- Expo Router (file-based routing)
- Supabase (auth, database, realtime, storage)
- Zustand (UI state) + TanStack Query (server state)
- NativeWind v4 (Tailwind for RN)
- expo-notifications (push)
- expo-location + react-native-maps

## Architecture Rules
- All screens in app/ using Expo Router
- Bottom tab navigation: Home, Explore, Saved, Profile
- Components in src/components/, hooks in src/hooks/
- Supabase client in src/lib/supabase.ts
- All API calls through TanStack Query hooks
- TypeScript interfaces in src/types/
- NativeWind for all styling — dark theme (#0A0A0A bg, #FF6B35 brand orange)

## Current Phase: 1 — App Shell + Data
Next: auth flow (Apple Sign In + email), event detail screen, save/unsave events

## Commands
- npx expo start — local dev
- npx expo start --ios — iOS simulator
- npx eas build --platform ios --profile preview — TestFlight build

## Brand Colors
- Background: #0A0A0A
- Card: #1A1A1A
- Border: #2A2A2A
- Brand Orange: #FF6B35
- Text: #FFFFFF
- Muted: #888888
EOF

echo ""
echo "✅ TROV app is ready!"
echo ""
echo "Next step — run the app:"
echo "  cd $PROJECT_DIR && npx expo start"
echo ""
