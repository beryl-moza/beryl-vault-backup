#!/bin/bash
cd "$HOME/Projects/trov-app"

kill $(lsof -t -i:8081) 2>/dev/null || true
kill $(lsof -t -i:8082) 2>/dev/null || true
sleep 1

echo "→ Writing TROV source files (no TypeScript complexity)..."

python3 << 'PYEOF'
import os

os.makedirs('contexts', exist_ok=True)
os.makedirs('constants', exist_ok=True)

# ── contexts/SavedContext.js ──────────────────────────────
with open('contexts/SavedContext.js', 'w') as f:
    f.write("""import React, { createContext, useContext, useState } from 'react'

const SavedContext = createContext({ savedIds: [], toggle: () => {}, isSaved: () => false })

export function SavedProvider({ children }) {
  const [savedIds, setSavedIds] = useState([])
  const toggle = (id) => setSavedIds(prev => prev.includes(id) ? prev.filter(x => x !== id) : [...prev, id])
  const isSaved = (id) => savedIds.includes(id)
  return <SavedContext.Provider value={{ savedIds, toggle, isSaved }}>{children}</SavedContext.Provider>
}

export function useSaved() { return useContext(SavedContext) }
""")

# ── constants/events.js ──────────────────────────────────
with open('constants/events.js', 'w') as f:
    f.write("""export const EVENTS = [
  { id:'1',  title:'Fanatics Fest NYC 2026',           venue:'Javits Center',              city:'New York',  state:'NY', category:'Card Shows',  month:'APR', day:18, featured:true,  price:'From $35' },
  { id:'2',  title:'Derek Jeter Autograph Signing',    venue:'Stadium Cards',              city:'New York',  state:'NY', category:'Autographs',  month:'APR', day:22, featured:true,  price:'$249' },
  { id:'3',  title:'Meadowlands Sports Card Show',     venue:'Meadowlands Expo Center',    city:'Secaucus',  state:'NJ', category:'Card Shows',  month:'APR', day:26, featured:false, price:'$10' },
  { id:'4',  title:'Patrick Mahomes Signing',          venue:'Steiner Sports',             city:'New York',  state:'NY', category:'Autographs',  month:'MAY', day:3,  featured:true,  price:'$299' },
  { id:'5',  title:'Brooklyn Collectors Fair',         venue:'Brooklyn Navy Yard',         city:'Brooklyn',  state:'NY', category:'Card Shows',  month:'MAY', day:9,  featured:false, price:'$12' },
  { id:'6',  title:'NJ Sports Collectors Convention', venue:'Raritan Center',             city:'Edison',    state:'NJ', category:'Card Shows',  month:'MAY', day:17, featured:false, price:'$8' },
  { id:'7',  title:"Shaquille O'Neal Appearance",     venue:'Garden State Plaza',         city:'Paramus',   state:'NJ', category:'Appearances', month:'MAY', day:24, featured:true,  price:'Free' },
  { id:'8',  title:'Heritage Auctions Spring Show',   venue:'Marriott Marquis',           city:'New York',  state:'NY', category:'Auctions',    month:'MAY', day:29, featured:true,  price:'Free' },
  { id:'9',  title:'Tom Brady Memorabilia Signing',   venue:'Legends NY',                 city:'New York',  state:'NY', category:'Autographs',  month:'JUN', day:7,  featured:true,  price:'$399' },
  { id:'10', title:'Triboro Card Show',               venue:'Queens Center Mall',         city:'Elmhurst',  state:'NY', category:'Card Shows',  month:'JUN', day:14, featured:false, price:'Free' },
  { id:'11', title:'LeBron James Signing Event',      venue:'Prudential Center',          city:'Newark',    state:'NJ', category:'Autographs',  month:'JUN', day:21, featured:true,  price:'$449' },
  { id:'12', title:'Steph Curry Meet & Greet',        venue:'Barclays Center',            city:'Brooklyn',  state:'NY', category:'Appearances', month:'JUN', day:28, featured:false, price:'$75' },
  { id:'13', title:'Summer Slab Auction',             venue:'PWCC Marketplace NYC',       city:'New York',  state:'NY', category:'Auctions',    month:'JUL', day:12, featured:false, price:'Free' },
  { id:'14', title:'Icons of the Game Signing',       venue:'Madison Square Garden',      city:'New York',  state:'NY', category:'Autographs',  month:'JUL', day:26, featured:true,  price:'From $149' },
]

export const CATEGORIES = ['Card Shows', 'Autographs', 'Appearances', 'Auctions']

export const CAT_COLOR = {
  'Card Shows':  '#FF6B35',
  'Autographs':  '#7B61FF',
  'Appearances': '#00C896',
  'Auctions':    '#FFB800',
}

export const CAT_ICON = {
  'Card Shows':  'grid-outline',
  'Autographs':  'create-outline',
  'Appearances': 'people-outline',
  'Auctions':    'hammer-outline',
}
""")

