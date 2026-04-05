#!/bin/bash
set -e
cd "$HOME/Projects/trov-app"

# Kill stale metro
kill $(lsof -t -i:8081) 2>/dev/null || true
kill $(lsof -t -i:8082) 2>/dev/null || true
sleep 1

echo "→ Writing ultra-safe self-contained app (no external deps)..."

# ── babel.config.js ──
cat > babel.config.js << 'EOF'
module.exports = function (api) {
  api.cache(true);
  return { presets: ['babel-preset-expo'] };
};
EOF

# ── metro.config.js ──
cat > metro.config.js << 'EOF'
const { getDefaultConfig } = require("expo/metro-config");
module.exports = getDefaultConfig(__dirname);
EOF

# ── Root layout (no external imports) ──
cat > app/_layout.tsx << 'EOF'
import { Stack } from 'expo-router'

export default function RootLayout() {
  return (
    <Stack screenOptions={{ headerShown: false }}>
      <Stack.Screen name="(tabs)" />
    </Stack>
  )
}
EOF

# ── Tab layout ──
cat > 'app/(tabs)/_layout.tsx' << 'EOF'
import { Tabs } from 'expo-router'
import { Ionicons } from '@expo/vector-icons'

export default function TabLayout() {
  return (
    <Tabs screenOptions={{
      headerShown: false,
      tabBarStyle: { backgroundColor: '#0A0A0A', borderTopColor: '#2A2A2A', paddingBottom: 8, height: 80 },
      tabBarActiveTintColor: '#FF6B35',
      tabBarInactiveTintColor: '#888888',
      tabBarLabelStyle: { fontSize: 11, fontWeight: '600' },
    }}>
      <Tabs.Screen name="index" options={{ title: 'Home', tabBarIcon: ({ color, size }) => <Ionicons name="home" size={size} color={color} /> }} />
      <Tabs.Screen name="explore" options={{ title: 'Explore', tabBarIcon: ({ color, size }) => <Ionicons name="map" size={size} color={color} /> }} />
      <Tabs.Screen name="saved" options={{ title: 'Saved', tabBarIcon: ({ color, size }) => <Ionicons name="bookmark" size={size} color={color} /> }} />
      <Tabs.Screen name="profile" options={{ title: 'Profile', tabBarIcon: ({ color, size }) => <Ionicons name="person" size={size} color={color} /> }} />
    </Tabs>
  )
}
EOF

# ── Home screen (hardcoded events, zero external imports) ──
cat > 'app/(tabs)/index.tsx' << 'EOF'
import { View, Text, ScrollView, TouchableOpacity, StyleSheet } from 'react-native'
import { SafeAreaView } from 'react-native-safe-area-context'
import { Ionicons } from '@expo/vector-icons'

const EVENTS = [
  { id: '1', title: 'Meadowlands Sports Card & Memorabilia Show', location_name: 'Meadowlands Expo Center', city: 'Secaucus', state: 'NJ', category: 'Card Shows', date: '2025-03-15', is_featured: true },
  { id: '2', title: 'Derek Jeter Autograph Signing', location_name: 'Stadium Cards', city: 'New York', state: 'NY', category: 'Autographs', date: '2025-03-20', is_featured: true },
  { id: '3', title: 'Fanatics Fest NYC 2025', location_name: 'Javits Center', city: 'New York', state: 'NY', category: 'Card Shows', date: '2025-04-05', is_featured: true },
  { id: '4', title: 'Brooklyn Card Show', location_name: 'Brooklyn Expo Center', city: 'Brooklyn', state: 'NY', category: 'Card Shows', date: '2025-04-12', is_featured: false },
  { id: '5', title: 'NJ Sports Collectors Convention', location_name: 'Raritan Center', city: 'Edison', state: 'NJ', category: 'Card Shows', date: '2025-04-19', is_featured: false },
  { id: '6', title: 'Tom Brady Signing Experience', location_name: 'MSG Fan Shop', city: 'New York', state: 'NY', category: 'Autographs', date: '2025-04-26', is_featured: true },
  { id: '7', title: 'Upper East Side Card Fair', location_name: 'Park Avenue Armory', city: 'New York', state: 'NY', category: 'Card Shows', date: '2025-05-03', is_featured: false },
  { id: '8', title: 'Hoboken Sports Memorabilia Expo', location_name: 'Hoboken Terminal', city: 'Hoboken', state: 'NJ', category: 'Card Shows', date: '2025-05-10', is_featured: false },
]

const CATEGORIES = ['All', 'Card Shows', 'Autographs', 'Athlete Appearances', 'Auctions']

