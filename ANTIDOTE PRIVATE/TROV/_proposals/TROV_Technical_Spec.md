# TROV Technical Spec & Build Bible

**Last Updated:** March 30, 2026
**Version:** 1.0 (Foundation)
**Owner:** Beryl Jacobson (Antidote Group) + Claude (Dev Partner)
**Target Launch:** Fanatics Fest (July 16-19, 2026) — App Store deadline June 7, 2026

---

## 1. PROJECT OVERVIEW

**TROV** (formerly Scout) is a native iOS app for collectibles event discovery. The platform helps sports card and memorabilia collectors discover live events near them via personalized alerts, curated feeds, and a community of collectors.

### Core Value Proposition
- **For Collectors:** Discover card shows, autograph signings, athlete appearances, and collector meetups personalized to your interests, within your radius, and alerted in real-time.
- **For Businesses:** Drive attendance to collectibles events through the only purpose-built discovery platform for the category.
- **For Fanatics:** Position Fanatics as the central hub for collectibles commerce (event discovery → in-app purchases).

### Founding Team
- **Ryan Wanderer** (Age 17) — Founder, Product Vision, Supabase Database
- **Beryl Jacobson** (Antidote Group) — Native App Build & Product Leadership
- **Claude** (Anthropic) — Lead Engineer, Architecture, Code Implementation

### Market Context
- Lovable prototype (web) validates demand at scoutcollectibles.lovable.app
- Real event data sourced from ~40 collectibles venues, card show organizers, and athlete appearance brokers
- Target audience: 12-65 age range; 80% male; $50K-500K+ household income; heavy sports engagement
- Revenue model (post-launch): Event listing premiums, sponsorships, in-app commerce integration with Fanatics

---

## 2. TECH STACK & ARCHITECTURE

### Frontend (iOS Native)
- **Framework:** Expo with React Native
- **Language:** TypeScript
- **Navigation:** Expo Router (file-based routing)
- **State Management:** Zustand + React Context (lightweight, no Redux overhead)
- **API Client:** TanStack Query (React Query v5) for data fetching, caching, background sync
- **Styling:** NativeWind (Tailwind for React Native) + custom color tokens
- **Authentication:**
  - Apple Sign In (native)
  - Google Sign In (native)
  - Biometric: expo-local-authentication (Touch ID / Face ID)
- **Notifications:** expo-notifications + Supabase Edge Functions for server-side triggers
- **Maps:** expo-location + react-native-maps
- **Share/Deep Linking:** Expo.Linking + Branch.io (optional, for future referral campaigns)

### Backend (Supabase)
- **Database:** PostgreSQL (hosted on Supabase)
- **Real-time:** PostgreSQL LISTEN/NOTIFY via Supabase Realtime
- **Auth:** Supabase Auth with custom JWT claims
- **Storage:** Supabase Storage (event images, user avatars)
- **Edge Functions:** Deno-based serverless for:
  - Event scraping pipeline (daily AI-powered ingestion)
  - Push notification triggers
  - Webhook receivers (Stripe, Branch)
  - Admin queue management
- **Row-Level Security (RLS):** All tables protected; users see only their own data + public events

### Admin Panel (Web)
- **Framework:** Next.js 14+ (App Router)
- **Database UI:** Refine (React-admin replacement) or custom React components
- **Authentication:** Supabase Auth (role-based: admin, moderator)
- **Deployment:** Vercel (linked to GitHub)
- **Purpose:** Event approval queue, user metrics, push notification composer, athlete/team management

### Build & Deployment
- **iOS Build:** EAS Build (Expo Application Services)
- **App Store Submit:** EAS Submit
- **TestFlight:** Automatic routing via EAS
- **CI/CD:** GitHub Actions (on-push lint/test, PR validation)
- **Environment Config:** .env files per stage (dev, staging, production)
- **Secrets Management:** GitHub Secrets + Vercel Secrets

### AI Event Discovery Pipeline
- **Scraper:** Python-based (Lambda or Edge Function) that:
  - Crawls target venues (Eventbrite, Ticketmaster, Facebook Events, venue websites)
  - Uses OpenAI/Claude API to extract event details (title, date, athlete names, category)
  - Inserts raw events into `events_pending_review` table
- **Admin Review Queue:** Ryan and team review/approve events before publishing to app
- **ML Personalization (Phase 4):** Supabase Functions + TF Lite model for notification ranking

---

## 3. SUPABASE DATA MODEL

All tables use PostgreSQL with UTC timestamps (`created_at`, `updated_at`). All foreign keys cascade on delete unless noted.

### 3.1 Core Tables

#### `users`
Primary user account table. Synced with Supabase Auth user IDs.

```sql
CREATE TABLE users (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  auth_id UUID NOT NULL UNIQUE REFERENCES auth.users(id) ON DELETE CASCADE,
  email TEXT NOT NULL UNIQUE,
  username TEXT UNIQUE,
  display_name TEXT,
  avatar_url TEXT,
  zip_code TEXT,
  search_radius_miles INT DEFAULT 50,
  latitude DECIMAL(9, 6),
  longitude DECIMAL(9, 6),
  notification_enabled BOOLEAN DEFAULT true,
  push_token TEXT, -- expo-notifications token
  phone_number TEXT,
  bio TEXT,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
  deleted_at TIMESTAMP WITH TIME ZONE -- soft delete for GDPR
);
```

**RLS Policies:**
- Users can read their own row
- Users can update their own row
- Anyone can read public profile info (username, avatar)

#### `events`
Published events (approved by admin). Ready for display in app.

```sql
CREATE TABLE events (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  title TEXT NOT NULL,
  description TEXT,
  category TEXT NOT NULL, -- e.g., 'Card Shows', 'Autograph Signings', 'Athlete Appearances'
  event_date TIMESTAMP WITH TIME ZONE NOT NULL,
  event_end_date TIMESTAMP WITH TIME ZONE,
  venue_name TEXT NOT NULL,
  address TEXT NOT NULL,
  city TEXT NOT NULL,
  state TEXT NOT NULL,
  zip_code TEXT,
  latitude DECIMAL(9, 6),
  longitude DECIMAL(9, 6),
  admission_type TEXT, -- 'free', 'paid', 'tiered'
  admission_price DECIMAL(10, 2),
  admission_note TEXT,
  confirmed_attendees_count INT DEFAULT 0,
  image_url TEXT,
  source_url TEXT NOT NULL,
  source_type TEXT, -- 'eventbrite', 'ticketmaster', 'venue', 'facebook', 'manual'
  is_featured BOOLEAN DEFAULT false,
  is_verified BOOLEAN DEFAULT false,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
  published_at TIMESTAMP WITH TIME ZONE,
  expires_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_events_date ON events(event_date);
CREATE INDEX idx_events_location ON events USING gist(ll_to_earth(latitude, longitude));
CREATE INDEX idx_events_category ON events(category);
```

**RLS Policies:**
- Anyone can read published events
- Only admins can insert/update/delete

#### `events_pending_review`
Raw events scraped from external sources, awaiting admin approval.

```sql
CREATE TABLE events_pending_review (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  title TEXT NOT NULL,
  description TEXT,
  category TEXT,
  event_date TIMESTAMP WITH TIME ZONE,
  venue_name TEXT,
  address TEXT,
  city TEXT,
  state TEXT,
  zip_code TEXT,
  latitude DECIMAL(9, 6),
  longitude DECIMAL(9, 6),
  admission_type TEXT,
  admission_price DECIMAL(10, 2),
  image_url TEXT,
  source_url TEXT NOT NULL,
  source_type TEXT,
  raw_data JSONB, -- full scrape metadata for debugging
  scrape_timestamp TIMESTAMP WITH TIME ZONE,
  review_status TEXT DEFAULT 'pending', -- 'pending', 'approved', 'rejected', 'duplicate'
  reviewed_by UUID REFERENCES users(id),
  reviewed_at TIMESTAMP WITH TIME ZONE,
  reviewer_notes TEXT,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

CREATE INDEX idx_pending_review_status ON events_pending_review(review_status);
CREATE INDEX idx_pending_review_created ON events_pending_review(created_at DESC);
```