# ── app/_layout.tsx ──────────────────────────────────────
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

# ── app/(tabs)/_layout.tsx ───────────────────────────────
with open('app/(tabs)/_layout.tsx', 'w') as f:
    f.write("""import { Tabs } from 'expo-router'
import { Ionicons } from '@expo/vector-icons'

export default function TabLayout() {
  return (
    <Tabs screenOptions={{
      headerShown: false,
      tabBarStyle: { backgroundColor: '#000', borderTopColor: '#111', borderTopWidth: 1, height: 84, paddingBottom: 8 },
      tabBarActiveTintColor: '#FF6B35',
      tabBarInactiveTintColor: '#444',
      tabBarLabelStyle: { fontSize: 11, fontWeight: '600' },
    }}>
      <Tabs.Screen name="index"   options={{ title:'Home',    tabBarIcon:({color,size,focused}) => <Ionicons name={focused?'home':'home-outline'}         size={size} color={color}/> }}/>
      <Tabs.Screen name="explore" options={{ title:'Explore', tabBarIcon:({color,size,focused}) => <Ionicons name={focused?'compass':'compass-outline'}     size={size} color={color}/> }}/>
      <Tabs.Screen name="saved"   options={{ title:'Saved',   tabBarIcon:({color,size,focused}) => <Ionicons name={focused?'bookmark':'bookmark-outline'}   size={size} color={color}/> }}/>
      <Tabs.Screen name="profile" options={{ title:'Profile', tabBarIcon:({color,size,focused}) => <Ionicons name={focused?'person':'person-outline'}       size={size} color={color}/> }}/>
    </Tabs>
  )
}
""")

