#!/bin/bash
set -e
cd "$HOME/Projects/trov-app"

# Kill everything on these ports
kill $(lsof -t -i:8081) 2>/dev/null || true
kill $(lsof -t -i:8082) 2>/dev/null || true
sleep 1

echo "→ Writing minimal app.json (no asset references)..."
cat > app.json << 'EOF'
{
  "expo": {
    "name": "TROV",
    "slug": "trov-app",
    "version": "1.0.0",
    "orientation": "portrait",
    "scheme": "trov",
    "userInterfaceStyle": "dark",
    "newArchEnabled": true,
    "ios": {
      "supportsTablet": false,
      "bundleIdentifier": "com.trov.app"
    },
    "android": {
      "package": "com.trov.app"
    }
  }
}
EOF

echo "→ Rewriting babel config (clean)..."
cat > babel.config.js << 'EOF'
module.exports = function (api) {
  api.cache(true);
  return { presets: ['babel-preset-expo'] };
};
EOF

echo "→ Rewriting metro config (clean)..."
cat > metro.config.js << 'EOF'
const { getDefaultConfig } = require("expo/metro-config");
module.exports = getDefaultConfig(__dirname);
EOF

echo "→ Rewriting root layout (no external imports)..."
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

echo "→ Rewriting tab layout..."
cat > 'app/(tabs)/_layout.tsx' << 'EOF'
import { Tabs } from 'expo-router'
import { Ionicons } from '@expo/vector-icons'