**RLS Policies:**
- Admins can read/update pending events
- App users cannot see this table

#### `athletes`
Professional athletes appearing at events.

```sql
CREATE TABLE athletes (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name TEXT NOT NULL,
  slug TEXT NOT NULL UNIQUE,
  league TEXT, -- 'NFL', 'NBA', 'MLB', 'NHL', etc.
  team TEXT,
  position TEXT,
  number INT,
  image_url TEXT,
  bio TEXT,
  external_id TEXT, -- ESPN ID, etc.
  created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

CREATE UNIQUE INDEX idx_athletes_slug ON athletes(slug);
```

**RLS Policies:**
- Anyone can read athletes
- Only admins can insert/update/delete

#### `event_athletes`
Many-to-many junction: which athletes appear at which events.

```sql
CREATE TABLE event_athletes (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  event_id UUID NOT NULL REFERENCES events(id) ON DELETE CASCADE,
  athlete_id UUID NOT NULL REFERENCES athletes(id) ON DELETE CASCADE,
  is_confirmed BOOLEAN DEFAULT false,
  notes TEXT, -- e.g., "Autographs only until 2pm"
  created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
  UNIQUE(event_id, athlete_id)
);

CREATE INDEX idx_event_athletes_event ON event_athletes(event_id);
CREATE INDEX idx_event_athletes_athlete ON event_athletes(athlete_id);
```

#### `teams`
Sports teams (NFL franchises, NBA teams, etc.).

```sql
CREATE TABLE teams (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name TEXT NOT NULL UNIQUE,
  slug TEXT NOT NULL UNIQUE,
  league TEXT NOT NULL, -- 'NFL', 'NBA', etc.
  logo_url TEXT,
  external_id TEXT,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);
```

**RLS Policies:**
- Anyone can read teams
- Only admins can insert/update/delete

#### `categories`
Event categories (pre-defined list).

```sql
CREATE TABLE categories (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name TEXT NOT NULL UNIQUE, -- e.g., 'Card Shows', 'Autograph Signings & Photo Ops'
  slug TEXT NOT NULL UNIQUE,
  icon TEXT, -- emoji or icon name
  description TEXT,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

-- Seed with 8 values from prototype
INSERT INTO categories (name, slug, icon, description) VALUES
  ('Card Shows', 'card-shows', '🃏', 'Collectible trading card shows and exhibitions'),
  ('Autograph Signings & Photo Ops', 'autograph-signings', '🖊️', 'Meet-and-greet with athletes for autographs and photos'),
  ('Athlete Appearances', 'athlete-appearances', '⭐', 'Player endorsements, appearances, and charity events'),
  ('Mail-in Signings', 'mail-in-signings', '📬', 'Send memorabilia for remote authentication and signatures'),
  ('Memorabilia Events', 'memorabilia-events', '🏆', 'Vintage cards, memorabilia auctions, and trading expos'),
  ('Collector Meetups', 'collector-meetups', '👥', 'Local collector groups and trading meetups'),
  ('Giveaways', 'giveaways', '🎁', 'Contests and giveaways from brands and athletes'),
  ('Brand Drops', 'brand-drops', '📦', 'New product releases from card companies and brands');
```

#### `sports_leagues`
Predefined list of sports leagues (19 from prototype).

```sql
CREATE TABLE sports_leagues (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name TEXT NOT NULL UNIQUE, -- e.g., 'NFL', 'NBA'
  slug TEXT NOT NULL UNIQUE,
  icon TEXT,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

-- Seed with 19 values
INSERT INTO sports_leagues (name, slug) VALUES
  ('NFL', 'nfl'),
  ('NBA', 'nba'),
  ('MLB', 'mlb'),
  ('NHL', 'nhl'),
  ('WNBA', 'wnba'),
  ('MLS', 'mls'),
  ('NBA G League', 'nba-g-league'),
  ('UFC/MMA', 'ufc-mma'),
  ('WWE', 'wwe'),
  ('Formula 1', 'formula-1'),
  ('PGA Tour', 'pga-tour'),
  ('Tennis', 'tennis'),
  ('NCAA Basketball', 'ncaa-basketball'),
  ('NCAA Football', 'ncaa-football'),
  ('Olympics', 'olympics'),
  ('Boxing', 'boxing'),
  ('NASCAR', 'nascar'),
  ('Rugby', 'rugby'),
  ('Cricket', 'cricket');
```

### 3.2 User Preference Tables

#### `user_preferences`
Stores user's alert category, league, and location preferences.

```sql
CREATE TABLE user_preferences (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE,
  -- Radius & location
  search_radius_miles INT DEFAULT 50,
  -- Notification settings
  alerts_enabled BOOLEAN DEFAULT true,
  alert_frequency TEXT DEFAULT 'instant', -- 'instant', 'daily', 'weekly'
  created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

CREATE INDEX idx_user_preferences_user ON user_preferences(user_id);
```

#### `user_followed_categories`
Which event categories a user subscribes to (many-to-many).

```sql
CREATE TABLE user_followed_categories (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  category_id UUID NOT NULL REFERENCES categories(id) ON DELETE CASCADE,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
  UNIQUE(user_id, category_id)
);

CREATE INDEX idx_followed_categories_user ON user_followed_categories(user_id);
```

#### `user_followed_leagues`
Which sports leagues a user cares about.

```sql
CREATE TABLE user_followed_leagues (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  league_id UUID NOT NULL REFERENCES sports_leagues(id) ON DELETE CASCADE,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
  UNIQUE(user_id, league_id)
);

CREATE INDEX idx_followed_leagues_user ON user_followed_leagues(user_id);
```

#### `user_following`
Users can follow athletes and teams for targeted alerts.

```sql
CREATE TABLE user_following (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  followable_type TEXT NOT NULL, -- 'athlete' or 'team'
  athlete_id UUID REFERENCES athletes(id) ON DELETE CASCADE,
  team_id UUID REFERENCES teams(id) ON DELETE CASCADE,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
  UNIQUE(user_id, athlete_id, team_id)
);

CREATE INDEX idx_following_user ON user_following(user_id);
CREATE INDEX idx_following_athlete ON user_following(athlete_id);
CREATE INDEX idx_following_team ON user_following(team_id);
```

#### `dream_experiences`
User's "dream experience" text (free-form wish list for event alerts).

```sql
CREATE TABLE dream_experiences (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE,
  dream_text TEXT, -- e.g., "Surf trip with son"
  description TEXT,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

CREATE INDEX idx_dream_user ON dream_experiences(user_id);
```

### 3.3 Engagement Tables

#### `saved_events`
Users bookmark/save events to revisit later.

```sql
CREATE TABLE saved_events (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  event_id UUID NOT NULL REFERENCES events(id) ON DELETE CASCADE,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
  UNIQUE(user_id, event_id)
);

CREATE INDEX idx_saved_events_user ON saved_events(user_id);
CREATE INDEX idx_saved_events_event ON saved_events(event_id);
```

#### `event_views`
Track which events users view (for analytics & ML training).

```sql
CREATE TABLE event_views (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  event_id UUID NOT NULL REFERENCES events(id) ON DELETE CASCADE,
  viewed_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
  time_spent_seconds INT
);

CREATE INDEX idx_event_views_user ON event_views(user_id);
CREATE INDEX idx_event_views_event ON event_views(event_id);
```

### 3.4 Notification Tables

#### `notifications`
Server-side notification history (what was sent, when, to whom).

```sql
CREATE TABLE notifications (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  event_id UUID REFERENCES events(id) ON DELETE SET NULL,
  title TEXT NOT NULL,
  body TEXT NOT NULL,
  type TEXT DEFAULT 'event_alert', -- 'event_alert', 'reminder', 'special_offer'
  is_sent BOOLEAN DEFAULT false,
  sent_at TIMESTAMP WITH TIME ZONE,
  clicked_at TIMESTAMP WITH TIME ZONE,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

CREATE INDEX idx_notifications_user ON notifications(user_id);
CREATE INDEX idx_notifications_sent ON notifications(is_sent);
```

#### `notification_settings`
Per-user notification preferences (quiet hours, opt-outs, etc.).