# ── app/(tabs)/index.tsx  HOME ────────────────────────────
with open('app/(tabs)/index.tsx', 'w') as f:
    f.write("""import React, { useState } from 'react'
import { View, Text, ScrollView, TouchableOpacity, StyleSheet } from 'react-native'
import { SafeAreaView } from 'react-native-safe-area-context'
import { Ionicons } from '@expo/vector-icons'
import { useSaved } from '../../contexts/SavedContext'
import { EVENTS, CATEGORIES, CAT_COLOR, CAT_ICON } from '../../constants/events'

const ALL = ['All', ...CATEGORIES]

export default function HomeScreen() {
  const [cat, setCat] = useState('All')
  const { toggle, isSaved } = useSaved()
  const filtered  = cat === 'All' ? EVENTS : EVENTS.filter(e => e.category === cat)
  const featured  = filtered.filter(e => e.featured)
  const upcoming  = filtered.filter(e => !e.featured)

  return (
    <SafeAreaView style={s.safe}>
      <ScrollView showsVerticalScrollIndicator={false} contentContainerStyle={{paddingBottom:24}}>

        <View style={s.header}>
          <View>
            <Text style={s.logo}>TROV</Text>
            <Text style={s.loc}>NYC / New Jersey</Text>
          </View>
          <TouchableOpacity style={s.bell}><Ionicons name="notifications-outline" size={22} color="#fff"/></TouchableOpacity>
        </View>

        <TouchableOpacity style={s.search}>
          <Ionicons name="search" size={16} color="#555"/>
          <Text style={s.searchTxt}>Search events, athletes, venues...</Text>
        </TouchableOpacity>

        <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={s.catRow}>
          {ALL.map(c => (
            <TouchableOpacity key={c} style={[s.catBtn, cat===c && s.catOn]} onPress={()=>setCat(c)}>
              <Text style={[s.catTxt, cat===c && s.catTxtOn]}>{c}</Text>
            </TouchableOpacity>
          ))}
        </ScrollView>

        {featured.length > 0 && (
          <View style={s.section}>
            <Text style={s.sLabel}>FEATURED</Text>
            <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={{gap:12}}>
              {featured.map(e => {
                const color = CAT_COLOR[e.category] || '#FF6B35'
                return (
                  <TouchableOpacity key={e.id} style={s.fCard}>
                    <View style={[s.fImg, {backgroundColor: color+'22'}]}>
                      <Ionicons name={CAT_ICON[e.category] || 'calendar-outline'} size={30} color={color} style={{opacity:0.7}}/>
                      <View style={[s.fBadge, {backgroundColor: color}]}>
                        <Text style={s.fBadgeTxt}>{e.category}</Text>
                      </View>
                    </View>
                    <View style={s.fBody}>
                      <Text style={s.fTitle} numberOfLines={2}>{e.title}</Text>
                      <Text style={s.fVenue} numberOfLines={1}>{e.venue}</Text>
                      <View style={s.fFooter}>
                        <Text style={[s.fDate, {color}]}>{e.month} {e.day}</Text>
                        <View style={{flexDirection:'row', alignItems:'center', gap:10}}>
                          <Text style={s.fPrice}>{e.price}</Text>
                          <TouchableOpacity onPress={()=>toggle(e.id)} hitSlop={{top:10,bottom:10,left:10,right:10}}>
                            <Ionicons name={isSaved(e.id)?'bookmark':'bookmark-outline'} size={18} color={isSaved(e.id)?'#FF6B35':'#444'}/>
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

        {upcoming.length > 0 && (
          <View style={s.section}>
            <Text style={s.sLabel}>UPCOMING</Text>
            {upcoming.map(e => {
              const color = CAT_COLOR[e.category] || '#FF6B35'
              return (
                <TouchableOpacity key={e.id} style={s.lCard}>
                  <View style={[s.lBar, {backgroundColor: color}]}/>
                  <View style={s.lDate}>
                    <Text style={s.lDateM}>{e.month}</Text>
                    <Text style={s.lDateD}>{e.day}</Text>
                  </View>
                  <View style={s.lBody}>
                    <Text style={s.lTitle} numberOfLines={2}>{e.title}</Text>
                    <Text style={s.lVenue} numberOfLines={1}>{e.venue} · {e.city}, {e.state}</Text>
                    <View style={[s.lBadge, {backgroundColor: color+'22'}]}>
                      <Text style={[s.lBadgeTxt, {color}]}>{e.category}</Text>
                    </View>
                  </View>
                  <TouchableOpacity onPress={()=>toggle(e.id)} style={s.lBm} hitSlop={{top:10,bottom:10,left:10,right:10}}>
                    <Ionicons name={isSaved(e.id)?'bookmark':'bookmark-outline'} size={20} color={isSaved(e.id)?'#FF6B35':'#444'}/>
                  </TouchableOpacity>
                </TouchableOpacity>
              )
            })}
          </View>
        )}

        {filtered.length === 0 && (
          <View style={{alignItems:'center', paddingVertical:60}}>
            <Ionicons name="calendar-outline" size={48} color="#1A1A1A"/>
            <Text style={{color:'#333', marginTop:14}}>No events in this category</Text>
          </View>
        )}

      </ScrollView>
    </SafeAreaView>
  )
}

const s = StyleSheet.create({
  safe:      {flex:1, backgroundColor:'#000'},
  header:    {flexDirection:'row', alignItems:'center', justifyContent:'space-between', paddingHorizontal:20, paddingTop:8, paddingBottom:12},
  logo:      {color:'#fff', fontSize:32, fontWeight:'900', letterSpacing:-1},
  loc:       {color:'#555', fontSize:12, marginTop:1},
  bell:      {backgroundColor:'#0F0F0F', padding:10, borderRadius:50, borderWidth:1, borderColor:'#222'},
  search:    {marginHorizontal:20, marginBottom:16, backgroundColor:'#0F0F0F', borderWidth:1, borderColor:'#1E1E1E', borderRadius:14, flexDirection:'row', alignItems:'center', paddingHorizontal:14, paddingVertical:12},
  searchTxt: {color:'#444', marginLeft:8, fontSize:14},
  catRow:    {paddingHorizontal:20, gap:8, marginBottom:24},
  catBtn:    {paddingHorizontal:16, paddingVertical:8, borderRadius:50, backgroundColor:'#0F0F0F', borderWidth:1, borderColor:'#1E1E1E'},
  catOn:     {backgroundColor:'#FF6B35', borderColor:'#FF6B35'},
  catTxt:    {color:'#555', fontSize:13, fontWeight:'600'},
  catTxtOn:  {color:'#fff'},
  section:   {paddingHorizontal:20, marginBottom:28},
  sLabel:    {color:'#444', fontSize:11, fontWeight:'700', letterSpacing:1, marginBottom:12},
  // featured
  fCard:     {width:220, backgroundColor:'#0D0D0D', borderRadius:18, borderWidth:1, borderColor:'#1A1A1A', overflow:'hidden'},
  fImg:      {height:110, alignItems:'center', justifyContent:'center'},
  fBadge:    {position:'absolute', bottom:10, left:12, paddingHorizontal:8, paddingVertical:3, borderRadius:50},
  fBadgeTxt: {color:'#fff', fontSize:10, fontWeight:'700'},
  fBody:     {padding:14},
  fTitle:    {color:'#fff', fontSize:14, fontWeight:'700', lineHeight:19},
  fVenue:    {color:'#555', fontSize:12, marginTop:4},
  fFooter:   {flexDirection:'row', justifyContent:'space-between', alignItems:'center', marginTop:10},
  fDate:     {fontSize:12, fontWeight:'800'},
  fPrice:    {color:'#555', fontSize:11},
  // list
  lCard:     {flexDirection:'row', backgroundColor:'#0D0D0D', borderRadius:16, marginBottom:10, borderWidth:1, borderColor:'#1A1A1A', overflow:'hidden', alignItems:'center'},
  lBar:      {width:4, alignSelf:'stretch'},
  lDate:     {alignItems:'center', paddingHorizontal:14, paddingVertical:16, minWidth:56},
  lDateM:    {color:'#555', fontSize:10, fontWeight:'700', letterSpacing:0.5},
  lDateD:    {color:'#fff', fontSize:22, fontWeight:'800'},
  lBody:     {flex:1, paddingVertical:14, paddingRight:4},
  lTitle:    {color:'#fff', fontSize:14, fontWeight:'700', lineHeight:19},
  lVenue:    {color:'#555', fontSize:11, marginTop:3},
  lBadge:    {alignSelf:'flex-start', marginTop:7, paddingHorizontal:8, paddingVertical:3, borderRadius:50},
  lBadgeTxt: {fontSize:10, fontWeight:'700'},
  lBm:       {paddingHorizontal:16},
})
""")