function EventCard({ event }: { event: typeof EVENTS[0] }) {
  const date = new Date(event.date)
  const month = date.toLocaleString('default', { month: 'short' }).toUpperCase()
  const day = date.getDate()
  return (
    <TouchableOpacity style={s.card} activeOpacity={0.8}>
      <View style={s.cardInner}>
        <View style={{ flex: 1, marginRight: 12 }}>
          <Text style={s.cardTitle} numberOfLines={2}>{event.title}</Text>
          <Text style={s.cardSub}>{event.location_name} · {event.city}, {event.state}</Text>
          <View style={{ flexDirection: 'row', marginTop: 8, gap: 8 }}>
            <View style={s.pill}><Text style={s.pillText}>{event.category}</Text></View>
            {event.is_featured && (
              <View style={[s.pill, { backgroundColor: 'rgba(255,107,53,0.2)' }]}>
                <Text style={[s.pillText, { color: '#FF6B35' }]}>⭐ Featured</Text>
              </View>
            )}
          </View>
        </View>
        <View style={s.dateBadge}>
          <Text style={s.dateMonth}>{month}</Text>
          <Text style={s.dateDay}>{day}</Text>
        </View>
      </View>
    </TouchableOpacity>
  )
}

export default function HomeScreen() {
  return (
    <SafeAreaView style={s.safe}>
      <ScrollView style={{ flex: 1 }} showsVerticalScrollIndicator={false}>
        <View style={s.header}>
          <View>
            <Text style={s.headerSub}>Welcome back</Text>
            <Text style={s.headerTitle}>Discover Events</Text>
          </View>
          <TouchableOpacity style={s.notifBtn}>
            <Ionicons name="notifications-outline" size={22} color="#FF6B35" />
          </TouchableOpacity>
        </View>

        <TouchableOpacity style={s.search}>
          <Ionicons name="search" size={18} color="#888" />
          <Text style={s.searchText}>Search events, athletes...</Text>
        </TouchableOpacity>

        <ScrollView horizontal showsHorizontalScrollIndicator={false} style={{ marginBottom: 20 }} contentContainerStyle={{ paddingHorizontal: 20, gap: 8 }}>
          {CATEGORIES.map((cat) => (
            <TouchableOpacity key={cat} style={[s.catPill, cat === 'All' && s.catPillActive]}>
              <Text style={[s.catPillText, cat === 'All' && { color: '#fff' }]}>{cat}</Text>
            </TouchableOpacity>
          ))}
        </ScrollView>

        <View style={{ paddingHorizontal: 20 }}>
          {EVENTS.map((event) => <EventCard key={event.id} event={event} />)}
        </View>
      </ScrollView>
    </SafeAreaView>
  )
}