```sql
CREATE TABLE notification_settings (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE,
  quiet_hours_enabled BOOLEAN DEFAULT false,
  quiet_hours_start TEXT, -- e.g., "22:00"
  quiet_hours_end TEXT,   -- e.g., "08:00"
  event_alert_enabled BOOLEAN DEFAULT true,
  reminder_enabled BOOLEAN DEFAULT true,
  marketing_enabled BOOLEAN DEFAULT true,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);
```

---

## 4. SCREEN-BY-SCREEN SPECIFICATION

### 4.1 Authentication Flow (Not in Prototype)

#### Screen: /auth/splash
**Purpose:** Initial launch screen before authentication.

**Layout:**
- Full-screen image (Scout logo or collectibles hero image)
- "Sign in to discover events" CTA button

**Components:**
- Image background
- Primary button leading to sign in method selection

**Data Source:** Local only

**User Interactions:**
- Tap "Sign in" → navigate to `/auth/signin`

---

#### Screen: /auth/signin
**Purpose:** Sign in method selection.

**Layout:**
- Header: "Welcome back"
- Two sign in options:
  - "Sign in with Apple" (native button)
  - "Sign in with Google" (native button)
- Toggle for "Use Face ID / Touch ID" (if device supports biometric)
- Divider
- "Don't have an account?" link to `/auth/signup`

**Components:**
- AppleAuthenticationButton (native)
- GoogleSignInButton (native)
- BiometricToggle (expo-local-authentication)

**Data Flow:**
1. User taps "Sign in with Apple"
2. expo calls native iOS sign in
3. JWT token returned → stored in SecureStore
4. Request to `POST /auth/signin` (custom endpoint)
5. User record created/updated in `users` table
6. Redirect to onboarding or `/home` based on `is_first_login` flag

**API Calls:**
- `POST /auth/signin` (custom Supabase function)
  - Input: `{ provider: 'apple' | 'google', token: string }`
  - Output: `{ user: User, onboarding_required: boolean }`

---

#### Screen: /auth/signup
**Purpose:** Create account for new collectors.

**Layout:**
- Header: "Welcome, collector!"
- Email input
- Username input (optional, auto-generated from email prefix)
- Display name input
- Zip code input
- CTA: "Create account"

**Components:**
- TextInput × 4
- Button

**Data Flow:**
1. User fills form
2. Client validates
3. `POST /auth/signup`
4. Supabase creates user
5. User record created in `users` table
6. Redirect to onboarding (`/onboarding/1`)

**API Calls:**
- `POST /auth/signup`
  - Input: `{ email, username, display_name, zip_code }`
  - Output: `{ user: User, onboarding_required: true }`

---

### 4.2 Onboarding Flow (Not in Prototype)

#### Screen: /onboarding/1 — Location & Radius
**Purpose:** Set home location and search radius.

**Layout:**
- Header: "Where are you?"
- Zip code input (pre-filled if available)
- Radius selector (radio buttons):
  - 25 miles
  - 50 miles (default)
  - 100 miles
  - Nationwide
- "Allow location access" prompt (iOS native permission)
- CTA: "Next"

**Components:**
- ZipCodeInput with validation
- RadioGroup (4 options)
- LocationPermissionPrompt (native)

**Data Flow:**
1. User enters zip code
2. Client geocodes zip → latitude/longitude
3. User selects radius
4. Tap "Next"
5. `PATCH /users/{id}` → update `zip_code`, `latitude`, `longitude`, `search_radius_miles`
6. Redirect to `/onboarding/2`

**API Calls:**
- `PATCH /users/{id}` (RLS: user can update own row)
  - Input: `{ zip_code, latitude, longitude, search_radius_miles }`

---

#### Screen: /onboarding/2 — Interest Categories
**Purpose:** Select event categories to follow.

**Layout:**
- Header: "What do you collect?"
- Subtitle: "Select all that interest you"
- Grid of category toggles (8 cards):
  - Card Shows 🃏
  - Autograph Signings 🖊️
  - Athlete Appearances ⭐
  - Mail-in Signings 📬
  - Memorabilia Events 🏆
  - Collector Meetups 👥
  - Giveaways 🎁
  - Brand Drops 📦
- CTA: "Next"

**Components:**
- CategoryToggle × 8 (pressable with state)

**Data Flow:**
1. User toggles categories (0+ selections)
2. Tap "Next"
3. `POST /user_followed_categories` for each selected category
4. Redirect to `/onboarding/3`

**API Calls:**
- `POST /user_followed_categories` (batch insert)
  - Input: `[{ category_id }, { category_id }, ...]`

---

#### Screen: /onboarding/3 — Sports Leagues
**Purpose:** Select sports leagues to follow.

**Layout:**
- Header: "Your favorite leagues?"
- Subtitle: "Select all you follow"
- Grid of league buttons (19 options):
  - NFL, NBA, MLB, NHL, WNBA, MLS, NBA G League, UFC/MMA, WWE, F1, PGA Tour, Tennis, NCAA Basketball, NCAA Football, Olympics, Boxing, NASCAR, Rugby, Cricket
- CTA: "Next"

**Components:**
- LeagueToggle × 19

**Data Flow:**
1. User toggles leagues (0+ selections)
2. Tap "Next"
3. `POST /user_followed_leagues` for each selected league
4. Redirect to `/onboarding/4`

---

#### Screen: /onboarding/4 — Athletes & Teams to Follow
**Purpose:** Follow favorite athletes and teams.

**Layout:**
- Header: "Who do you follow?"
- Subtitle: "Pick your favorite athletes and teams"
- Search bar: "Search athletes, teams..."
- Recently added/popular athletes section
- Recently added/popular teams section
- CTA: "Complete Setup" → goto `/home`

**Components:**
- SearchInput
- AthleteTile × N (pressable, shows avatar + name + league + team)
- TeamTile × N
- CompletionButton

**Data Flow:**
1. User searches or taps suggestions
2. Tap athlete/team → `POST /user_following`
3. Tap "Complete Setup"
4. Redirect to `/home`

**API Calls:**
- `GET /athletes?search=` (search)
- `GET /teams?search=` (search)
- `POST /user_following`
  - Input: `{ followable_type: 'athlete' | 'team', athlete_id? team_id? }`

---

#### Screen: /onboarding/5 — Dream Experience
**Purpose:** Capture user's aspirational collectibles goal.

**Layout:**
- Header: "What's your dream?"
- Subtitle: "Tell us your dream experience — we'll alert you if it comes true"
- Text input (large, multi-line): "e.g., Surf trip with son"
- Optional description field
- CTA: "Let's Go!" → goto `/home`

**Components:**
- TextInput (primary)
- TextArea (secondary)
- CompletionButton

**Data Flow:**
1. User types dream
2. Tap "Let's Go!"
3. `POST /dream_experiences`
4. Redirect to `/home` with celebration animation

**API Calls:**
- `POST /dream_experiences`
  - Input: `{ dream_text, description }`

---

### 4.3 Core Navigation (Tab-Based)

All core screens use bottom tab navigation:
- **Home** (🏠) → `/home`
- **Saved** (❤️) → `/saved`
- **Explore** (🔍) → `/explore`
- **Profile** (👤) → `/profile`

---

### 4.4 /home — Personalized Feed

**Purpose:** Primary interface. Shows personalized event recommendations based on user preferences, location, and follows.

**Layout:**
```
┌─────────────────────────────┐
│  Scout          [Avatar: B] │  ← Header
├─────────────────────────────┤
│ Hey Brett 👋                │  ← Greeting
│ 20 events found near you.   │
├─────────────────────────────┤
│ [Filter] [Sort By ▼]        │  ← Action bar
├─────────────────────────────┤
│ Perfect Match (3)           │  ← Tab 1
│ Strong Match (8)            │  ← Tab 2
│ Nearby (9)                  │  ← Tab 3
├─────────────────────────────┤
│ ┌─────────────────────────┐ │
│ │ Card Show Extravaganza  │ │
│ │ Mar 29 • 10am-4pm       │ │
│ │ Chicago Convention Ctr  │ │
│ │ 5.2 miles away          │ │
│ │ 🃏 💼 ✨ [Free entry]  │ │
│ │ Time Running Out        │ │
│ └─────────────────────────┘ │
├─────────────────────────────┤
│ [Event Card 2]              │
│ [Event Card 3]              │
│ ...                         │
└─────────────────────────────┘
```