# ── app/(tabs)/explore.tsx  EXPLORE ───────────────────────
with open('app/(tabs)/explore.tsx', 'w') as f:
    f.write("""import React, { useState } from 'react'
import { View, Text, ScrollView, TextInput, TouchableOpacity, StyleSheet } from 'react-native'
import { SafeAreaView } from 'react-native-safe-area-context'
import { Ionicons } from '@expo/vector-icons'
import { EVENTS, CATEGORIES, CAT_COLOR, CAT_ICON } from '../../constants/events'

export default function ExploreScreen() {
  const [query, setQuery] = useState('')
  const [cat, setCat]     = useState(null)
  const showResults = query.length >= 1 || cat !== null
  const results = EVENTS.filter(e => {
    const q = query.toLowerCase()
    const mQ = q.length === 0 || e.title.toLowerCase().includes(q) || e.venue.toLowerCase().includes(q) || e.city.toLowerCase().includes(q)
    const mC = cat === null || e.category === cat
    return mQ && mC
  })

  return (
    <SafeAreaView style={s.safe}>
      <View style={s.header}><Text style={s.title}>Explore</Text></View>
      <View style={s.searchWrap}>
        <Ionicons name="search" size={16} color="#555" style={{marginRight:8}}/>
        <TextInput style={s.input} placeholder="Events, athletes, venues..." placeholderTextColor="#444"
          value={query} onChangeText={setQuery} returnKeyType="search" autoCapitalize="none" autoCorrect={false} clearButtonMode="while-editing"/>
      </View>
      <ScrollView showsVerticalScrollIndicator={false} contentContainerStyle={{paddingBottom:30}}>
        <View style={s.tilesWrap}>
          <Text style={s.tilesLabel}>BROWSE BY CATEGORY</Text>
          <View style={s.tilesGrid}>
            {CATEGORIES.map(c => {
              const color  = CAT_COLOR[c]
              const active = cat === c
              return (
                <TouchableOpacity key={c} style={[s.tile, {backgroundColor:color+'18', borderColor:active?color:'transparent', borderWidth:2}]}
                  onPress={()=>setCat(active ? null : c)}>
                  <Ionicons name={CAT_ICON[c]} size={28} color={color}/>
                  <Text style={[s.tileName, {color}]}>{c}</Text>
                  <Text style={s.tileCount}>{EVENTS.filter(e=>e.category===c).length} events</Text>
                </TouchableOpacity>
              )
            })}
          </View>
        </View>
        {showResults && (
          <View style={s.results}>
            <Text style={s.rMeta}>{results.length} event{results.length!==1?'s':''} found</Text>
            {results.length === 0
              ? <View style={{alignItems:'center', paddingVertical:48}}><Ionicons name="search-outline" size={44} color="#1A1A1A"/><Text style={{color:'#333', marginTop:12}}>No events matched</Text></View>
              : results.map(e => {
                  const color = CAT_COLOR[e.category]
                  return (
                    <TouchableOpacity key={e.id} style={s.rCard}>
                      <View style={[s.rDot, {backgroundColor:color}]}/>
                      <View style={{flex:1}}>
                        <Text style={s.rTitle} numberOfLines={1}>{e.title}</Text>
                        <Text style={s.rSub}>{e.venue} · {e.month} {e.day}</Text>
                      </View>
                      <Text style={[s.rPrice, {color}]}>{e.price}</Text>
                    </TouchableOpacity>
                  )
                })
            }
          </View>
        )}
      </ScrollView>
    </SafeAreaView>
  )
}

const s = StyleSheet.create({
  safe:       {flex:1, backgroundColor:'#000'},
  header:     {paddingHorizontal:20, paddingTop:8, paddingBottom:12},
  title:      {color:'#fff', fontSize:32, fontWeight:'900', letterSpacing:-1},
  searchWrap: {marginHorizontal:20, marginBottom:20, backgroundColor:'#0F0F0F', borderWidth:1, borderColor:'#1E1E1E', borderRadius:14, flexDirection:'row', alignItems:'center', paddingHorizontal:14, paddingVertical:10},
  input:      {flex:1, color:'#fff', fontSize:14, paddingVertical:2},
  tilesWrap:  {paddingHorizontal:20, marginBottom:24},
  tilesLabel: {color:'#444', fontSize:11, fontWeight:'700', letterSpacing:1, marginBottom:12},
  tilesGrid:  {flexDirection:'row', flexWrap:'wrap', gap:12},
  tile:       {width:'47%', padding:16, borderRadius:16, alignItems:'flex-start'},
  tileName:   {fontSize:14, fontWeight:'800', marginTop:8},
  tileCount:  {color:'#555', fontSize:12, marginTop:2},
  results:    {paddingHorizontal:20},
  rMeta:      {color:'#444', fontSize:12, fontWeight:'600', marginBottom:10},
  rCard:      {flexDirection:'row', alignItems:'center', backgroundColor:'#0D0D0D', borderRadius:14, marginBottom:8, padding:14, borderWidth:1, borderColor:'#1A1A1A'},
  rDot:       {width:8, height:8, borderRadius:4, marginRight:12},
  rTitle:     {color:'#fff', fontSize:14, fontWeight:'600'},
  rSub:       {color:'#555', fontSize:12, marginTop:2},
  rPrice:     {fontSize:12, fontWeight:'700', marginLeft:8},
})
""")