const s = StyleSheet.create({
  safe: { flex: 1, backgroundColor: '#0A0A0A' },
  header: { paddingHorizontal: 20, paddingTop: 16, paddingBottom: 8, flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between' },
  headerSub: { color: '#888', fontSize: 13 },
  headerTitle: { color: '#fff', fontSize: 24, fontWeight: 'bold' },
  notifBtn: { backgroundColor: '#1A1A1A', padding: 12, borderRadius: 100, borderWidth: 1, borderColor: '#2A2A2A' },
  search: { marginHorizontal: 20, marginTop: 12, marginBottom: 20, backgroundColor: '#1A1A1A', borderWidth: 1, borderColor: '#2A2A2A', borderRadius: 16, flexDirection: 'row', alignItems: 'center', paddingHorizontal: 16, paddingVertical: 12 },
  searchText: { color: '#888', marginLeft: 8, fontSize: 15 },
  catPill: { paddingHorizontal: 16, paddingVertical: 8, borderRadius: 100, backgroundColor: '#1A1A1A', borderWidth: 1, borderColor: '#2A2A2A' },
  catPillActive: { backgroundColor: '#FF6B35', borderColor: '#FF6B35' },
  catPillText: { color: '#888', fontSize: 13, fontWeight: '600' },
  card: { backgroundColor: '#1A1A1A', borderRadius: 16, marginBottom: 16, borderWidth: 1, borderColor: '#2A2A2A' },
  cardInner: { padding: 16, flexDirection: 'row', alignItems: 'flex-start' },
  cardTitle: { color: '#fff', fontWeight: 'bold', fontSize: 16, lineHeight: 22 },
  cardSub: { color: '#888', fontSize: 13, marginTop: 4 },
  pill: { backgroundColor: '#2A2A2A', borderRadius: 100, paddingHorizontal: 10, paddingVertical: 4 },
  pillText: { color: '#FF6B35', fontSize: 11, fontWeight: '600' },
  dateBadge: { backgroundColor: '#FF6B35', borderRadius: 12, paddingHorizontal: 10, paddingVertical: 8, alignItems: 'center', minWidth: 52 },
  dateMonth: { color: '#fff', fontSize: 11, fontWeight: 'bold' },
  dateDay: { color: '#fff', fontSize: 22, fontWeight: 'bold', lineHeight: 28 },
})
EOF

# ── Explore screen ──
cat > 'app/(tabs)/explore.tsx' << 'EOF'
import { View, Text, TouchableOpacity, StyleSheet } from 'react-native'
import { SafeAreaView } from 'react-native-safe-area-context'
import { Ionicons } from '@expo/vector-icons'

export default function ExploreScreen() {
  return (
    <SafeAreaView style={s.safe}>
      <View style={s.header}>
        <Text style={s.title}>Explore</Text>
        <Text style={s.sub}>Events near you</Text>
      </View>
      <TouchableOpacity style={s.search}>
        <Ionicons name="search" size={18} color="#888" />
        <Text style={s.searchText}>Search by city, zip, or venue...</Text>
      </TouchableOpacity>
      <View style={s.mapBox}>
        <Ionicons name="map-outline" size={64} color="#2A2A2A" />
        <Text style={s.mapText}>Map coming soon</Text>
        <Text style={s.mapSub}>Events will appear as pins on the map</Text>
      </View>
    </SafeAreaView>
  )
}

const s = StyleSheet.create({
  safe: { flex: 1, backgroundColor: '#0A0A0A' },
  header: { paddingHorizontal: 20, paddingTop: 16, paddingBottom: 16 },
  title: { color: '#fff', fontSize: 24, fontWeight: 'bold' },
  sub: { color: '#888', fontSize: 13, marginTop: 4 },
  search: { marginHorizontal: 20, marginBottom: 16, backgroundColor: '#1A1A1A', borderWidth: 1, borderColor: '#2A2A2A', borderRadius: 16, flexDirection: 'row', alignItems: 'center', paddingHorizontal: 16, paddingVertical: 12 },
  searchText: { color: '#888', marginLeft: 8, fontSize: 15 },
  mapBox: { flex: 1, marginHorizontal: 20, marginBottom: 20, backgroundColor: '#1A1A1A', borderRadius: 16, borderWidth: 1, borderColor: '#2A2A2A', alignItems: 'center', justifyContent: 'center' },
  mapText: { color: '#888', marginTop: 12, fontWeight: '600', fontSize: 16 },
  mapSub: { color: '#555', fontSize: 13, marginTop: 4, textAlign: 'center', paddingHorizontal: 40 },
})
EOF

# ── Saved screen ──
cat > 'app/(tabs)/saved.tsx' << 'EOF'
import { View, Text, TouchableOpacity, StyleSheet } from 'react-native'
import { SafeAreaView } from 'react-native-safe-area-context'
import { Ionicons } from '@expo/vector-icons'

export default function SavedScreen() {
  return (
    <SafeAreaView style={s.safe}>
      <View style={s.header}>
        <Text style={s.title}>Saved</Text>
        <Text style={s.sub}>Events you're watching</Text>
      </View>
      <View style={s.center}>
        <View style={s.iconBox}>
          <Ionicons name="bookmark-outline" size={48} color="#FF6B35" />
        </View>
        <Text style={s.big}>No saved events yet</Text>
        <Text style={s.dim}>Tap the bookmark icon on any event to save it here</Text>
        <TouchableOpacity style={s.btn}>
          <Text style={s.btnText}>Browse Events</Text>
        </TouchableOpacity>
      </View>
    </SafeAreaView>
  )
}

const s = StyleSheet.create({
  safe: { flex: 1, backgroundColor: '#0A0A0A' },
  header: { paddingHorizontal: 20, paddingTop: 16, paddingBottom: 16 },
  title: { color: '#fff', fontSize: 24, fontWeight: 'bold' },
  sub: { color: '#888', fontSize: 13, marginTop: 4 },
  center: { flex: 1, alignItems: 'center', justifyContent: 'center', paddingBottom: 80 },
  iconBox: { backgroundColor: '#1A1A1A', padding: 24, borderRadius: 100, marginBottom: 16, borderWidth: 1, borderColor: '#2A2A2A' },
  big: { color: '#fff', fontSize: 20, fontWeight: 'bold' },
  dim: { color: '#888', fontSize: 13, marginTop: 8, textAlign: 'center', paddingHorizontal: 40 },
  btn: { marginTop: 24, backgroundColor: '#FF6B35', paddingHorizontal: 24, paddingVertical: 12, borderRadius: 100 },
  btnText: { color: '#fff', fontWeight: 'bold' },
})
EOF

# ── Profile screen ──
cat > 'app/(tabs)/profile.tsx' << 'EOF'
import { View, Text, TouchableOpacity, ScrollView, StyleSheet } from 'react-native'
import { SafeAreaView } from 'react-native-safe-area-context'
import { Ionicons } from '@expo/vector-icons'

const MENU_ITEMS = [
  { icon: 'notifications-outline', label: 'Notification Preferences', danger: false },
  { icon: 'heart-outline', label: 'My Interests', danger: false },
  { icon: 'location-outline', label: 'My Location', danger: false },
  { icon: 'shield-checkmark-outline', label: 'Privacy & Security', danger: false },
  { icon: 'help-circle-outline', label: 'Help & Support', danger: false },
  { icon: 'log-out-outline', label: 'Sign Out', danger: true },
]

export default function ProfileScreen() {
  return (
    <SafeAreaView style={s.safe}>
      <ScrollView>
        <View style={s.header}><Text style={s.title}>Profile</Text></View>
        <View style={s.avatarSection}>
          <View style={s.avatar}>
            <Ionicons name="person" size={40} color="#888" />
          </View>
          <Text style={s.name}>Sign in to get started</Text>
          <Text style={s.sub}>Personalize your TROV experience</Text>
          <TouchableOpacity style={s.signIn}>
            <Text style={s.signInText}>Sign In with Apple</Text>
          </TouchableOpacity>
        </View>
        <View style={s.menu}>
          {MENU_ITEMS.map((item, i) => (
            <TouchableOpacity key={item.label} style={[s.menuItem, i < MENU_ITEMS.length - 1 && s.borderBottom]} activeOpacity={0.7}>
              <Ionicons name={item.icon as any} size={20} color={item.danger ? '#FF4444' : '#888'} />
              <Text style={[s.menuLabel, item.danger && { color: '#FF4444' }]}>{item.label}</Text>
              {!item.danger && <Ionicons name="chevron-forward" size={16} color="#444" />}
            </TouchableOpacity>
          ))}
        </View>
        <Text style={s.version}>TROV v1.0.0-beta</Text>
      </ScrollView>
    </SafeAreaView>
  )
}

const s = StyleSheet.create({
  safe: { flex: 1, backgroundColor: '#0A0A0A' },
  header: { paddingHorizontal: 20, paddingTop: 16, paddingBottom: 24 },
  title: { color: '#fff', fontSize: 24, fontWeight: 'bold' },
  avatarSection: { alignItems: 'center', paddingBottom: 32 },
  avatar: { width: 96, height: 96, borderRadius: 48, backgroundColor: '#2A2A2A', alignItems: 'center', justifyContent: 'center', borderWidth: 2, borderColor: '#FF6B35', marginBottom: 12 },
  name: { color: '#fff', fontSize: 20, fontWeight: 'bold' },
  sub: { color: '#888', fontSize: 13, marginTop: 4 },
  signIn: { marginTop: 16, backgroundColor: '#1A1A1A', paddingHorizontal: 32, paddingVertical: 14, borderRadius: 100, borderWidth: 1, borderColor: '#FF6B35', flexDirection: 'row', alignItems: 'center' },
  signInText: { color: '#fff', fontWeight: 'bold', fontSize: 15 },
  menu: { marginHorizontal: 20, backgroundColor: '#1A1A1A', borderRadius: 16, borderWidth: 1, borderColor: '#2A2A2A', overflow: 'hidden' },
  menuItem: { flexDirection: 'row', alignItems: 'center', paddingHorizontal: 20, paddingVertical: 16 },
  borderBottom: { borderBottomWidth: 1, borderBottomColor: '#2A2A2A' },
  menuLabel: { color: '#fff', fontSize: 15, fontWeight: '500', flex: 1, marginLeft: 12 },
  version: { textAlign: 'center', color: '#444', fontSize: 11, marginTop: 24, marginBottom: 32 },
})
EOF

# Remove global.css import if it exists anywhere
grep -rl "global.css" app/ 2>/dev/null | xargs sed -i '' "s/import '..\/global.css'//g" 2>/dev/null || true
grep -rl "global.css" app/ 2>/dev/null | xargs sed -i '' "s/import '.\/global.css'//g" 2>/dev/null || true

echo ""
echo "✅ Ultra-safe version written. Starting in Expo Go mode..."
echo ""
npx expo start --go --clear
