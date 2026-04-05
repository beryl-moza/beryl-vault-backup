#!/bin/bash
cd "$HOME/Projects/trov-app"

kill $(lsof -t -i:8081) 2>/dev/null || true
kill $(lsof -t -i:8082) 2>/dev/null || true
sleep 1

echo "→ Writing all TROV source files..."

python3 << 'PYEOF'
import os

os.makedirs('contexts', exist_ok=True)
os.makedirs('constants', exist_ok=True)
os.makedirs('app/(tabs)', exist_ok=True)

# ─────────────────────────────────────────────
# contexts/SavedContext.tsx
# ─────────────────────────────────────────────
with open('contexts/SavedContext.tsx', 'w') as f:
    f.write("""import React, { createContext, useContext, useState } from 'react'

interface SavedContextType {
  savedIds: string[]
  toggle: (id: string) => void
  isSaved: (id: string) => boolean
}

export const SavedContext = createContext<SavedContextType>({
  savedIds: [],
  toggle: () => {},
  isSaved: () => false,
})

export function SavedProvider({ children }: { children: React.ReactNode }) {
  const [savedIds, setSavedIds] = useState<string[]>([])

  const toggle = (id: string) => {
    setSavedIds(prev =>
      prev.includes(id) ? prev.filter(x => x !== id) : [...prev, id]
    )
  }

  const isSaved = (id: string) => savedIds.includes(id)

  return (
    <SavedContext.Provider value={{ savedIds, toggle, isSaved }}>
      {children}
    </SavedContext.Provider>
  )
}

export function useSaved() {
  return useContext(SavedContext)
}
""")

# ─────────────────────────────────────────────
# constants/events.ts
# ─────────────────────────────────────────────
with open('constants/events.ts', 'w') as f:
    f.write("""export type Category = 'Card Shows' | 'Autographs' | 'Appearances' | 'Auctions'

export interface TrovEvent {
  id: string
  title: string
  venue: string
  city: string
  state: string
  category: Category
  month: string
  day: number
  year: number
  featured: boolean
  price: string
  description: string
}

export const EVENTS: TrovEvent[] = [
  {
    id: '1',
    title: 'Fanatics Fest NYC 2026',
    venue: 'Javits Center',
    city: 'New York', state: 'NY',
    category: 'Card Shows',
    month: 'APR', day: 18, year: 2026,
    featured: true,
    price: 'From $35',
    description: 'The biggest sports collectibles event of the year returns to NYC with hundreds of vendors and celebrity appearances.',
  },
  {
    id: '2',
    title: 'Derek Jeter Autograph Signing',
    venue: 'Stadium Cards & Collectibles',
    city: 'New York', state: 'NY',
    category: 'Autographs',
    month: 'APR', day: 22, year: 2026,
    featured: true,
    price: '$249',
    description: 'Limited signing session with Derek Jeter. Official MLB authenticated autographs on your choice of item.',
  },
  {
    id: '3',
    title: 'Meadowlands Sports Card Show',
    venue: 'Meadowlands Expo Center',
    city: 'Secaucus', state: 'NJ',
    category: 'Card Shows',
    month: 'APR', day: 26, year: 2026,
    featured: false,
    price: '$10',
    description: 'Monthly card show with 200+ tables of sports cards, memorabilia, and collectibles from top dealers.',
  },
  {
    id: '4',
    title: 'Patrick Mahomes Signing Session',
    venue: 'Steiner Sports',
    city: 'New York', state: 'NY',
    category: 'Autographs',
    month: 'MAY', day: 3, year: 2026,
    featured: true,
    price: '$299',
    description: 'Exclusive signing with three-time Super Bowl champion Patrick Mahomes. Limited to 100 guests.',
  },
  {
    id: '5',
    title: 'Brooklyn Collectors Fair',
    venue: 'Brooklyn Navy Yard',
    city: 'Brooklyn', state: 'NY',
    category: 'Card Shows',
    month: 'MAY', day: 9, year: 2026,
    featured: false,
    price: '$12',
    description: 'Two-day fair featuring vintage cards, graded slabs, memorabilia, and open trading tables.',
  },
  {
    id: '6',
    title: 'NJ Sports Collectors Convention',
    venue: 'Raritan Center',
    city: 'Edison', state: 'NJ',
    category: 'Card Shows',
    month: 'MAY', day: 17, year: 2026,
    featured: false,
    price: '$8',
    description: 'Annual NJ convention with 300+ dealer tables covering all major sports and Pokémon.',
  },
  {
    id: '7',
    title: "Shaquille O'Neal Appearance",
    venue: 'Garden State Plaza',
    city: 'Paramus', state: 'NJ',
    category: 'Appearances',
    month: 'MAY', day: 24, year: 2026,
    featured: true,
    price: 'Free',
    description: 'Shaq makes a special mall appearance for meet & greet and photo ops with fans.',
  },
  {
    id: '8',
    title: 'Heritage Auctions Spring Showcase',
    venue: 'Marriott Marquis',
    city: 'New York', state: 'NY',
    category: 'Auctions',
    month: 'MAY', day: 29, year: 2026,
    featured: true,
    price: 'Free to attend',
    description: 'Live auction event with top-tier graded cards, vintage memorabilia, and authenticated signed items.',
  },
  {
    id: '9',
    title: 'Tom Brady Memorabilia Signing',
    venue: 'Legends NY',
    city: 'New York', state: 'NY',
    category: 'Autographs',
    month: 'JUN', day: 7, year: 2026,
    featured: true,
    price: '$399',
    description: 'Rare signing with the GOAT. Official Fanatics-authenticated items only. 75 spots available.',
  },
  {
    id: '10',
    title: 'Triboro Card Show',
    venue: 'Queens Center Mall',
    city: 'Elmhurst', state: 'NY',
    category: 'Card Shows',
    month: 'JUN', day: 14, year: 2026,
    featured: false,
    price: 'Free',
    description: 'Indoor card show open to the public. Tables for beginners and seasoned collectors alike.',
  },
  {
    id: '11',
    title: 'LeBron James Signing Event',
    venue: 'Prudential Center',
    city: 'Newark', state: 'NJ',
    category: 'Autographs',
    month: 'JUN', day: 21, year: 2026,
    featured: true,
    price: '$449',
    description: 'Pre-game exclusive signing with LeBron James before the summer showcase at the Prudential Center.',
  },
  {
    id: '12',
    title: 'Steph Curry Fan Meet & Greet',
    venue: 'Barclays Center',
    city: 'Brooklyn', state: 'NY',
    category: 'Appearances',
    month: 'JUN', day: 28, year: 2026,
    featured: false,
    price: '$75',
    description: 'Photo op and quick meet with Stephen Curry before the Warriors vs. Nets summer game.',
  },
  {
    id: '13',
    title: 'Summer Slab Auction',
    venue: 'PWCC Marketplace NYC',
    city: 'New York', state: 'NY',
    category: 'Auctions',
    month: 'JUL', day: 12, year: 2026,
    featured: false,
    price: 'Free to attend',
    description: 'High-grade PSA and BGS slabs up for live auction. Pokémon, basketball, baseball, and football.',
  },
  {
    id: '14',
    title: 'NJ Summer Blowout Card Show',
    venue: 'Pines Manor',
    city: 'Edison', state: 'NJ',
    category: 'Card Shows',
    month: 'JUL', day: 19, year: 2026,
    featured: false,
    price: '$8',
    description: 'Massive summer card show with special discount tables, mystery packs, and door prizes.',
  },
  {
    id: '15',
    title: 'Icons of the Game Signing',
    venue: 'Madison Square Garden',
    city: 'New York', state: 'NY',
    category: 'Autographs',
    month: 'JUL', day: 26, year: 2026,
    featured: true,
    price: 'From $149',
    description: 'Multi-athlete signing event at the Garden featuring 5 Hall of Famers across NFL, NBA, and MLB.',
  },
]

export const CATEGORIES: Category[] = ['Card Shows', 'Autographs', 'Appearances', 'Auctions']

export const CATEGORY_COLORS: Record<Category, string> = {
  'Card Shows':  '#FF6B35',
  'Autographs':  '#7B61FF',
  'Appearances': '#00C896',
  'Auctions':    '#FFB800',
}

export const CATEGORY_ICONS: Record<Category, string> = {
  'Card Shows':  'grid-outline',
  'Autographs':  'create-outline',
  'Appearances': 'people-outline',
  'Auctions':    'hammer-outline',
}
""")