# ── app/(tabs)/saved.tsx  SAVED ───────────────────────────
with open('app/(tabs)/saved.tsx', 'w') as f:
    f.write("""import React from 'react'
import { View, Text, ScrollView, TouchableOpacity, StyleSheet } from 'react-native'
import { SafeAreaView } from 'react-native-safe-area-context'
import { Ionicons } from '@expo/vector-icons'
import { useSaved } from '../../contexts/SavedContext'
import { EVENTS, CAT_COLOR } from '../../constants/events'

export default function SavedScreen() {
  const { savedIds, toggle } = useSaved()
  const saved = EVENTS.filter(e => savedIds.includes(e.id))
  return (
    <SafeAreaView style={s.safe}>
      <View style={s.header}>
        <Text style={s.title}>Saved</Text>
        {saved.length > 0 && <View style={s.pill}><Text style={s.pillTxt}>{saved.length}</Text></View>}
      </View>
      {saved.length === 0
        ? <View style={s.empty}>
            <View style={s.emptyCircle}><Ionicons name="bookmark-outline" size={44} color="#FF6B35"/></View>
            <Text style={s.emptyTitle}>Nothing saved yet</Text>
            <Text style={s.emptySub}>Tap the bookmark on any event{'\n'}to save it here</Text>
          </View>
        : <ScrollView showsVerticalScrollIndicator={false} contentContainerStyle={{paddingHorizontal:20, paddingBottom:30}}>
            {saved.map(e => {
              const color = CAT_COLOR[e.category] || '#FF6B35'
              return (
                <TouchableOpacity key={e.id} style={s.card}>
                  <View style={[s.bar, {backgroundColor:color}]}/>
                  <View style={s.dateBlock}>
                    <Text style={s.dM}>{e.month}</Text>
                    <Text style={s.dD}>{e.day}</Text>
                  </View>
                  <View style={s.body}>
                    <Text style={s.cTitle} numberOfLines={2}>{e.title}</Text>
                    <Text style={s.cVenue} numberOfLines={1}>{e.venue} · {e.city}, {e.state}</Text>
                    <View style={[s.badge, {backgroundColor:color+'22'}]}>
                      <Text style={[s.badgeTxt, {color}]}>{e.category}</Text>
                    </View>
                  </View>
                  <TouchableOpacity onPress={()=>toggle(e.id)} style={{paddingHorizontal:14}} hitSlop={{top:10,bottom:10,left:10,right:10}}>
                    <Ionicons name="bookmark" size={22} color="#FF6B35"/>
                  </TouchableOpacity>
                </TouchableOpacity>
              )
            })}
          </ScrollView>
      }
    </SafeAreaView>
  )
}

const s = StyleSheet.create({
  safe:        {flex:1, backgroundColor:'#000'},
  header:      {flexDirection:'row', alignItems:'center', paddingHorizontal:20, paddingTop:8, paddingBottom:16},
  title:       {color:'#fff', fontSize:32, fontWeight:'900', letterSpacing:-1},
  pill:        {marginLeft:10, backgroundColor:'#FF6B35', borderRadius:50, paddingHorizontal:9, paddingVertical:2},
  pillTxt:     {color:'#fff', fontSize:12, fontWeight:'700'},
  empty:       {flex:1, alignItems:'center', justifyContent:'center', paddingBottom:80},
  emptyCircle: {backgroundColor:'#0F0F0F', padding:24, borderRadius:100, borderWidth:1, borderColor:'#1A1A1A', marginBottom:20},
  emptyTitle:  {color:'#fff', fontSize:18, fontWeight:'700'},
  emptySub:    {color:'#444', fontSize:14, marginTop:8, textAlign:'center', lineHeight:21},
  card:        {flexDirection:'row', backgroundColor:'#0D0D0D', borderRadius:16, marginBottom:10, borderWidth:1, borderColor:'#1A1A1A', overflow:'hidden', alignItems:'center'},
  bar:         {width:4, alignSelf:'stretch'},
  dateBlock:   {alignItems:'center', paddingHorizontal:14, paddingVertical:16, minWidth:56},
  dM:          {color:'#555', fontSize:10, fontWeight:'700', letterSpacing:0.5},
  dD:          {color:'#fff', fontSize:22, fontWeight:'800'},
  body:        {flex:1, paddingVertical:14},
  cTitle:      {color:'#fff', fontSize:14, fontWeight:'700', lineHeight:19},
  cVenue:      {color:'#555', fontSize:11, marginTop:3},
  badge:       {alignSelf:'flex-start', marginTop:7, paddingHorizontal:8, paddingVertical:3, borderRadius:50},
  badgeTxt:    {fontSize:10, fontWeight:'700'},
})
""")