**Components:**
- Header (logo, avatar button)
- GreetingSection (name, event count)
- FilterButton (→ `/home/filter`)
- SortButton (→ `/home/sort`)
- MatchQualityTabs (3 tabs: Perfect, Strong, Nearby)
- EventCard (reusable, appears in all list views)
  - Title, date/time, venue + distance
  - Category badges
  - Urgency labels (New, Time Running Out, Last Chance)
  - Save button
- BottomTabNavigator

**Data Sources:**
```typescript
// Query: personalized events for logged-in user
GET /events?
  - filter by user location (within radius)
  - filter by user followed categories
  - filter by user followed leagues
  - filter by user followed athletes/teams
  - sort by relevance (perfect match → strong → nearby)
  - limit 50
```

**RLS Filter (server-side):**
```sql
-- Supabase RLS automatically filters to:
-- 1. Published events (published_at IS NOT NULL)
-- 2. Not expired (expires_at > NOW())
-- 3. Future events (event_date > NOW() OR event_date IS NULL)
```

**Calculations (client-side):**
- **Match Quality:**
  - Perfect Match: event has user's followed athlete/team + followed category + within radius
  - Strong Match: event has user's followed category + within radius
  - Nearby: within radius, any category
- **Distance:** Haversine calculation (user location vs. event lat/lng)
- **Urgency Labels:**
  - "New" if created_at < 7 days ago
  - "Time Running Out" if event_date < 14 days from now
  - "Last Chance" if event_date < 3 days from now

**User Interactions:**
- Swipe to filter → `/home/filter`
- Tap sort button → `/home/sort`
- Tap event card → `/event/{id}`
- Long-press event → save event (via `POST /saved_events`)
- Tap avatar → `/profile`
- Tap tab nav → navigate

**API Calls:**
- `GET /events?filters=...` (TanStack Query: cache 5 min, background refetch)
- `POST /saved_events` (save event, optimistic update)
- `POST /event_views` (fire-and-forget: log view for analytics)

---

### 4.5 /home/filter (Modal)

**Purpose:** Filter events by category, league, distance, athlete/team, free/paid.

**Layout:**
```
┌─────────────────────────────┐
│ ← Filters         [✕ Close] │
├─────────────────────────────┤
│ DISTANCE RADIUS             │
│ [O] 25mi [O] 50mi [O] 100mi │
│ [O] Nationwide              │
├─────────────────────────────┤
│ CATEGORIES                  │
│ [X] Card Shows              │
│ [ ] Autograph Signings      │
│ ...                         │
├─────────────────────────────┤
│ LEAGUES                     │
│ [X] NFL                     │
│ ...                         │
├─────────────────────────────┤
│ ADMISSION                   │
│ [ ] Free events only        │
│ [ ] Paid events only        │
├─────────────────────────────┤
│ [Apply Filters]             │
└─────────────────────────────┘
```

**Components:**
- FilterSection × N (each with toggles)
- ApplyButton

**State Management:**
- Zustand store (filterStore): `{ radius, categories, leagues, admissionType }`

**User Interactions:**
- Toggle filters (optimistic update to store)
- Tap "Apply" → close modal, re-query `/events` with new filters
- Tap "✕" → discard changes, close

**API Calls:**
- `GET /events?filters=...` (with new filter params)

---

### 4.6 /home/sort (Modal)

**Purpose:** Select event list sort order.

**Layout:**
```
┌─────────────────────────────┐
│ ← Sort          [✕ Close]   │
├─────────────────────────────┤
│ (O) Closest first           │
│ ( ) Soonest first           │
│ ( ) Newest added            │
│ ( ) Most attendees          │
│ ( ) Trending                │
│ ( ) Free events first       │
└─────────────────────────────┘
```

**Components:**
- RadioGroup (6 options)

**State Management:**
- Zustand store: `{ sortBy }`

**User Interactions:**
- Tap radio → update store
- Close modal → re-sort home feed

---

### 4.7 /explore — Browse All Events

**Purpose:** Unfiltered event catalog. Discovery interface for events outside user's direct matches.

**Layout:**
```
┌─────────────────────────────┐
│ Explore                     │  ← Header
├─────────────────────────────┤
│ [Search events, athletes...] │
├─────────────────────────────┤
│ [Event Type ▼] [Sort By ▼] │
├─────────────────────────────┤
│ [Event Card 1]              │
│ [Event Card 2]              │
│ [Event Card 3]              │
│ ...                         │
│ [Load More]                 │  ← Pagination
└─────────────────────────────┘
```

**Components:**
- SearchInput
- EventTypeFilter (dropdown)
- SortButton
- EventCardList (pagination with `TanStack Query` infinite query)

**Data Source:**
```typescript
GET /events?
  - no personalization filters
  - sort by relevance or user-selected sort
  - limit 20, offset/pagination
```

**User Interactions:**
- Type in search → filter by title, description, athlete names (server-side)
- Tap event type filter → show only that category
- Scroll to bottom → auto-load next 20 events (infinite scroll)
- Tap event card → `/event/{id}`
- Tap event heart → save event

**API Calls:**
- `GET /events?search=...&category=...&offset=...` (infinite query, cache 5 min)
- `POST /saved_events`
- `POST /event_views`

---

### 4.8 /event/{id} — Event Detail

**Purpose:** Full event information, attended athletes, confirm attendance, save event.

**Layout:**
```
┌─────────────────────────────┐
│ ← [Hero Image]      [❤️]   │
├─────────────────────────────┤
│ 🃏 💼 ✨                   │  ← Category badges
│ Card Show Extravaganza      │  ← Title
├─────────────────────────────┤
│ March 29, 2026              │
│ 10:00 AM - 4:00 PM          │
│ Chicago Convention Center   │
│ 123 Main St, Chicago, IL    │
│ 5.2 miles away              │
├─────────────────────────────┤
│ ABOUT                       │
│ The largest regional card   │
│ show in the midwest...      │
├─────────────────────────────┤
│ ADMISSION                   │
│ Free entry                  │
├─────────────────────────────┤
│ CONFIRMED ATTENDEES (3)     │
│ [Avatar] Stephen Curry      │  ← Athlete tile
│          NBA • Golden State │
│ [Avatar] LaMelo Ball        │
│          NBA • Charlotte    │
│ [Avatar] Jayson Tatum       │
│          NBA • Boston       │
├─────────────────────────────┤
│ SOURCE: Eventbrite          │
│ [View on Eventbrite]        │
├─────────────────────────────┤
│ [Save Event] [Share Event]  │
└─────────────────────────────┘
```

**Components:**
- BackButton
- HeroImage
- SaveButton (heart, filled/unfilled state)
- CategoryBadges
- Title
- DateTimeLocation
- DistanceDisplay
- AboutSection (description)
- AdmissionSection (free/paid, price, notes)
- ConfirmedAttendeesSection (athlete cards)
- SourceLink (external URL)
- ActionButtonBar (Save, Share)

**Data Source:**
```typescript
GET /events/{id}
  - include athlete array (via event_athletes join)
  - include category name
  - compute distance from user location
```

**RLS Query:**
```sql
SELECT
  e.*,
  c.name as category_name,
  array_agg(json_build_object(
    'id', a.id,
    'name', a.name,
    'league', a.league,
    'team', a.team,
    'image_url', a.image_url
  )) as athletes
FROM events e
LEFT JOIN categories c ON e.category = c.id
LEFT JOIN event_athletes ea ON e.id = ea.event_id
LEFT JOIN athletes a ON ea.athlete_id = a.id
WHERE e.id = $1 AND e.published_at IS NOT NULL
GROUP BY e.id;
```

**User Interactions:**
- Tap back → `/home` or previous route
- Tap heart → `POST /saved_events` (or `DELETE /saved_events/{id}` if already saved)
- Tap athlete card → `/athlete/{id}` (future: profile view)
- Tap "View on Eventbrite" → open external URL (expo.linking)
- Tap "Share Event" → native share sheet