# ─────────────────────────────────────────────
# app/_layout.tsx
# ─────────────────────────────────────────────
with open('app/_layout.tsx', 'w') as f:
    f.write("""import { Stack } from 'expo-router'
import { SavedProvider } from '../contexts/SavedContext'

export default function RootLayout() {
  return (
    <SavedProvider>
      <Stack screenOptions={{ headerShown: false }}>
        <Stack.Screen name="(tabs)" />
      </Stack>
    </SavedProvider>
  )
}
""")

# ─────────────────────────────────────────────
# app/(tabs)/_layout.tsx
# ─────────────────────────────────────────────
with open('app/(tabs)/_layout.tsx', 'w') as f:
    f.write("""import { Tabs } from 'expo-router'
import { Ionicons } from '@expo/vector-icons'

export default function TabLayout() {
  return (
    <Tabs
      screenOptions={{
        headerShown: false,
        tabBarStyle: {
          backgroundColor: '#000',
          borderTopColor: '#111',
          borderTopWidth: 1,
          height: 84,
          paddingBottom: 8,
          paddingTop: 4,
        },
        tabBarActiveTintColor: '#FF6B35',
        tabBarInactiveTintColor: '#444',
        tabBarLabelStyle: { fontSize: 11, fontWeight: '600' },
      }}
    >
      <Tabs.Screen
        name="index"
        options={{
          title: 'Home',
          tabBarIcon: ({ color, size, focused }) => (
            <Ionicons name={focused ? 'home' : 'home-outline'} size={size} color={color} />
          ),
        }}
      />
      <Tabs.Screen
        name="explore"
        options={{
          title: 'Explore',
          tabBarIcon: ({ color, size, focused }) => (
            <Ionicons name={focused ? 'compass' : 'compass-outline'} size={size} color={color} />
          ),
        }}
      />
      <Tabs.Screen
        name="saved"
        options={{
          title: 'Saved',
          tabBarIcon: ({ color, size, focused }) => (
            <Ionicons name={focused ? 'bookmark' : 'bookmark-outline'} size={size} color={color} />
          ),
        }}
      />
      <Tabs.Screen
        name="profile"
        options={{
          title: 'Profile',
          tabBarIcon: ({ color, size, focused }) => (
            <Ionicons name={focused ? 'person' : 'person-outline'} size={size} color={color} />
          ),
        }}
      />
    </Tabs>
  )
}
""")