# ── app/(tabs)/profile.tsx  PROFILE ──────────────────────
with open('app/(tabs)/profile.tsx', 'w') as f:
    f.write("""import React from 'react'
import { View, Text, ScrollView, TouchableOpacity, StyleSheet } from 'react-native'
import { SafeAreaView } from 'react-native-safe-area-context'
import { Ionicons } from '@expo/vector-icons'
import { useSaved } from '../../contexts/SavedContext'

const MENU = [
  { section:'Account',       items:[{icon:'person-circle-outline',label:'Sign In',sub:'Apple or email'},{icon:'notifications-outline',label:'Notifications',sub:'Manage alerts'}]},
  { section:'My Collection', items:[{icon:'bookmark-outline',label:'Saved Events',sub:''},{icon:'calendar-outline',label:'Attending',sub:'0 upcoming'},{icon:'time-outline',label:'Past Events',sub:'0 attended'}]},
  { section:'App',           items:[{icon:'star-outline',label:'Rate TROV',sub:'Love the app?'},{icon:'share-social-outline',label:'Share TROV',sub:'Tell a collector'},{icon:'information-circle-outline',label:'About',sub:'v1.0.0-beta'}]},
]

export default function ProfileScreen() {
  const { savedIds } = useSaved()
  return (
    <SafeAreaView style={s.safe}>
      <ScrollView showsVerticalScrollIndicator={false} contentContainerStyle={{paddingBottom:30}}>
        <View style={s.header}><Text style={s.title}>Profile</Text></View>
        <View style={s.hero}>
          <View style={s.avatar}><Ionicons name="person" size={40} color="#333"/></View>
          <Text style={s.heroTitle}>Join TROV</Text>
          <Text style={s.heroSub}>Save events, track signings, and never miss a drop in NYC and NJ.</Text>
          <TouchableOpacity style={s.appleBtn}>
            <Ionicons name="logo-apple" size={18} color="#000"/>
            <Text style={s.appleTxt}>Sign in with Apple</Text>
          </TouchableOpacity>
          <TouchableOpacity style={s.emailBtn}>
            <Text style={s.emailTxt}>Continue with Email</Text>
          </TouchableOpacity>
        </View>
        <View style={s.stats}>
          {[[String(savedIds.length),'Saved'],['0','Going'],['0','Past']].map(([n,l]) => (
            <View key={l} style={s.stat}>
              <Text style={s.statN}>{n}</Text>
              <Text style={s.statL}>{l}</Text>
            </View>
          ))}
        </View>
        {MENU.map(({section, items}) => (
          <View key={section} style={s.mGroup}>
            <Text style={s.mGroupL}>{section.toUpperCase()}</Text>
            <View style={s.mCard}>
              {items.map((item, i) => (
                <TouchableOpacity key={item.label} style={[s.mRow, i>0 && s.mBorder]}>
                  <View style={s.mIcon}><Ionicons name={item.icon} size={20} color="#FF6B35"/></View>
                  <View style={{flex:1}}>
                    <Text style={s.mLabel}>{item.label}</Text>
                    <Text style={s.mSub}>{item.label==='Saved Events' ? savedIds.length+' saved' : item.sub}</Text>
                  </View>
                  <Ionicons name="chevron-forward" size={16} color="#2A2A2A"/>
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
  safe:      {flex:1, backgroundColor:'#000'},
  header:    {paddingHorizontal:20, paddingTop:8, paddingBottom:4},
  title:     {color:'#fff', fontSize:32, fontWeight:'900', letterSpacing:-1},
  hero:      {alignItems:'center', paddingHorizontal:24, paddingTop:12, paddingBottom:24},
  avatar:    {width:90, height:90, borderRadius:45, backgroundColor:'#0F0F0F', borderWidth:2, borderColor:'#1A1A1A', alignItems:'center', justifyContent:'center', marginBottom:16},
  heroTitle: {color:'#fff', fontSize:22, fontWeight:'800'},
  heroSub:   {color:'#555', fontSize:13, textAlign:'center', marginTop:8, lineHeight:20, paddingHorizontal:16},
  appleBtn:  {marginTop:20, backgroundColor:'#fff', flexDirection:'row', alignItems:'center', gap:8, paddingHorizontal:28, paddingVertical:13, borderRadius:50, width:'100%', justifyContent:'center'},
  appleTxt:  {color:'#000', fontWeight:'700', fontSize:15},
  emailBtn:  {marginTop:10, borderWidth:1, borderColor:'#1E1E1E', paddingHorizontal:28, paddingVertical:13, borderRadius:50, width:'100%', alignItems:'center'},
  emailTxt:  {color:'#666', fontWeight:'600', fontSize:14},
  stats:     {flexDirection:'row', marginHorizontal:20, backgroundColor:'#0D0D0D', borderRadius:18, borderWidth:1, borderColor:'#1A1A1A', marginBottom:28},
  stat:      {flex:1, alignItems:'center', paddingVertical:16},
  statN:     {color:'#fff', fontSize:22, fontWeight:'800'},
  statL:     {color:'#555', fontSize:12, marginTop:2},
  mGroup:    {paddingHorizontal:20, marginBottom:16},
  mGroupL:   {color:'#444', fontSize:11, fontWeight:'700', letterSpacing:1, marginBottom:8},
  mCard:     {backgroundColor:'#0D0D0D', borderRadius:18, borderWidth:1, borderColor:'#1A1A1A', overflow:'hidden'},
  mRow:      {flexDirection:'row', alignItems:'center', padding:14},
  mBorder:   {borderTopWidth:1, borderTopColor:'#141414'},
  mIcon:     {width:36, height:36, borderRadius:10, backgroundColor:'#1A1A1A', alignItems:'center', justifyContent:'center', marginRight:12},
  mLabel:    {color:'#fff', fontSize:14, fontWeight:'600'},
  mSub:      {color:'#555', fontSize:12, marginTop:1},
  footer:    {textAlign:'center', color:'#222', fontSize:11, marginTop:8},
})
""")

print("✅  All files written successfully!")
PYEOF

echo ""
echo "→ Clearing Metro cache..."
rm -rf /tmp/metro-* 2>/dev/null || true
rm -rf "$TMPDIR/metro-*" 2>/dev/null || true

echo "→ Starting Expo..."
npx expo start --go --clear
