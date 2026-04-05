# TROV Phase 1 — Claude Code Kickoff Guide

**Date:** April 2, 2026
**Goal:** Get a working Expo app shell on your phone via TestFlight or Expo Go

---

## Step 1: Create the Project Folder

Pick a location on your machine for the actual code (NOT inside Dropbox — code repos don't belong in cloud sync). Something like:

```
~/Projects/trov-app
```

Open Claude Code in that folder:
```bash
cd ~/Projects/trov-app
claude
```

---

## Step 2: Paste This CLAUDE.md Into the Project

Once Claude Code opens, tell it to create `CLAUDE.md` at the project root with this content:

```markdown
# TROV — iOS App (Expo/React Native + Supabase)

## What This Is
Collectibles event discovery app. Users customize interests → get push alerts for matching card shows, signings, meetups in NYC/NJ. Manual curation for v1, AI pipeline later.

## Tech Stack
- Expo SDK 52+ (managed workflow, NO ejection)
- TypeScript strict mode
- Expo Router (file-based routing)
- Supabase (auth, database, realtime, storage)
- Zustand (UI state) + TanStack Query (server state)
- NativeWind (Tailwind for RN)
- expo-notifications (push)
- expo-location + react-native-maps

## Architecture Rules
- All screens in `app/` using Expo Router file-based routing
- Bottom tab navigation: Home, Explore, Saved, Profile
- Components in `src/components/`, hooks in `src/hooks/`, utils in `src/utils/`
- Supabase client in `src/lib/supabase.ts`
- All API calls through TanStack Query hooks in `src/hooks/`
- TypeScript interfaces in `src/types/`
- NativeWind for all styling — no inline StyleSheet unless necessary

## Phase 1 Target (Current)
1. Expo project scaffolded with TypeScript
2. Bottom tab navigation (Home, Explore, Saved, Profile)
3. Supabase client wired (connection verified)
4. Auth flow: Apple Sign In + email fallback
5. Basic event feed pulling real data from Supabase
6. Builds successfully via EAS Build
7. Runs on Expo Go or TestFlight

## Supabase Connection (Our Own Instance)
- URL: [from your Supabase project dashboard → Settings → API]
- Anon Key: [from your Supabase project dashboard → Settings → API]
- Tables to query first: `events`, `users`, `user_preferences`

## Commands
- `npx expo start` — local dev
- `npx expo start --ios` — iOS simulator
- `npx eas build --platform ios --profile preview` — build for TestFlight
- `npx eas build --platform ios --profile development` — dev client build

## Code Standards
- Commit format: `feat(scope): description` / `fix(scope): description`
- No `any` types — always define interfaces
- Components are functional with hooks only
- Error boundaries on all screens
```

---

## Step 3: First Claude Code Prompt

Copy-paste this into Claude Code as your first instruction:

```
Scaffold a new Expo project for TROV. Use the latest Expo SDK with TypeScript template. Set up:

1. Initialize with: npx create-expo-app trov-app --template expo-template-blank-typescript
   Then move everything from trov-app/ to the current directory.

2. Install core dependencies:
   - expo-router (file-based routing)
   - @supabase/supabase-js
   - zustand
   - @tanstack/react-query
   - nativewind + tailwindcss
   - expo-location
   - react-native-maps
   - expo-notifications
   - expo-secure-store (for auth tokens)
   - expo-local-authentication (biometrics)
   - @expo/vector-icons

3. Set up Expo Router with bottom tab navigation:
   - app/(tabs)/_layout.tsx — Tab navigator
   - app/(tabs)/index.tsx — Home (event feed)
   - app/(tabs)/explore.tsx — Explore (map + search)
   - app/(tabs)/saved.tsx — Saved events
   - app/(tabs)/profile.tsx — User profile
   - app/_layout.tsx — Root layout with providers

4. Create the Supabase client at src/lib/supabase.ts
   Use environment variables EXPO_PUBLIC_SUPABASE_URL and EXPO_PUBLIC_SUPABASE_ANON_KEY
   Use expo-secure-store for token persistence

5. Create a .env.example with:
   EXPO_PUBLIC_SUPABASE_URL=your-supabase-url
   EXPO_PUBLIC_SUPABASE_ANON_KEY=your-anon-key

6. Set up NativeWind (Tailwind CSS for React Native)

7. Create a basic TanStack Query provider wrapper

8. Make sure it compiles and runs: npx expo start

Do NOT stub out screens with just "Hello World" — give each tab a proper skeleton:
- Home: ScrollView with a header "Discover Events" and placeholder event cards
- Explore: Map placeholder with "Events near you" header
- Saved: Empty state with "No saved events yet" message
- Profile: Basic profile layout with avatar placeholder and settings list
```

---

## Step 4: Create Your Own Supabase Project

We're building on our own infrastructure — clean, independent, no dependencies on anyone else's backend.

1. Go to **supabase.com** → Sign up or log in (free tier is plenty for dev)
2. Click **New Project** → Name it `trov-app` → Pick a strong database password → Region: East US
3. Wait ~2 min for it to spin up
4. Go to **Settings → API** → Copy:
   - **Project URL** (looks like `https://xxxxx.supabase.co`)
   - **anon public key** (long JWT starting with `eyJ...`)
5. Create a `.env` file in your project root:
   ```
   EXPO_PUBLIC_SUPABASE_URL=https://xxxxx.supabase.co
   EXPO_PUBLIC_SUPABASE_ANON_KEY=eyJ...your-key-here
   ```

Then tell Claude Code:
```
Set up the Supabase database tables for TROV. Create these core tables using the SQL editor in Supabase (or via the Supabase client):

1. events — id (uuid), title, description, date (timestamptz), end_date, location_name, address, city, state, zip, latitude (float8), longitude (float8), category (text), subcategory, image_url, source_url, venue_id (uuid nullable), is_featured (bool default false), status (text default 'active'), created_at, updated_at

2. users — id (uuid, references auth.users), email, username, display_name, avatar_url, bio, city, state, zip, latitude, longitude, notification_preferences (jsonb), onboarding_completed (bool default false), created_at, updated_at

3. user_preferences — id (uuid), user_id (uuid references users), category (text), subcategory (text), created_at

4. saved_events — id (uuid), user_id (uuid references users), event_id (uuid references events), created_at

5. Enable Row Level Security on all tables. Users can only read/write their own user data and preferences. Events are readable by all authenticated users.

After creating tables, seed with 15-20 realistic sample events: NYC/NJ card shows, autograph signings, collector meetups, athlete appearances. Use real venue names (Javits Center, Meadowlands Expo Center, etc.) and realistic dates in May-July 2026.
```

This gives us a fully functional backend with real-looking data. When the deal happens with Ryan, we either migrate his event data into our Supabase or swap the connection — one env variable change.

---

## Step 5: After Scaffold Is Working

Once the app shell runs in Expo Go (or simulator), come back to this Cowork thread and tell me:

1. Did it compile and run?
2. Any errors or issues?
3. Screenshot if possible

Then we move to **Phase 1B**: Wire auth (Apple Sign In + email), connect to our Supabase, pull real event data into the Home feed.

---

## Quick Reference: What Happens Where

| Activity | Where |
|----------|-------|
| Writing code, running builds, debugging | **Claude Code** |
| Tracking progress, strategy, decisions | **This Cowork thread** |
| Learnings, specs, proposals | **TROV folder in Dropbox** |
| Ryan/Phil communication (later) | **iMessage / email** |

---

## Troubleshooting

**"Can't find expo-router"** → Make sure you ran `npx expo install expo-router react-native-safe-area-context react-native-screens expo-linking expo-constants expo-status-bar`

**NativeWind not working** → NativeWind v4 setup is specific. Tell Claude Code: "Set up NativeWind v4 following the official Expo setup guide. Make sure babel.config.js, tailwind.config.js, and metro.config.js are all configured."

**EAS Build fails** → You need an Expo account. Run `npx eas login` first, then `npx eas build:configure` to set up eas.json.

**Apple Developer Account** → You'll need this for TestFlight. $99/year. If you don't have one yet, sign up at developer.apple.com — takes 24-48hrs to activate. You can develop locally without it, but can't push to TestFlight.