**API Calls:**
- `GET /events/{id}` (cache: 30 min)
- `POST /saved_events`
- `DELETE /saved_events/{id}`
- `POST /event_views` (fire-and-forget)

---

### 4.9 /saved — Saved Events

**Purpose:** User's bookmarked events. Personalized collection.

**Layout:**
```
┌─────────────────────────────┐
│ Saved Events       [0]      │
├─────────────────────────────┤
│ You haven't saved any       │
│ events yet.                 │
│                             │
│ [Explore Events]            │
│       OR                    │
│                             │
│ [Event Card 1]              │
│ [Event Card 2]              │
│ ...                         │
└─────────────────────────────┘
```

**Components:**
- Header with event count
- EmptyState (if no saved events)
- EventCardList (saved events only)
- ExploreButton (CTA to `/explore`)

**Data Source:**
```typescript
GET /saved_events?user_id={id}
  - join with events table
  - filter published events only
  - sort by saved date (newest first)
```

**User Interactions:**
- Tap event card → `/event/{id}`
- Tap heart on card → remove from saved (optimistic update)
- Tap "Explore Events" → `/explore`

**API Calls:**
- `GET /saved_events?user_id=...` (cache: 5 min)
- `DELETE /saved_events/{id}` (optimistic update)

---

### 4.10 /profile — Preferences & Settings

**Purpose:** User profile, preferences, settings, account management.

**Layout:**
```
┌─────────────────────────────┐
│ Profile                     │
├─────────────────────────────┤
│ [Avatar: B]                 │
│ Brett                       │
│ 60601 (Chicago)             │
├─────────────────────────────┤
│ STATS                       │
│ Alerts: 20 | Topics: 2 | Saved: 0 │
├─────────────────────────────┤
│ LOCATION & RADIUS           │
│ [Zip code input] 60601      │
│ [O] 25mi [●] 50mi [O] 100mi │
│ [O] Nationwide              │
├─────────────────────────────┤
│ INTERESTS                   │
│ [Tap to edit categories]    │
│ [Tap to edit leagues]       │
│ [Tap to edit athletes/teams]│
├─────────────────────────────┤
│ NOTIFICATIONS               │
│ [Quiet hours toggle]        │
│ [00:00 - 08:00]             │
├─────────────────────────────┤
│ SETTINGS                    │
│ [Dark mode toggle]          │
│ [App version: 1.0.0]        │
│ [Terms of Service]          │
│ [Privacy Policy]            │
├─────────────────────────────┤
│ [Sign Out]                  │
└─────────────────────────────┘
```

**Components:**
- ProfileHeader (avatar, name, zip code)
- StatsRow (alerts sent, topics, saved events)
- LocationSection (zip code input + radius selector)
- InterestsSection (edit buttons for categories, leagues, athletes)
- NotificationSection (quiet hours, toggles)
- SettingsSection (dark mode, version, links)
- SignOutButton

**Data Source:**
```typescript
GET /users/{id}
GET /user_preferences/{id}
GET /user_followed_categories?user_id={id}
GET /user_followed_leagues?user_id={id}
GET /user_following?user_id={id}
GET /notifications?user_id={id}&limit=1000 (for alert count)
GET /saved_events?user_id={id}&limit=1000 (for saved count)
```

**User Interactions:**
- Tap avatar → image picker → upload to Supabase Storage → `PATCH /users/{id}`
- Edit zip code → geocode → `PATCH /users/{id}`
- Change radius → `PATCH /users/{id}`
- Tap "Edit Categories" → modal with toggles → `POST /user_followed_categories` (batch)
- Tap "Edit Leagues" → modal → `POST /user_followed_leagues` (batch)
- Tap "Edit Athletes/Teams" → search modal → `POST /user_following` (batch)
- Toggle quiet hours → `PATCH /notification_settings/{id}`
- Toggle dark mode → Zustand store (local)
- Tap "Sign Out" → clear tokens → redirect to `/auth/splash`

**API Calls:**
- `PATCH /users/{id}` (zip code, avatar)
- `PATCH /user_preferences/{id}` (radius, alert frequency)
- `POST /user_followed_categories` (batch)
- `DELETE /user_followed_categories/{id}` (remove)
- `PATCH /notification_settings/{id}` (quiet hours)
- `POST /auth/logout` (clear session)

---

### 4.11 /profile/dream-experience (Modal/Screen)

**Purpose:** Edit or view user's dream experience.

**Layout:**
```
┌─────────────────────────────┐
│ ← Dream Experience  [✕]     │
├─────────────────────────────┤
│ "What's your dream?"        │
│ Tell us your dream — we'll  │
│ alert you if it comes true. │
├─────────────────────────────┤
│ [Text input]                │
│ e.g., Surf trip with son    │
│                             │
│ [Description input]         │
│ (optional)                  │
├─────────────────────────────┤
│ [Save Dream]                │
└─────────────────────────────┘
```

**Components:**
- TextInput (main)
- TextArea (description)
- SaveButton

**Data Flow:**
1. User types dream
2. Tap "Save Dream"
3. `PATCH /dream_experiences/{id}` or `POST /dream_experiences`
4. Close modal

---

## 5. ONBOARDING FLOW (Detailed)

### Entry Point
- User launches app
- App checks `auth.currentUser`
- If unauthenticated → `/auth/splash`
- If authenticated but `onboarding_complete = false` → `/onboarding/1`
- If authenticated + onboarding done → `/home`

### Onboarding Sequence
1. **Location & Radius** (`/onboarding/1`) — geo-enables the app
2. **Categories** (`/onboarding/2`) — event type interests
3. **Leagues** (`/onboarding/3`) — sports preferences
4. **Athletes & Teams** (`/onboarding/4`) — follow favorites
5. **Dream Experience** (`/onboarding/5`) — aspirational goal

### Completion
- After step 5, set `users.onboarding_complete = true`
- Redirect to `/home` with celebratory animation
- Home feed immediately shows personalized events

### Skip Option
- User can skip any step (except location) with "Skip for now" button
- Onboarding marked complete regardless
- Profile later allows editing all preferences

### Data Persistence
All onboarding choices are saved to Supabase in real-time (optimistic updates):
- `users` table (zip code, lat/lng, radius)
- `user_followed_categories` (many-to-many)
- `user_followed_leagues` (many-to-many)
- `user_following` (athletes/teams)
- `dream_experiences` (text)

---

## 6. ADMIN PANEL SPEC

### Purpose
Ryan and team review scraped events, approve for publishing, manage athletes/teams, view analytics.

### Tech Stack
- **Framework:** Next.js 14+ (App Router)
- **Admin UI:** Refine (React-admin) — data grid, form builder, auth
- **Database:** Direct Supabase queries (via admin RLS bypass)
- **Deployment:** Vercel

### Core Pages

#### /admin/dashboard
**Purpose:** High-level stats and queue overview.

**Sections:**
- **Key Metrics:**
  - Total events published this month
  - Pending review events count (high-priority alert)
  - Active users
  - Alerts sent today
- **Pending Review Queue:** Count and recent submissions
- **New Events This Week:** Chart
- **Top Athletes (by saves):** List
- **Incoming Notifications:** Pipeline status

**Components:**
- StatCard × 4 (metric + trend)
- BarChart (events by week)
- DataTable (pending events, sortable)

---

#### /admin/events
**Purpose:** Full event management (CRUD).

**Layout:**
- Refine DataGrid with all events
- Filters: status (published/pending), date range, category, city
- Bulk actions: approve, reject, feature, delete
- Search by title, venue, address
- Export to CSV

**Columns:**
- Title
- Venue
- Date
- Category
- Status (Published, Pending, Rejected)
- Athletes (count)
- Actions (edit, delete, preview)

**Edit Form:**
- All event fields (title, description, date, venue, address, lat/lng, admission, image, etc.)
- Multi-select for athletes
- Category dropdown
- Publish/reject buttons

---

#### /admin/events/pending-review
**Purpose:** Approval queue for scraped events.