# ─────────────────────────────────────────────
# app/(tabs)/index.tsx  — Home
# ─────────────────────────────────────────────
with open('app/(tabs)/index.tsx', 'w') as f:
    f.write("""import React, { useState } from 'react'
import {
  View, Text, ScrollView, TouchableOpacity, StyleSheet,
} from 'react-native'
import { SafeAreaView } from 'react-native-safe-area-context'
import { Ionicons } from '@expo/vector-icons'
import { useSaved } from '../../contexts/SavedContext'
import { EVENTS, CATEGORIES, CATEGORY_COLORS, CATEGORY_ICONS } from '../../constants/events'

const ALL_CATS = ['All', ...CATEGORIES]

export default function HomeScreen() {
  const [activeCat, setActiveCat] = useState('All')
  const { toggle, isSaved } = useSaved()

  const filtered = activeCat === 'All' ? EVENTS : EVENTS.filter(e => e.category === activeCat)
  const featured  = filtered.filter(e => e.featured)
  const upcoming  = filtered.filter(e => !e.featured)

  return (
    <SafeAreaView style={s.safe}>
      <ScrollView showsVerticalScrollIndicator={false} contentContainerStyle={{ paddingBottom: 20 }}>

        {/* ── Header ── */}
        <View style={s.header}>
          <View>
            <Text style={s.logo}>TROV</Text>
            <Text style={s.location}>📍 NYC / New Jersey</Text>
          </View>
          <TouchableOpacity style={s.iconBtn}>
            <Ionicons name="notifications-outline" size={22} color="#fff" />
          </TouchableOpacity>
        </View>

        {/* ── Search bar ── */}
        <TouchableOpacity style={s.search} activeOpacity={0.8}>
          <Ionicons name="search" size={16} color="#555" />
          <Text style={s.searchTxt}>Search events, athletes, venues...</Text>
        </TouchableOpacity>

        {/* ── Category filter ── */}
        <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={s.catRow}>
          {ALL_CATS.map(c => (
            <TouchableOpacity
              key={c}
              style={[s.catBtn, activeCat === c && s.catBtnOn]}
              onPress={() => setActiveCat(c)}
              activeOpacity={0.8}
            >
              <Text style={[s.catBtnTxt, activeCat === c && s.catBtnTxtOn]}>{c}</Text>
            </TouchableOpacity>
          ))}
        </ScrollView>

        {/* ── Featured horizontal scroll ── */}
        {featured.length > 0 && (
          <View style={s.section}>
            <Text style={s.sectionLabel}>⭐  FEATURED</Text>
            <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={s.featRow}>
              {featured.map(e => {
                const color = CATEGORY_COLORS[e.category as keyof typeof CATEGORY_COLORS]
                return (
                  <TouchableOpacity key={e.id} style={s.featCard} activeOpacity={0.85}>
                    {/* color block */}
                    <View style={[s.featImgBlock, { backgroundColor: color + '22' }]}>
                      <Ionicons name={CATEGORY_ICONS[e.category as keyof typeof CATEGORY_ICONS] as any} size={32} color={color} style={{ opacity: 0.6 }} />
                      <View style={[s.featCatBadge, { backgroundColor: color }]}>
                        <Text style={s.featCatTxt}>{e.category}</Text>
                      </View>
                    </View>
                    {/* body */}
                    <View style={s.featBody}>
                      <Text style={s.featTitle} numberOfLines={2}>{e.title}</Text>
                      <Text style={s.featVenue} numberOfLines={1}>{e.venue}</Text>
                      <View style={s.featFooter}>
                        <Text style={[s.featDate, { color }]}>{e.month} {e.day}</Text>
                        <View style={s.featRight}>
                          <Text style={s.featPrice}>{e.price}</Text>
                          <TouchableOpacity onPress={() => toggle(e.id)} hitSlop={{ top: 10, bottom: 10, left: 10, right: 10 }}>
                            <Ionicons
                              name={isSaved(e.id) ? 'bookmark' : 'bookmark-outline'}
                              size={18}
                              color={isSaved(e.id) ? '#FF6B35' : '#444'}
                            />
                          </TouchableOpacity>
                        </View>
                      </View>
                    </View>
                  </TouchableOpacity>
                )
              })}
            </ScrollView>
          </View>
        )}

        {/* ── Upcoming list ── */}
        {upcoming.length > 0 && (
          <View style={s.section}>
            <Text style={s.sectionLabel}>UPCOMING</Text>
            {upcoming.map(e => {
              const color = CATEGORY_COLORS[e.category as keyof typeof CATEGORY_COLORS]
              return (
                <TouchableOpacity key={e.id} style={s.listCard} activeOpacity={0.85}>
                  <View style={[s.listBar, { backgroundColor: color }]} />
                  <View style={s.listDate}>
                    <Text style={s.listDateM}>{e.month}</Text>
                    <Text style={s.listDateD}>{e.day}</Text>
                  </View>
                  <View style={s.listBody}>
                    <Text style={s.listTitle} numberOfLines={2}>{e.title}</Text>
                    <Text style={s.listVenue} numberOfLines={1}>{e.venue} · {e.city}, {e.state}</Text>
                    <View style={[s.listBadge, { backgroundColor: color + '22' }]}>
                      <Text style={[s.listBadgeTxt, { color }]}>{e.category}</Text>
                    </View>
                  </View>
                  <TouchableOpacity onPress={() => toggle(e.id)} style={s.listBookmark} hitSlop={{ top: 10, bottom: 10, left: 10, right: 10 }}>
                    <Ionicons
                      name={isSaved(e.id) ? 'bookmark' : 'bookmark-outline'}
                      size={20}
                      color={isSaved(e.id) ? '#FF6B35' : '#444'}
                    />
                  </TouchableOpacity>
                </TouchableOpacity>
              )
            })}
          </View>
        )}

        {filtered.length === 0 && (
          <View style={s.empty}>
            <Ionicons name="calendar-outline" size={48} color="#1A1A1A" />
            <Text style={s.emptyTxt}>No events in this category yet</Text>
          </View>
        )}

      </ScrollView>
    </SafeAreaView>
  )
}

const s = StyleSheet.create({
  safe:           { flex: 1, backgroundColor: '#000' },
  header:         { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', paddingHorizontal: 20, paddingTop: 8, paddingBottom: 12 },
  logo:           { color: '#fff', fontSize: 32, fontWeight: '900', letterSpacing: -1 },
  location:       { color: '#555', fontSize: 12, fontWeight: '500', marginTop: 1 },
  iconBtn:        { backgroundColor: '#0F0F0F', padding: 10, borderRadius: 50, borderWidth: 1, borderColor: '#222' },
  search:         { marginHorizontal: 20, marginBottom: 16, backgroundColor: '#0F0F0F', borderWidth: 1, borderColor: '#1E1E1E', borderRadius: 14, flexDirection: 'row', alignItems: 'center', paddingHorizontal: 14, paddingVertical: 12 },
  searchTxt:      { color: '#444', marginLeft: 8, fontSize: 14 },
  catRow:         { paddingHorizontal: 20, gap: 8, marginBottom: 24 },
  catBtn:         { paddingHorizontal: 16, paddingVertical: 8, borderRadius: 50, backgroundColor: '#0F0F0F', borderWidth: 1, borderColor: '#1E1E1E' },
  catBtnOn:       { backgroundColor: '#FF6B35', borderColor: '#FF6B35' },
  catBtnTxt:      { color: '#555', fontSize: 13, fontWeight: '600' },
  catBtnTxtOn:    { color: '#fff' },
  section:        { paddingHorizontal: 20, marginBottom: 28 },
  sectionLabel:   { color: '#444', fontSize: 11, fontWeight: '700', letterSpacing: 1, marginBottom: 12 },
  // Featured
  featRow:        { gap: 12 },
  featCard:       { width: 230, backgroundColor: '#0D0D0D', borderRadius: 18, borderWidth: 1, borderColor: '#1A1A1A', overflow: 'hidden' },
  featImgBlock:   { height: 110, alignItems: 'center', justifyContent: 'center' },
  featCatBadge:   { position: 'absolute', bottom: 10, left: 12, paddingHorizontal: 8, paddingVertical: 3, borderRadius: 50 },
  featCatTxt:     { color: '#fff', fontSize: 10, fontWeight: '700' },
  featBody:       { padding: 14 },
  featTitle:      { color: '#fff', fontSize: 14, fontWeight: '700', lineHeight: 19 },
  featVenue:      { color: '#555', fontSize: 12, marginTop: 4 },
  featFooter:     { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginTop: 10 },
  featDate:       { fontSize: 12, fontWeight: '800' },
  featRight:      { flexDirection: 'row', alignItems: 'center', gap: 10 },
  featPrice:      { color: '#666', fontSize: 11, fontWeight: '600' },
  // List cards
  listCard:       { flexDirection: 'row', backgroundColor: '#0D0D0D', borderRadius: 16, marginBottom: 10, borderWidth: 1, borderColor: '#1A1A1A', overflow: 'hidden', alignItems: 'center' },
  listBar:        { width: 4, alignSelf: 'stretch' },
  listDate:       { alignItems: 'center', paddingHorizontal: 14, paddingVertical: 16, minWidth: 56 },
  listDateM:      { color: '#555', fontSize: 10, fontWeight: '700', letterSpacing: 0.5 },
  listDateD:      { color: '#fff', fontSize: 22, fontWeight: '800' },
  listBody:       { flex: 1, paddingVertical: 14, paddingRight: 4 },
  listTitle:      { color: '#fff', fontSize: 14, fontWeight: '700', lineHeight: 19 },
  listVenue:      { color: '#555', fontSize: 11, marginTop: 3 },
  listBadge:      { alignSelf: 'flex-start', marginTop: 7, paddingHorizontal: 8, paddingVertical: 3, borderRadius: 50 },
  listBadgeTxt:   { fontSize: 10, fontWeight: '700' },
  listBookmark:   { paddingHorizontal: 16 },
  empty:          { alignItems: 'center', paddingVertical: 60 },
  emptyTxt:       { color: '#333', marginTop: 14, fontSize: 14 },
})
""")