export default function TabLayout() {
  return (
    <Tabs screenOptions={{
      headerShown: false,
      tabBarStyle: { backgroundColor: '#0A0A0A', borderTopColor: '#1A1A1A', height: 80, paddingBottom: 8 },
      tabBarActiveTintColor: '#FF6B35',
      tabBarInactiveTintColor: '#666',
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

echo "→ Rewriting home screen..."
cat > 'app/(tabs)/index.tsx' << 'EOF'
import { View, Text, ScrollView, TouchableOpacity, StyleSheet } from 'react-native'
import { SafeAreaView } from 'react-native-safe-area-context'
import { Ionicons } from '@expo/vector-icons'

const EVENTS = [
  { id: '1', title: 'Meadowlands Sports Card & Memorabilia Show', venue: 'Meadowlands Expo Center', city: 'Secaucus, NJ', cat: 'Card Shows', month: 'MAR', day: 15, featured: true },
  { id: '2', title: 'Derek Jeter Autograph Signing', venue: 'Stadium Cards', city: 'New York, NY', cat: 'Autographs', month: 'MAR', day: 20, featured: true },
  { id: '3', title: 'Fanatics Fest NYC 2025', venue: 'Javits Center', city: 'New York, NY', cat: 'Card Shows', month: 'APR', day: 5, featured: true },
  { id: '4', title: 'Brooklyn Card Show', venue: 'Brooklyn Expo Center', city: 'Brooklyn, NY', cat: 'Card Shows', month: 'APR', day: 12, featured: false },
  { id: '5', title: 'Tom Brady Signing Experience', venue: 'MSG Fan Shop', city: 'New York, NY', cat: 'Autographs', month: 'APR', day: 26, featured: true },
  { id: '6', title: 'NJ Sports Collectors Convention', venue: 'Raritan Center', city: 'Edison, NJ', cat: 'Card Shows', month: 'MAY', day: 3, featured: false },
]

export default function HomeScreen() {
  return (
    <SafeAreaView style={s.safe}>
      <ScrollView showsVerticalScrollIndicator={false}>
        <View style={s.header}>
          <View>
            <Text style={s.sub}>NYC / NJ</Text>
            <Text style={s.title}>Discover Events</Text>
          </View>
          <TouchableOpacity style={s.bell}><Ionicons name="notifications-outline" size={20} color="#FF6B35" /></TouchableOpacity>
        </View>

        <TouchableOpacity style={s.search}>
          <Ionicons name="search" size={16} color="#555" />
          <Text style={s.searchTxt}>Search events, athletes...</Text>
        </TouchableOpacity>

        <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={s.cats}>
          {['All','Card Shows','Autographs','Appearances'].map((c,i) => (
            <TouchableOpacity key={c} style={[s.cat, i===0 && s.catOn]}>
              <Text style={[s.catTxt, i===0 && s.catTxtOn]}>{c}</Text>
            </TouchableOpacity>
          ))}
        </ScrollView>

        <View style={s.cards}>
          {EVENTS.map(e => (
            <TouchableOpacity key={e.id} style={s.card} activeOpacity={0.8}>
              <View style={s.cardBody}>
                <View style={{flex:1, marginRight:12}}>
                  <Text style={s.cardTitle} numberOfLines={2}>{e.title}</Text>
                  <Text style={s.cardVenue}>{e.venue}</Text>
                  <Text style={s.cardCity}>{e.city}</Text>
                  <View style={s.pills}>
                    <View style={s.pill}><Text style={s.pillTxt}>{e.cat}</Text></View>
                    {e.featured && <View style={s.pillFeat}><Text style={s.pillFeatTxt}>⭐ Featured</Text></View>}
                  </View>
                </View>
                <View style={s.date}>
                  <Text style={s.dateM}>{e.month}</Text>
                  <Text style={s.dateD}>{e.day}</Text>
                </View>
              </View>
            </TouchableOpacity>
          ))}
        </View>
      </ScrollView>
    </SafeAreaView>
  )
}

const s = StyleSheet.create({
  safe: { flex:1, backgroundColor:'#000' },
  header: { flexDirection:'row', alignItems:'center', justifyContent:'space-between', paddingHorizontal:20, paddingTop:16, paddingBottom:12 },
  sub: { color:'#555', fontSize:12, fontWeight:'600', letterSpacing:1 },
  title: { color:'#fff', fontSize:26, fontWeight:'800', marginTop:2 },
  bell: { backgroundColor:'#111', padding:10, borderRadius:50, borderWidth:1, borderColor:'#222' },
  search: { marginHorizontal:20, marginBottom:16, backgroundColor:'#111', borderWidth:1, borderColor:'#222', borderRadius:14, flexDirection:'row', alignItems:'center', paddingHorizontal:14, paddingVertical:11 },
  searchTxt: { color:'#555', marginLeft:8, fontSize:14 },
  cats: { paddingHorizontal:20, gap:8, marginBottom:20 },
  cat: { paddingHorizontal:16, paddingVertical:8, borderRadius:50, backgroundColor:'#111', borderWidth:1, borderColor:'#222' },
  catOn: { backgroundColor:'#FF6B35', borderColor:'#FF6B35' },
  catTxt: { color:'#666', fontSize:13, fontWeight:'600' },
  catTxtOn: { color:'#fff' },
  cards: { paddingHorizontal:20, paddingBottom:24 },
  card: { backgroundColor:'#111', borderRadius:16, marginBottom:12, borderWidth:1, borderColor:'#1A1A1A' },
  cardBody: { padding:16, flexDirection:'row' },
  cardTitle: { color:'#fff', fontSize:15, fontWeight:'700', lineHeight:21 },
  cardVenue: { color:'#555', fontSize:12, marginTop:4 },
  cardCity: { color:'#444', fontSize:12 },
  pills: { flexDirection:'row', gap:6, marginTop:10 },
  pill: { backgroundColor:'#1A1A1A', borderRadius:50, paddingHorizontal:10, paddingVertical:4 },
  pillTxt: { color:'#FF6B35', fontSize:11, fontWeight:'600' },
  pillFeat: { backgroundColor:'rgba(255,107,53,0.15)', borderRadius:50, paddingHorizontal:10, paddingVertical:4 },
  pillFeatTxt: { color:'#FF6B35', fontSize:11, fontWeight:'600' },
  date: { backgroundColor:'#FF6B35', borderRadius:12, paddingHorizontal:10, paddingVertical:8, alignItems:'center', minWidth:50, justifyContent:'center' },
  dateM: { color:'#fff', fontSize:10, fontWeight:'700', letterSpacing:0.5 },
  dateD: { color:'#fff', fontSize:22, fontWeight:'800', lineHeight:26 },
})
EOF

echo "→ Rewriting explore screen..."
cat > 'app/(tabs)/explore.tsx' << 'EOF'
import { View, Text, StyleSheet } from 'react-native'
import { SafeAreaView } from 'react-native-safe-area-context'
import { Ionicons } from '@expo/vector-icons'
export default function ExploreScreen() {
  return (
    <SafeAreaView style={{flex:1,backgroundColor:'#000'}}>
      <View style={{padding:20}}><Text style={{color:'#fff',fontSize:26,fontWeight:'800'}}>Explore</Text></View>
      <View style={{flex:1,margin:20,backgroundColor:'#111',borderRadius:16,borderWidth:1,borderColor:'#1A1A1A',alignItems:'center',justifyContent:'center'}}>
        <Ionicons name="map-outline" size={56} color="#222" />
        <Text style={{color:'#444',marginTop:12,fontWeight:'600'}}>Map coming soon</Text>
      </View>
    </SafeAreaView>
  )
}
EOF

echo "→ Rewriting saved screen..."
cat > 'app/(tabs)/saved.tsx' << 'EOF'
import { View, Text, TouchableOpacity } from 'react-native'
import { SafeAreaView } from 'react-native-safe-area-context'
import { Ionicons } from '@expo/vector-icons'
export default function SavedScreen() {
  return (
    <SafeAreaView style={{flex:1,backgroundColor:'#000'}}>
      <View style={{padding:20}}><Text style={{color:'#fff',fontSize:26,fontWeight:'800'}}>Saved</Text></View>
      <View style={{flex:1,alignItems:'center',justifyContent:'center',paddingBottom:80}}>
        <View style={{backgroundColor:'#111',padding:24,borderRadius:100,borderWidth:1,borderColor:'#1A1A1A',marginBottom:16}}>
          <Ionicons name="bookmark-outline" size={44} color="#FF6B35" />
        </View>
        <Text style={{color:'#fff',fontSize:18,fontWeight:'700'}}>No saved events yet</Text>
        <Text style={{color:'#444',fontSize:13,marginTop:8,textAlign:'center',paddingHorizontal:40}}>Tap the bookmark on any event</Text>
      </View>
    </SafeAreaView>
  )
}
EOF

echo "→ Rewriting profile screen..."
cat > 'app/(tabs)/profile.tsx' << 'EOF'
import { View, Text, TouchableOpacity, ScrollView } from 'react-native'
import { SafeAreaView } from 'react-native-safe-area-context'
import { Ionicons } from '@expo/vector-icons'
export default function ProfileScreen() {
  return (
    <SafeAreaView style={{flex:1,backgroundColor:'#000'}}>
      <ScrollView>
        <View style={{padding:20}}><Text style={{color:'#fff',fontSize:26,fontWeight:'800'}}>Profile</Text></View>
        <View style={{alignItems:'center',paddingBottom:32}}>
          <View style={{width:88,height:88,borderRadius:44,backgroundColor:'#1A1A1A',alignItems:'center',justifyContent:'center',borderWidth:2,borderColor:'#FF6B35',marginBottom:12}}>
            <Ionicons name="person" size={36} color="#555" />
          </View>
          <Text style={{color:'#fff',fontSize:18,fontWeight:'700'}}>Sign in to get started</Text>
          <TouchableOpacity style={{marginTop:16,backgroundColor:'#FF6B35',paddingHorizontal:28,paddingVertical:12,borderRadius:50}}>
            <Text style={{color:'#fff',fontWeight:'700'}}>Sign In with Apple</Text>
          </TouchableOpacity>
        </View>
        <Text style={{textAlign:'center',color:'#333',fontSize:11,marginBottom:24}}>TROV v1.0.0-beta</Text>
      </ScrollView>
    </SafeAreaView>
  )
}
EOF

echo ""
echo "✅ All files rewritten. Starting clean..."
npx expo start --go --clear