**Layout:**
- Refine DataGrid showing only `review_status = 'pending'`
- For each row:
  - Raw event data (from scrape)
  - Reviewer notes field
  - Approve / Reject buttons
  - Link to "preview in app"
- Sort by date scraped (oldest first)

**Workflow:**
1. Admin reviews pending event
2. Taps "Preview in App" to see how it renders
3. If good → "Approve" → event moves to `published_at = now()`, visible in app
4. If bad → "Reject" + optional notes → event marked `review_status = 'rejected'`
5. If duplicate → "Mark as Duplicate" → flag for ML training

---

#### /admin/athletes
**Purpose:** Manage athlete database.

**Columns:**
- Name
- League
- Team
- Position
- Number
- Image
- External ID (ESPN, etc.)
- Actions (edit, delete)

**Add New Athlete:**
- Form with name, league, team, position, number, image upload, external ID
- Save → athlete available for event assignment

---

#### /admin/teams
**Purpose:** Manage sports teams.

**Columns:**
- Name
- League
- Logo
- External ID
- Actions (edit, delete)

---

#### /admin/notifications
**Purpose:** Compose and send targeted notifications.

**Layout:**
- **Send Now:**
  - Title input
  - Body input
  - Target filter: by category, league, location, athlete follow
  - Preview: "3,200 users will receive this"
  - Send button
- **Scheduled:** Calendar view of past/future notifications
- **Metrics:** Opens, clicks, conversions by notification

**API Call:**
- `POST /admin/notifications`
  - Input: `{ title, body, target_filter, send_at? }`
  - Triggers Supabase Edge Function to send via expo-notifications

---

#### /admin/analytics
**Purpose:** User metrics and engagement data.

**Sections:**
- **Users:** Total, daily active, retention cohorts
- **Events:** Total published, pending, rejected, by category
- **Engagement:** Alerts sent, clicks, saves, event views
- **Geography:** Heatmap of user locations, events by region
- **Athletes:** Most-followed, most-appearing-at-events

**Visualizations:**
- Line chart (DAU over time)
- Map (user locations)
- Heatmap (event popularity)
- Table (top athletes/teams)

---

### Admin Authentication
- Supabase Auth with role-based claims
- Roles: `admin`, `moderator`, `viewer`
- `admin`: full CRUD on events, settings, notifications
- `moderator`: read/approve events only
- `viewer`: read-only analytics

---

## 7. PUSH NOTIFICATION ARCHITECTURE

### Expo Notifications + Supabase Edge Functions

#### Setup
1. **Client (iOS):**
   - `expo-notifications` installed
   - User grants permission at first launch (or in settings)
   - `ExpoPushToken` captured and stored in `users.push_token`

2. **Server (Supabase):**
   - Edge Function listens for events via Realtime or scheduled job
   - Queries eligible users based on preferences/location/follows
   - Calls Expo Push Notification API to send

#### Notification Triggers

**Event-Triggered (Real-time):**
```
When new event is published:
1. Edge Function listens for published_at update
2. Checks each user's preferences:
   - Is event within radius?
   - User follows this category?
   - User follows athlete/team in event?
3. If match: send notification to that user's push_token
```

**Daily Digest (Scheduled):**
```
Every morning at 8am (user's timezone):
1. Cron job queries events created in last 24h
2. For each user with alerts_enabled:
   - Find events matching their criteria
   - Batch into digest
   - Send single "New events near you" notification
```

**Dream Experience (Ad-hoc):**
```
When new event is published:
1. NLP model analyzes event description + dream_text
2. If match confidence > 0.8:
   - Send alert: "We found your dream! Card show..."
```

#### Edge Function: notify_on_event
```typescript
// supabase/functions/notify_on_event/index.ts

import { serve } from 'https://deno.land/std@0.168.0/http/server.ts'
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2.0.0'
import { Expo } from 'https://esm.sh/expo-server-sdk@3.6.0'

const supabase = createClient(
  Deno.env.get('SUPABASE_URL')!,
  Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!
)

const expo = new Expo({
  accessToken: Deno.env.get('EXPO_ACCESS_TOKEN')!
})

serve(async (req) => {
  const { event_id } = await req.json()

  // Get event details
  const { data: event } = await supabase
    .from('events')
    .select('*')
    .eq('id', event_id)
    .single()

  if (!event) return new Response('Event not found', { status: 404 })

  // Find eligible users
  const { data: users } = await supabase
    .from('users')
    .select('id, push_token, email')
    .eq('notification_enabled', true)
    .eq('push_token', 'is.not', null)
    // Filter by location
    .lte(
      'haversine_distance',
      event.search_radius_miles
    )
    // Filter by followed categories
    .in('followed_categories', [event.category])

  // Send notifications
  const messages = users!.map((user) => ({
    to: user.push_token,
    sound: 'default',
    title: event.title,
    body: `${event.venue_name} - ${event.event_date}`,
    data: { event_id },
  }))

  const tickets = await expo.sendPushNotificationsAsync(messages)

  // Log results
  await supabase
    .from('notifications')
    .insert(
      users!.map((user, i) => ({
        user_id: user.id,
        event_id,
        title: event.title,
        body: messages[i].body,
        is_sent: tickets[i].status === 'ok',
        sent_at: new Date(),
      }))
    )

  return new Response('Notifications sent', { status: 200 })
})
```

#### Push Payload
```json
{
  "to": "ExponentPushToken[...]",
  "title": "Card Show Extravaganza",
  "body": "Chicago Convention Center - Mar 29, 10am",
  "data": {
    "event_id": "uuid",
    "action": "open_event"
  },
  "sound": "default"
}
```

#### Notification Settings
Users can control:
- Enable/disable all notifications
- Quiet hours (e.g., 10pm - 8am, no alerts)
- Alert frequency: instant, daily digest, weekly
- Category/league-specific toggles (via preferences)

---

## 8. AI EVENT DISCOVERY PIPELINE

### Architecture Overview
```
External Sources (Eventbrite, Ticketmaster, Venues, Facebook)
          ↓
    Web Scraper (Lambda or Edge Function)
          ↓
    AI Extraction (OpenAI/Claude)
          ↓
    `events_pending_review` (Raw + Confidence Score)
          ↓
    Admin Approval Queue
          ↓
    `events` (Published)
          ↓
    App (Notifications, Discovery)
```

### Scraper Implementation

#### Edge Function: scrape_events
```typescript
// supabase/functions/scrape_events/index.ts

import { serve } from 'https://deno.land/std@0.168.0/http/server.ts'
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2.0.0'

const supabase = createClient(
  Deno.env.get('SUPABASE_URL')!,
  Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!
)

const SOURCES = [
  {
    name: 'eventbrite',
    url: 'https://www.eventbrite.com/api/v3/events/search',
    searchTerms: ['card show', 'sports card', 'collectibles'],
  },
  {
    name: 'ticketmaster',
    url: 'https://app.ticketmaster.com/discovery/v2/events',
    searchTerms: ['sports', 'collectibles'],
  },
  {
    name: 'facebook',
    url: 'https://graph.facebook.com/v18.0/search',
    searchTerms: ['sports card event', 'collector meetup'],
  },
]

serve(async (req) => {
  // 1. Scrape from external sources
  const rawEvents = []
  for (const source of SOURCES) {
    const events = await scrapeSource(source)
    rawEvents.push(...events.map(e => ({ ...e, source: source.name })))
  }

  // 2. Extract details with AI
  const extractedEvents = []
  for (const event of rawEvents) {
    const extracted = await extractEventDetails(event)
    extractedEvents.push(extracted)
  }

  // 3. Deduplicate (check if event already exists)
  const uniqueEvents = deduplicateEvents(extractedEvents)

  // 4. Insert into pending_review table
  const { error } = await supabase
    .from('events_pending_review')
    .insert(
      uniqueEvents.map((e) => ({
        title: e.title,
        description: e.description,
        category: categorizeEvent(e.title, e.description),
        event_date: e.date,
        venue_name: e.venue,
        address: e.address,
        city: e.city,
        state: e.state,
        zip_code: e.zip,
        latitude: e.latitude,
        longitude: e.longitude,
        admission_type: e.admission_type,
        admission_price: e.admission_price,
        image_url: e.image_url,
        source_url: e.source_url,
        source_type: e.source_type,
        raw_data: e,
        scrape_timestamp: new Date(),
        review_status: 'pending',
      }))
    )

  return new Response(
    JSON.stringify({
      scraped: rawEvents.length,
      extracted: extractedEvents.length,
      unique: uniqueEvents.length,
      inserted: !error,
    }),
    { status: 200 }
  )
})

async function extractEventDetails(event: any) {
  // Call Claude API
  const response = await fetch('https://api.anthropic.com/v1/messages', {
    method: 'POST',
    headers: {
      'x-api-key': Deno.env.get('ANTHROPIC_API_KEY')!,
      'anthropic-version': '2023-06-01',
      'content-type': 'application/json',
    },
    body: JSON.stringify({
      model: 'claude-3-5-sonnet-20241022',
      max_tokens: 500,
      messages: [
        {
          role: 'user',
          content: `Extract event details from this raw event data. Return JSON:
{
  "title": "string",
  "description": "string",
  "date": "ISO 8601",
  "venue": "string",
  "address": "string",
  "city": "string",
  "state": "string",
  "zip": "string",
  "latitude": number,
  "longitude": number,
  "admission_type": "free" | "paid" | "tiered",
  "admission_price": number | null,
  "image_url": "string | null",
  "athlete_names": ["string"],
  "confidence": 0.0 - 1.0
}