# ─────────────────────────────────────────────
# app/(tabs)/explore.tsx
# ─────────────────────────────────────────────
with open('app/(tabs)/explore.tsx', 'w') as f:
    f.write("""import React, { useState } from 'react'
import {
  View, Text, ScrollView, TextInput, TouchableOpacity, StyleSheet,
} from 'react-native'
import { SafeAreaView } from 'react-native-safe-area-context'
import { Ionicons } from '@expo/vector-icons'
import { EVENTS, CATEGORIES, CATEGORY_COLORS, CATEGORY_ICONS } from '../../constants/events'

export default function ExploreScreen() {
  const [query, setQuery]           = useState('')
  const [activeCat, setActiveCat]   = useState<string | null>(null)

  const showResults = query.length >= 1 || activeCat !== null

  const results = EVENTS.filter(e => {
    const q = query.toLowerCase()
    const matchQ =
      q.length === 0 ||
      e.title.toLowerCase().includes(q) ||
      e.venue.toLowerCase().includes(q) ||
      e.city.toLowerCase().includes(q)
    const matchC = activeCat === null || e.category === activeCat
    return matchQ && matchC
  })

  return (
    <SafeAreaView style={s.safe}>
      <View style={s.header}>
        <Text style={s.title}>Explore</Text>
      </View>

      {/* Search input */}
      <View style={s.searchWrap}>
        <Ionicons name="search" size={16} color="#555" style={{ marginRight: 8 }} />
        <TextInput
          style={s.input}
          placeholder="Events, athletes, venues..."
          placeholderTextColor="#444"
          value={query}
          onChangeText={setQuery}
          returnKeyType="search"
          autoCapitalize="none"
          autoCorrect={false}
          clearButtonMode="while-editing"
        />
      </View>

      <ScrollView showsVerticalScrollIndicator={false} contentContainerStyle={{ paddingBottom: 30 }}>

        {/* Category tiles */}
        <View style={s.tilesSection}>
          <Text style={s.tilesLabel}>BROWSE BY CATEGORY</Text>
          <View style={s.tilesGrid}>
            {CATEGORIES.map(cat => {
              const color   = CATEGORY_COLORS[cat]
              const active  = activeCat === cat
              const count   = EVENTS.filter(e => e.category === cat).length
              return (
                <TouchableOpacity
                  key={cat}
                  style={[s.tile, { backgroundColor: color + '18', borderColor: active ? color : 'transparent', borderWidth: 2 }]}
                  onPress={() => setActiveCat(active ? null : cat)}
                  activeOpacity={0.8}
                >
                  <Ionicons name={CATEGORY_ICONS[cat] as any} size={28} color={color} />
                  <Text style={[s.tileName, { color }]}>{cat}</Text>
                  <Text style={s.tileCount}>{count} events</Text>
                </TouchableOpacity>
              )
            })}
          </View>
        </View>

        {/* Results */}
        {showResults && (
          <View style={s.results}>
            <Text style={s.resultsMeta}>
              {results.length} event{results.length !== 1 ? 's' : ''} found
            </Text>
            {results.length === 0 ? (
              <View style={s.noResults}>
                <Ionicons name="search-outline" size={44} color="#1A1A1A" />
                <Text style={s.noResultsTxt}>No events matched</Text>
              </View>
            ) : (
              results.map(e => {
                const color = CATEGORY_COLORS[e.category as keyof typeof CATEGORY_COLORS]
                return (
                  <TouchableOpacity key={e.id} style={s.resultCard} activeOpacity={0.8}>
                    <View style={[s.resultDot, { backgroundColor: color }]} />
                    <View style={s.resultBody}>
                      <Text style={s.resultTitle} numberOfLines={1}>{e.title}</Text>
                      <Text style={s.resultSub}>{e.venue} · {e.month} {e.day}</Text>
                    </View>
                    <Text style={[s.resultPrice, { color }]}>{e.price}</Text>
                  </TouchableOpacity>
                )
              })
            )}
          </View>
        )}

      </ScrollView>
    </SafeAreaView>
  )
}

const s = StyleSheet.create({
  safe:         { flex: 1, backgroundColor: '#000' },
  header:       { paddingHorizontal: 20, paddingTop: 8, paddingBottom: 12 },
  title:        { color: '#fff', fontSize: 32, fontWeight: '900', letterSpacing: -1 },
  searchWrap:   { marginHorizontal: 20, marginBottom: 20, backgroundColor: '#0F0F0F', borderWidth: 1, borderColor: '#1E1E1E', borderRadius: 14, flexDirection: 'row', alignItems: 'center', paddingHorizontal: 14, paddingVertical: 10 },
  input:        { flex: 1, color: '#fff', fontSize: 14, paddingVertical: 2 },
  tilesSection: { paddingHorizontal: 20, marginBottom: 24 },
  tilesLabel:   { color: '#444', fontSize: 11, fontWeight: '700', letterSpacing: 1, marginBottom: 12 },
  tilesGrid:    { flexDirection: 'row', flexWrap: 'wrap', gap: 12 },
  tile:         { width: '47%', padding: 16, borderRadius: 16, alignItems: 'flex-start' },
  tileName:     { fontSize: 14, fontWeight: '800', marginTop: 8 },
  tileCount:    { color: '#555', fontSize: 12, marginTop: 2 },
  results:      { paddingHorizontal: 20 },
  resultsMeta:  { color: '#444', fontSize: 12, fontWeight: '600', marginBottom: 10 },
  resultCard:   { flexDirection: 'row', alignItems: 'center', backgroundColor: '#0D0D0D', borderRadius: 14, marginBottom: 8, padding: 14, borderWidth: 1, borderColor: '#1A1A1A' },
  resultDot:    { width: 8, height: 8, borderRadius: 4, marginRight: 12, flexShrink: 0 },
  resultBody:   { flex: 1 },
  resultTitle:  { color: '#fff', fontSize: 14, fontWeight: '600' },
  resultSub:    { color: '#555', fontSize: 12, marginTop: 2 },
  resultPrice:  { fontSize: 12, fontWeight: '700', marginLeft: 8, flexShrink: 0 },
  noResults:    { alignItems: 'center', paddingVertical: 48 },
  noResultsTxt: { color: '#333', marginTop: 12, fontSize: 14 },
})
""")

# ─────────────────────────────────────────────
# app/(tabs)/saved.tsx
# ─────────────────────────────────────────────
with open('app/(tabs)/saved.tsx', 'w') as f:
    f.write("""import React from 'react'
import { View, Text, ScrollView, TouchableOpacity, StyleSheet } from 'react-native'
import { SafeAreaView } from 'react-native-safe-area-context'
import { Ionicons } from '@expo/vector-icons'
import { useSaved } from '../../contexts/SavedContext'
import { EVENTS, CATEGORY_COLORS } from '../../constants/events'

export default function SavedScreen() {
  const { savedIds, toggle } = useSaved()
  const saved = EVENTS.filter(e => savedIds.includes(e.id))

  return (
    <SafeAreaView style={s.safe}>
      <View style={s.header}>
        <Text style={s.title}>Saved</Text>
        {saved.length > 0 && (
          <View style={s.countPill}>
            <Text style={s.countTxt}>{saved.length}</Text>
          </View>
        )}
      </View>

      {saved.length === 0 ? (
        <View style={s.empty}>
          <View style={s.emptyCircle}>
            <Ionicons name="bookmark-outline" size={44} color="#FF6B35" />
          </View>
          <Text style={s.emptyTitle}>Nothing saved yet</Text>
          <Text style={s.emptyBody}>
            Tap the bookmark on any event{'\n'}to save it here
          </Text>
        </View>
      ) : (
        <ScrollView showsVerticalScrollIndicator={false} contentContainerStyle={s.list}>
          {saved.map(e => {
            const color = CATEGORY_COLORS[e.category as keyof typeof CATEGORY_COLORS]
            return (
              <TouchableOpacity key={e.id} style={s.card} activeOpacity={0.85}>
                <View style={[s.bar, { backgroundColor: color }]} />
                <View style={s.dateBlock}>
                  <Text style={s.dateM}>{e.month}</Text>
                  <Text style={s.dateD}>{e.day}</Text>
                </View>
                <View style={s.body}>
                  <Text style={s.cardTitle} numberOfLines={2}>{e.title}</Text>
                  <Text style={s.cardVenue} numberOfLines={1}>{e.venue} · {e.city}, {e.state}</Text>
                  <View style={[s.badge, { backgroundColor: color + '22' }]}>
                    <Text style={[s.badgeTxt, { color }]}>{e.category}</Text>
                  </View>
                </View>
                <View style={s.right}>
                  <Text style={[s.price, { color }]}>{e.price}</Text>
                  <TouchableOpacity onPress={() => toggle(e.id)} hitSlop={{ top: 10, bottom: 10, left: 10, right: 10 }}>
                    <Ionicons name="bookmark" size={22} color="#FF6B35" />
                  </TouchableOpacity>
                </View>
              </TouchableOpacity>
            )
          })}
        </ScrollView>
      )}
    </SafeAreaView>
  )
}

const s = StyleSheet.create({
  safe:        { flex: 1, backgroundColor: '#000' },
  header:      { flexDirection: 'row', alignItems: 'center', paddingHorizontal: 20, paddingTop: 8, paddingBottom: 16 },
  title:       { color: '#fff', fontSize: 32, fontWeight: '900', letterSpacing: -1 },
  countPill:   { marginLeft: 10, backgroundColor: '#FF6B35', borderRadius: 50, paddingHorizontal: 9, paddingVertical: 2 },
  countTxt:    { color: '#fff', fontSize: 12, fontWeight: '700' },
  empty:       { flex: 1, alignItems: 'center', justifyContent: 'center', paddingBottom: 80 },
  emptyCircle: { backgroundColor: '#0F0F0F', padding: 24, borderRadius: 100, borderWidth: 1, borderColor: '#1A1A1A', marginBottom: 20 },
  emptyTitle:  { color: '#fff', fontSize: 18, fontWeight: '700' },
  emptyBody:   { color: '#444', fontSize: 14, marginTop: 8, textAlign: 'center', lineHeight: 21 },
  list:        { paddingHorizontal: 20, paddingBottom: 30 },
  card:        { flexDirection: 'row', backgroundColor: '#0D0D0D', borderRadius: 16, marginBottom: 10, borderWidth: 1, borderColor: '#1A1A1A', overflow: 'hidden', alignItems: 'center' },
  bar:         { width: 4, alignSelf: 'stretch' },
  dateBlock:   { alignItems: 'center', paddingHorizontal: 14, paddingVertical: 16, minWidth: 56 },
  dateM:       { color: '#555', fontSize: 10, fontWeight: '700', letterSpacing: 0.5 },
  dateD:       { color: '#fff', fontSize: 22, fontWeight: '800' },
  body:        { flex: 1, paddingVertical: 14 },
  cardTitle:   { color: '#fff', fontSize: 14, fontWeight: '700', lineHeight: 19 },
  cardVenue:   { color: '#555', fontSize: 11, marginTop: 3 },
  badge:       { alignSelf: 'flex-start', marginTop: 7, paddingHorizontal: 8, paddingVertical: 3, borderRadius: 50 },
  badgeTxt:    { fontSize: 10, fontWeight: '700' },
  right:       { paddingHorizontal: 14, alignItems: 'center', gap: 8 },
  price:       { fontSize: 11, fontWeight: '700' },
})
""")