Event: ${JSON.stringify(event)}`,
        },
      ],
    }),
  })

  const data = await response.json()
  return JSON.parse(data.content[0].text)
}

function deduplicateEvents(events: any[]) {
  // Group by (title + venue + date), keep highest confidence
  const grouped = events.reduce(
    (acc, e) => {
      const key = `${e.title}|${e.venue}|${e.date}`
      if (!acc[key] || e.confidence > acc[key].confidence) {
        acc[key] = e
      }
      return acc
    },
    {} as Record<string, any>
  )
  return Object.values(grouped)
}

function categorizeEvent(title: string, description: string) {
  const text = `${title} ${description}`.toLowerCase()
  if (text.includes('card show') || text.includes('trading card')) {
    return 'Card Shows'
  } else if (
    text.includes('autograph') ||
    text.includes('photo op') ||
    text.includes('meet and greet')
  ) {
    return 'Autograph Signings & Photo Ops'
  } else if (text.includes('athlete appearance') || text.includes('player')) {
    return 'Athlete Appearances'
  } else if (text.includes('mail-in') || text.includes('shipping')) {
    return 'Mail-in Signings'
  }
  return 'Memorabilia Events'
}
```

### Cron Schedule
- **Daily Scrape:** 2am UTC (run `scrape_events` function)
- **Weekly Dedup:** Sunday 1am UTC (clean duplicate pending events)
- **Monthly Archive:** 1st of month, archive old rejected events

### Approval Workflow
1. Raw events land in `events_pending_review`
2. Admin sees queue in dashboard at `/admin/events/pending-review`
3. Admin reviews, sees:
   - Title, description, date, venue
   - Raw scraped data (for context)
   - AI confidence score
   - Preview of how it looks in app
4. Admin clicks "Approve" → event published to `events` table
5. On publish, `POST /notify_on_event` triggers push notifications

### Athlete Extraction
- AI also extracts athlete names from event description
- On approval, system:
  1. Fuzzy-matches athlete names to `athletes` table
  2. If match confidence > 0.9, auto-links to `event_athletes`
  3. If below threshold, flags for manual review

---

## 9. BUILD PHASES

### Phase 1: Foundation (Weeks 1-3)
**Deliverables:**
- Project scaffold (Expo + TypeScript)
- Navigation structure (Expo Router, bottom tabs)
- Supabase schema (all tables created, RLS policies)
- Auth setup (sign in flow skeleton)
- Home screen skeleton with fake data
- Style system (NativeWind + design tokens)

**Testing:**
- App launches on iOS simulator
- Basic navigation between tabs works
- Supabase connection verified

**Definition of Done:**
- Codebase committed to GitHub
- All team members can run locally
- No console errors on launch

---

### Phase 2: Core Screens (Weeks 4-6)
**Deliverables:**
- Full auth flow (Apple Sign In, Google Sign In)
- All 5 onboarding screens functional
- Home feed (personalized event list)
- Event detail screen
- Explore screen (unfiltered browse)
- Saved events screen
- Profile screen with preferences

**Data Integration:**
- All screens wired to Supabase
- TanStack Query set up for caching
- Optimistic updates on save/like

**Testing:**
- Full user flow: sign up → onboarding → home → explore → detail → save
- Push notifications ready (token capture)
- Offline mode tested (TanStack Query fallback)

---

### Phase 3: Auth & Identity (Weeks 7-8)
**Deliverables:**
- Biometric auth (Face ID / Touch ID)
- Account linking (Apple + Google on same email)
- Profile editing fully functional
- User avatar upload to Supabase Storage
- Sign out flow

**Testing:**
- Face ID / Touch ID works on real device
- Avatar upload and display verified
- Session persistence across app restart

---

### Phase 4: Alerts & Intelligence (Weeks 9-11)
**Deliverables:**
- Push notifications fully functional (expo-notifications + Edge Function)
- Admin panel (Next.js + Refine)
- Event approval queue
- Event scraping pipeline (Python/Lambda)
- Athlete/team database management
- Push notification composer
- Dream experience matching

**Testing:**
- Send test push → verify on device
- Admin approves event → appears in app within 5 sec
- Dream experience AI triggers correct alerts
- Notification metrics tracked

---

### Phase 5: Polish & Ship (Weeks 12-13)
**Deliverables:**
- QA pass (all screens, all flows)
- Performance optimization (bundle size, load times)
- Accessibility audit (WCAG 2.1 AA)
- Privacy policy & ToS finalized
- Screenshots for App Store
- Promotional artwork

**Testing:**
- EAS Build successful (release build)
- TestFlight deployment
- Internal testing on real devices (iPhone 12+)
- Crash logs reviewed

**App Store Submission:**
- All metadata filled in
- Privacy labels configured
- Screenshots uploaded
- Submitted by June 7, 2026 deadline

---

## 10. APP STORE SUBMISSION CHECKLIST

### Pre-Submission (3 weeks before deadline)

**App Metadata:**
- [ ] App name: "TROV"
- [ ] Subtitle: "Event Discovery for Collectors"
- [ ] Description (max 170 chars)
- [ ] Keywords: "collectibles, events, sports cards, discovery"
- [ ] Category: "Lifestyle" or "Entertainment"
- [ ] Content rating (ESRB): likely "12+" (no mature content)

**Privacy & Legal:**
- [ ] Privacy Policy URL (hosted on website)
- [ ] Terms of Service URL
- [ ] Contact email for App Store support
- [ ] Privacy labels (Data Collection):
  - Identifiers: Name, Email (required for auth)
  - User ID: Yes (for preferences)
  - Device ID: Yes (push token)
  - Precise Location: Yes (for distance calculations)
  - Usage Data: Yes (event views, clicks)
  - Diagnostics: Yes (crash logs)

**Ratings & Review:**
- [ ] Age rating completed (IARC questionnaire)
- [ ] Content guidelines reviewed
- [ ] No prohibited content (gambling, illegal activity, etc.)

**Build & Testing:**
- [ ] TestFlight build uploaded and tested
- [ ] No crashes on iPhone 12, 13, 14 Pro, 15 Pro
- [ ] No privacy/data handling issues
- [ ] Push notifications tested end-to-end
- [ ] Biometric auth tested
- [ ] Offline mode tested

**Screenshots:**
- [ ] 5 screenshots per locale (English minimum)
  - Screenshot 1: Home feed
  - Screenshot 2: Event detail
  - Screenshot 3: Personalization
  - Screenshot 4: Saved events
  - Screenshot 5: Push notification
- [ ] Each screenshot includes brief caption (max 170 chars)
- [ ] Images 1242x2208 pixels (iPhone 6.5")

**Icon & Artwork:**
- [ ] App icon (1024x1024, no transparency)
- [ ] App preview video (optional but recommended): 30s walkthrough
- [ ] Promotional artwork for App Store featuring

**Sign-In Requirements:**
- [ ] Apple Sign In implemented (required by Apple for any OAuth)
- [ ] Demo account credentials provided for review (if needed)
- [ ] Sign-in flow is clear and non-disruptive

**Device Support:**
- [ ] Minimum iOS version: 14.0 (set in app.json)
- [ ] Supported device families: iPhone only (not iPad initially)
- [ ] Landscape/portrait orientation: portrait only

**Submission:**
- [ ] Release notes written (e.g., "Launch version: discover events, follow artists, get alerts")
- [ ] Version number set to 1.0.0
- [ ] Build number incremented
- [ ] Submit via App Store Connect

---

### Post-Submission
- Apple review typically takes 24-48 hours
- Monitor App Store Connect for review feedback
- Be prepared to provide demo account or clarification
- If rejected, address feedback and resubmit

---

## 11. RISK REGISTER

### High-Risk Items

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|-----------|
| **Supabase Rate Limits (API)** | Medium | High | Implement request debouncing, cache aggressively with TanStack Query, monitor usage dashboard |
| **Push Notification Delivery** | Medium | High | Test extensively, implement fallback to in-app alerts, monitor delivery metrics |
| **Event Data Quality** | High | Medium | Implement strong AI extraction + admin approval flow, feedback loop from users (flag bad data) |
| **User Adoption** | Medium | High | Launch with pre-populated event data, targeted social media campaign, influencer partnerships |
| **App Store Rejection** | Low | High | Privacy compliance, Apple Sign In, clear ToS/Privacy, test on real devices before submit |
| **Scaling (high DAU)** | Low | High | Use Supabase edge caching, consider CDN for images, read replicas for analytics |
| **Athlete/Team Data Accuracy** | Medium | Medium | Manual curation + AI extraction, link to official league data (ESPN API) |
| **Biometric Auth Failure** | Low | Medium | Fallback to password/email sign in, clear error messages |

### Medium-Risk Items

| Risk | Mitigation |
|------|-----------|
| **Timezone Issues** | Always use UTC in DB, convert to user timezone client-side |
| **Network Latency** | Implement skeleton loaders, optimistic updates, background sync |
| **Image Loading** | Use image compression, caching, lazy load off-screen |
| **Location Permissions** | Handle deny gracefully, offer manual zip code input |
| **Auth Token Expiry** | Refresh token automatically, re-auth if expired |

### Low-Risk Items
- Third-party API downtime (Expo, Eventbrite) — implement queue/retry
- Design inconsistencies — use design system rigorously
- Code quality drift — GitHub Actions CI/linting, PR reviews mandatory

---

## 12. DEPLOYMENT & OPERATIONS

### Local Development
```bash
# Setup
npm install
npx eas build --platform ios --local
npm run ios

# .env.development
EXPO_PUBLIC_SUPABASE_URL=https://dev.supabase.co
EXPO_PUBLIC_SUPABASE_ANON_KEY=...
```

### Staging (GitHub Develop Branch)
```bash
# On push to develop:
# 1. GitHub Actions lint + test
# 2. EAS Build (preview)
# 3. Auto-deploy admin panel to staging.trov.app
```

### Production (GitHub Main Branch)
```bash
# On push to main:
# 1. GitHub Actions lint + test + build
# 2. EAS Build (production)
# 3. Manual approval for App Store submit
# 4. Admin panel deployed to trov.app
```

### Monitoring
- **Sentry:** Error tracking (frontend + backend)
- **LogRocket:** Session replay (opt-in for user support)
- **PostHog:** Product analytics (event tracking)
- **Supabase Dashboard:** Database health, API metrics

### Backup & Disaster Recovery
- Supabase automated backups (daily)
- GitHub as source of truth for code
- Admin export of events/users monthly to Google Drive

---

## 13. FUTURE ROADMAP (Post-Launch)

### Phase 6: Monetization (Q3 2026)
- Event listing premiums (venue featured placements)
- Sponsored notifications (brands reach collectors)
- In-app marketplace (Fanatics integration for card purchases)
- Premium tier (ad-free, early access to events)

### Phase 7: Community Features (Q4 2026)
- Collector profiles & following
- Event reviews & ratings
- Collector groups/forums
- Live chat during events

### Phase 8: Advanced Intelligence (Q1 2027)
- ML-powered recommendation engine (TensorFlow Lite)
- Trend detection (emerging athletes/teams)
- Price prediction (collectible card values)
- Wishlist matching (AI suggests events for dreams)

### Phase 9: Expansion (Q2 2027)
- Android app
- Web app (browser version)
- International events (EU, Asia)
- Other collectibles (art, vintage, sneakers)

---

## 14. APPENDIX: TECH DEBT & DECISIONS

### Architecture Decisions

**Why Expo over Bare React Native?**
- Faster development velocity (no native code needed initially)
- EAS Build simplifies CI/CD
- Can eject to bare RN later if needed

**Why Supabase over Firebase?**
- Direct PostgreSQL access (more powerful for complex queries)
- Better for event geospatial queries (PostGIS)
- RLS for fine-grained auth
- Cheaper at scale

**Why TanStack Query over Redux?**
- Server-state management is simpler
- Built-in caching, deduplication, background sync
- Smaller bundle size
- Less boilerplate

**Why NativeWind over StyleSheet?**
- Tailwind familiarity (shorter onboarding for team)
- Consistent spacing/sizing tokens
- Better maintainability

### Known Limitations (Phase 1)

1. **No Offline-First:** App requires network. Could add SQLite sync in Phase 4.
2. **Single Event Image:** Only 1 image per event. Could add gallery in Phase 7.
3. **No Comments/Reviews:** Events not yet rated by users. Could add Phase 6.
4. **Manual Athlete Data:** Athlete details manually curated. AI extraction in Phase 4.
5. **No Team Messaging:** Can't DM other collectors yet. Phase 7.

### Technical Debt To Avoid

- **Don't hardcode strings:** Use i18n (expo-localization) from day 1
- **Don't skip tests:** Write tests for auth, notifications, critical flows
- **Don't mix state management:** Zustand for UI state, TanStack Query for server state, nothing else
- **Don't over-engineer early:** KISS principle, add complexity only when proven needed

---

## 15. DEVELOPMENT STANDARDS

### Code Style
- TypeScript strict mode enabled
- ESLint + Prettier configured
- Naming: `camelCase` for variables/functions, `PascalCase` for components
- File structure: screens → components → hooks → utils → services

### Commit Convention
```
feat(auth): implement Apple Sign In
fix(home): correct distance calculation
docs(README): update setup instructions
test(notifications): add unit tests
chore(deps): upgrade Expo SDK
```

### PR Process
1. Feature branch from `develop`
2. PR with description, before/after screenshots
3. Code review + approve required
4. Merge to develop, auto-deploy to staging
5. Periodic merges to main (production releases)

### Documentation
- Inline comments for non-obvious logic
- JSDoc for exported functions
- README for setup and architecture overview
- CHANGELOG tracking all releases

---

## 16. SUCCESS METRICS (Post-Launch)

### App Store
- [ ] 4.5+ star rating (after 100 reviews)
- [ ] 50K+ downloads by end of Q3 2026
- [ ] 10K+ monthly active users by end of Q3 2026

### Engagement
- [ ] 2+ sessions per week (average user)
- [ ] 30% DAU/MAU ratio
- [ ] 5+ events saved per active user
- [ ] 50% push notification open rate

### Business
- [ ] Fanatics Fest 2026 attendance up 20% (measured via survey)
- [ ] 100+ events listed in app
- [ ] 50+ venues/organizers actively posting
- [ ] $10K+ monthly revenue (post-June 2026)

---

## 17. CONTACT & OWNERSHIP

**Product Owner:** Ryan Wanderer (Founder)
**Lead Engineer:** Claude (Anthropic) + Beryl Jacobson (Antidote Group)
**Admin Panel:** Ryan Wanderer + Moderators (TBD)
**Questions:** TROV@antidote.group

**Last Updated:** March 30, 2026
**Next Review:** After Phase 2 (end of Week 6)

---

**END OF TECHNICAL SPEC**