# ─────────────────────────────────────────────
# app/(tabs)/profile.tsx
# ─────────────────────────────────────────────
with open('app/(tabs)/profile.tsx', 'w') as f:
    f.write("""import React from 'react'
import { View, Text, ScrollView, TouchableOpacity, StyleSheet } from 'react-native'
import { SafeAreaView } from 'react-native-safe-area-context'
import { Ionicons } from '@expo/vector-icons'
import { useSaved } from '../../contexts/SavedContext'

const MENU = [
  {
    section: 'Account',
    items: [
      { icon: 'person-circle-outline', label: 'Sign In', sub: 'Sign in with Apple or email' },
      { icon: 'notifications-outline', label: 'Notifications', sub: 'Manage your alerts' },
    ],
  },
  {
    section: 'My Collection',
    items: [
      { icon: 'bookmark-outline', label: 'Saved Events', sub: '' },
      { icon: 'calendar-outline', label: 'Attending', sub: '0 upcoming' },
      { icon: 'time-outline', label: 'Past Events', sub: '0 attended' },
    ],
  },
  {
    section: 'App',
    items: [
      { icon: 'star-outline', label: 'Rate TROV', sub: 'Love the app? Tell us!' },
      { icon: 'share-social-outline', label: 'Share TROV', sub: 'Tell a fellow collector' },
      { icon: 'information-circle-outline', label: 'About', sub: 'v1.0.0-beta' },
    ],
  },
]

export default function ProfileScreen() {
  const { savedIds } = useSaved()

  return (
    <SafeAreaView style={s.safe}>
      <ScrollView showsVerticalScrollIndicator={false} contentContainerStyle={{ paddingBottom: 30 }}>

        <View style={s.header}>
          <Text style={s.title}>Profile</Text>
        </View>

        {/* Avatar + CTA */}
        <View style={s.hero}>
          <View style={s.avatar}>
            <Ionicons name="person" size={40} color="#333" />
          </View>
          <Text style={s.heroTitle}>Join TROV</Text>
          <Text style={s.heroSub}>
            Save events, track signings, and never miss a drop in NYC & NJ.
          </Text>
          <TouchableOpacity style={s.appleBtn} activeOpacity={0.88}>
            <Ionicons name="logo-apple" size={18} color="#000" />
            <Text style={s.appleTxt}>Sign in with Apple</Text>
          </TouchableOpacity>
          <TouchableOpacity style={s.emailBtn} activeOpacity={0.88}>
            <Text style={s.emailTxt}>Continue with Email</Text>
          </TouchableOpacity>
        </View>

        {/* Stats */}
        <View style={s.statsRow}>
          {[
            [String(savedIds.length), 'Saved'],
            ['0', 'Going'],
            ['0', 'Past'],
          ].map(([num, label]) => (
            <View key={label} style={s.stat}>
              <Text style={s.statNum}>{num}</Text>
              <Text style={s.statLabel}>{label}</Text>
            </View>
          ))}
        </View>

        {/* Menu */}
        {MENU.map(({ section, items }) => (
          <View key={section} style={s.menuGroup}>
            <Text style={s.menuGroupLabel}>{section.toUpperCase()}</Text>
            <View style={s.menuCard}>
              {items.map((item, idx) => (
                <TouchableOpacity
                  key={item.label}
                  style={[s.menuRow, idx > 0 && s.menuBorder]}
                  activeOpacity={0.7}
                >
                  <View style={s.menuIcon}>
                    <Ionicons name={item.icon as any} size={20} color="#FF6B35" />
                  </View>
                  <View style={s.menuText}>
                    <Text style={s.menuLabel}>{item.label}</Text>
                    {item.sub ? (
                      <Text style={s.menuSub}>
                        {item.label === 'Saved Events' ? savedIds.length + ' events saved' : item.sub}
                      </Text>
                    ) : null}
                  </View>
                  <Ionicons name="chevron-forward" size={16} color="#2A2A2A" />
                </TouchableOpacity>
              ))}
            </View>
          </View>
        ))}

        <Text style={s.footer}>TROV · NYC/NJ Collectibles · v1.0.0-beta</Text>

      </ScrollView>
    </SafeAreaView>
  )
}

const s = StyleSheet.create({
  safe:           { flex: 1, backgroundColor: '#000' },
  header:         { paddingHorizontal: 20, paddingTop: 8, paddingBottom: 4 },
  title:          { color: '#fff', fontSize: 32, fontWeight: '900', letterSpacing: -1 },
  hero:           { alignItems: 'center', paddingHorizontal: 24, paddingTop: 12, paddingBottom: 24 },
  avatar:         { width: 90, height: 90, borderRadius: 45, backgroundColor: '#0F0F0F', borderWidth: 2, borderColor: '#1A1A1A', alignItems: 'center', justifyContent: 'center', marginBottom: 16 },
  heroTitle:      { color: '#fff', fontSize: 22, fontWeight: '800' },
  heroSub:        { color: '#555', fontSize: 13, textAlign: 'center', marginTop: 8, lineHeight: 20, paddingHorizontal: 16 },
  appleBtn:       { marginTop: 20, backgroundColor: '#fff', flexDirection: 'row', alignItems: 'center', gap: 8, paddingHorizontal: 28, paddingVertical: 13, borderRadius: 50, width: '100%', justifyContent: 'center' },
  appleTxt:       { color: '#000', fontWeight: '700', fontSize: 15 },
  emailBtn:       { marginTop: 10, borderWidth: 1, borderColor: '#1E1E1E', paddingHorizontal: 28, paddingVertical: 13, borderRadius: 50, width: '100%', alignItems: 'center' },
  emailTxt:       { color: '#666', fontWeight: '600', fontSize: 14 },
  statsRow:       { flexDirection: 'row', marginHorizontal: 20, backgroundColor: '#0D0D0D', borderRadius: 18, borderWidth: 1, borderColor: '#1A1A1A', marginBottom: 28 },
  stat:           { flex: 1, alignItems: 'center', paddingVertical: 16 },
  statNum:        { color: '#fff', fontSize: 22, fontWeight: '800' },
  statLabel:      { color: '#555', fontSize: 12, marginTop: 2 },
  menuGroup:      { paddingHorizontal: 20, marginBottom: 16 },
  menuGroupLabel: { color: '#444', fontSize: 11, fontWeight: '700', letterSpacing: 1, marginBottom: 8 },
  menuCard:       { backgroundColor: '#0D0D0D', borderRadius: 18, borderWidth: 1, borderColor: '#1A1A1A', overflow: 'hidden' },
  menuRow:        { flexDirection: 'row', alignItems: 'center', padding: 14 },
  menuBorder:     { borderTopWidth: 1, borderTopColor: '#141414' },
  menuIcon:       { width: 36, height: 36, borderRadius: 10, backgroundColor: '#1A1A1A', alignItems: 'center', justifyContent: 'center', marginRight: 12 },
  menuText:       { flex: 1 },
  menuLabel:      { color: '#fff', fontSize: 14, fontWeight: '600' },
  menuSub:        { color: '#555', fontSize: 12, marginTop: 1 },
  footer:         { textAlign: 'center', color: '#222', fontSize: 11, marginTop: 8 },
})
""")

print("")
print("✅  All files written:")
print("   contexts/SavedContext.tsx")
print("   constants/events.ts  (15 events)")
print("   app/_layout.tsx")
print("   app/(tabs)/_layout.tsx")
print("   app/(tabs)/index.tsx  (Home)")
print("   app/(tabs)/explore.tsx")
print("   app/(tabs)/saved.tsx")
print("   app/(tabs)/profile.tsx")
PYEOF

echo ""
echo "→ Clearing Metro cache..."
rm -rf /tmp/metro-* 2>/dev/null || true
rm -rf "$TMPDIR/metro-*" 2>/dev/null || true

echo "→ Starting Expo in Expo Go mode..."
npx expo start --go --clear
