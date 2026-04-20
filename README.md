# SoundFit — Project Planning & Build Reference

This document captures the full design decisions, architecture, and Claude Code build prompt for **SoundFit** — a web app that recommends outfits based on a user's Spotify music taste.

---

## Table of Contents

1. [Project Concept](#1-project-concept)
2. [How It Works](#2-how-it-works)
3. [Key Design Decisions](#3-key-design-decisions)
4. [Tech Stack](#4-tech-stack)
5. [Architecture Overview](#5-architecture-overview)
6. [Folder Structure](#6-folder-structure)
7. [Environment Variables](#7-environment-variables)
8. [Claude Code Build Prompt](#8-claude-code-build-prompt)
9. [Before You Run Claude Code](#9-before-you-run-claude-code)
10. [Running the App](#10-running-the-app)

---

## 1. Project Concept

SoundFit connects to a user's Spotify account, analyzes the lyrics of their most-listened-to songs, and uses an LLM to generate personalized outfit recommendations with shoppable links — all based on the aesthetics, moods, and style cues found in the music they actually listen to.

---

## 2. How It Works

1. User logs in via **Spotify OAuth 2.0 (PKCE flow)**
2. The app fetches the user's **top 5 artists** (medium-term listening history)
3. For each artist, it fetches their **top 3 tracks** via the Spotify API
4. Lyrics for each track are fetched via the **Genius API** (search + HTML scrape)
5. Artist names + lyrics are sent to **Claude** with a fashion-stylist system prompt
6. Claude returns a **style profile** and **3 outfit recommendations**, each with 4–5 items and search links to ASOS, Depop, and Amazon
7. Results are displayed on a clean dark-themed dashboard

---

## 3. Key Design Decisions

### Lyrics over a static taxonomy
An earlier approach considered maintaining a hand-curated `artist_taxonomy.json` mapping artists to vibe descriptors. This was dropped in favor of **live lyric analysis** because:
- It grounds recommendations in what the user actually listens to, not a generic archetype
- It surfaces specific clothing references, brand mentions, color palettes, and mood signals directly from lyrics
- It works for long-tail artists not in any pre-built catalog
- The Genius API + BeautifulSoup scraper handles lyrics fetching at runtime

If Genius can't find lyrics for a track, the app skips it gracefully and uses whatever lyrics it did find.

### PKCE OAuth (no client secret on the frontend)
The Spotify OAuth flow uses **PKCE (Proof Key for Code Exchange)**:
- The frontend generates a random `codeVerifier`, hashes it to produce a `codeChallenge`, and redirects the user to Spotify
- Spotify redirects back to `/callback` with an authorization `code`
- The frontend sends the `code` + `codeVerifier` to the FastAPI backend
- The backend exchanges them for an access token with Spotify (no client secret needed for PKCE)
- The token is stored in `localStorage` on the frontend

### TypeScript on the frontend
React + TypeScript is the current industry standard for new projects. The frontend uses strict TypeScript (`"strict": true` in tsconfig) with all shared types defined in `src/types/index.ts`.

### Python + FastAPI on the backend
FastAPI was chosen for its async-first design (important for parallel Spotify + Genius HTTP calls), automatic OpenAPI docs, and Pydantic validation. All external calls use `httpx.AsyncClient`.

---

## 4. Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React 18, TypeScript, Vite, React Router v6 |
| Backend | Python 3.11+, FastAPI, httpx, pydantic-settings |
| Auth | Spotify OAuth 2.0 with PKCE |
| Lyrics | Genius API + BeautifulSoup HTML scraping |
| LLM | Anthropic Claude (`claude-sonnet-4-20250514`) |
| Styling | Plain CSS with custom properties (dark theme) |

---

## 5. Architecture Overview

```
Browser (React + TypeScript)
  │
  │  1. Redirects user to Spotify OAuth
  │  2. Receives /callback with auth code
  │  3. Sends code + verifier to backend
  │  4. Receives access token
  │  5. Calls POST /outfits/recommend
  │
FastAPI Backend (Python)
  │
  ├── routers/spotify.py     — POST /auth/callback (token exchange)
  ├── routers/outfits.py     — POST /outfits/recommend
  │
  ├── services/spotify_client.py  — Fetches top artists + top tracks
  ├── services/genius_client.py   — Searches Genius, scrapes lyrics
  └── services/llm_service.py     — Builds prompt, calls Claude API
  │
  ├── Spotify Web API        — Top artists, top tracks per artist
  ├── Genius API             — Song search + lyrics page URL
  └── Anthropic Claude API   — Style profile + outfit recommendations
```

**Data flow for a recommendation request:**
```
top 5 artists → top 3 tracks each (15 tracks) →
lyrics for each track (Genius) →
[artist names + lyrics] → Claude →
style_profile + 3 outfit recommendations (each with 4-5 items + search links)
```

---

## 6. Folder Structure

```
soundfit/
├── frontend/
│   ├── index.html
│   ├── vite.config.ts
│   ├── tsconfig.json
│   ├── tsconfig.node.json
│   ├── package.json
│   ├── .env.example
│   └── src/
│       ├── main.tsx
│       ├── App.tsx
│       ├── index.css
│       ├── vite-env.d.ts
│       ├── types/
│       │   └── index.ts          ← All shared TS interfaces
│       ├── pages/
│       │   ├── Login.tsx          ← PKCE OAuth redirect
│       │   ├── Callback.tsx       ← Handles /callback, exchanges token
│       │   └── Dashboard.tsx      ← Top artists + outfit results
│       ├── components/
│       │   ├── ArtistCard.tsx
│       │   ├── OutfitResults.tsx
│       │   └── LoadingScreen.tsx
│       ├── hooks/
│       │   └── useAuth.ts         ← Token state + localStorage
│       └── services/
│           └── api.ts             ← Backend fetch calls
├── backend/
│   ├── main.py                    ← FastAPI app + CORS + routers
│   ├── config.py                  ← pydantic-settings env loader
│   ├── models.py                  ← Pydantic request/response models
│   ├── requirements.txt
│   ├── .env.example
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── spotify.py             ← POST /auth/callback
│   │   └── outfits.py             ← POST /outfits/recommend
│   └── services/
│       ├── __init__.py
│       ├── spotify_client.py      ← get_top_artists, get_top_tracks
│       ├── genius_client.py       ← search_song, get_lyrics (scraper)
│       └── llm_service.py         ← Claude prompt + response parser
└── README.md
```

---

## 7. Environment Variables

### `frontend/.env` (copy from `.env.example`)

```env
VITE_SPOTIFY_CLIENT_ID=your_spotify_client_id
VITE_REDIRECT_URI=http://localhost:5173/callback
VITE_API_BASE_URL=http://localhost:8000
```

### `backend/.env` (copy from `.env.example`)

```env
SPOTIFY_CLIENT_ID=your_spotify_client_id
SPOTIFY_CLIENT_SECRET=your_spotify_client_secret
SPOTIFY_REDIRECT_URI=http://localhost:5173/callback
GENIUS_ACCESS_TOKEN=your_genius_access_token
ANTHROPIC_API_KEY=your_anthropic_api_key
```

---

## 8. Claude Code Build Prompt

Paste the following into Claude Code to scaffold and implement all files:

---

Build a full-stack web app called **SoundFit** that recommends outfits based on a user's Spotify listening history. The app fetches the user's top 5 artists, retrieves their top tracks, fetches lyrics via the Genius API, analyzes the lyrics with Claude to extract style/aesthetic signals, and returns outfit recommendations with shoppable search links.

### Tech Stack

- **Frontend**: React with TypeScript, Vite, React Router v6
- **Backend**: Python, FastAPI, httpx, python-dotenv
- **Auth**: Spotify OAuth 2.0 with PKCE (frontend-initiated, backend token exchange)
- **Lyrics**: Genius API (search + scrape lyrics via BeautifulSoup)
- **LLM**: Anthropic Claude API (`claude-sonnet-4-20250514`)

---

### Project Structure

Create the following folder structure exactly:

```
soundfit/
├── frontend/
│   ├── index.html
│   ├── vite.config.ts
│   ├── tsconfig.json
│   ├── tsconfig.node.json
│   ├── package.json
│   ├── .env.example
│   └── src/
│       ├── main.tsx
│       ├── App.tsx
│       ├── index.css
│       ├── vite-env.d.ts
│       ├── types/
│       │   └── index.ts
│       ├── pages/
│       │   ├── Login.tsx
│       │   ├── Callback.tsx
│       │   └── Dashboard.tsx
│       ├── components/
│       │   ├── ArtistCard.tsx
│       │   ├── OutfitResults.tsx
│       │   └── LoadingScreen.tsx
│       ├── hooks/
│       │   └── useAuth.ts
│       └── services/
│           └── api.ts
├── backend/
│   ├── main.py
│   ├── config.py
│   ├── models.py
│   ├── requirements.txt
│   ├── .env.example
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── spotify.py
│   │   └── outfits.py
│   └── services/
│       ├── __init__.py
│       ├── spotify_client.py
│       ├── genius_client.py
│       └── llm_service.py
└── README.md
```

---

### Environment Variables

#### `frontend/.env.example`
```
VITE_SPOTIFY_CLIENT_ID=your_spotify_client_id
VITE_REDIRECT_URI=http://localhost:5173/callback
VITE_API_BASE_URL=http://localhost:8000
```

#### `backend/.env.example`
```
SPOTIFY_CLIENT_ID=your_spotify_client_id
SPOTIFY_CLIENT_SECRET=your_spotify_client_secret
SPOTIFY_REDIRECT_URI=http://localhost:5173/callback
GENIUS_ACCESS_TOKEN=your_genius_access_token
ANTHROPIC_API_KEY=your_anthropic_api_key
```

---

### Frontend Files

#### `frontend/package.json`
```json
{
  "name": "soundfit-frontend",
  "private": true,
  "version": "0.1.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "tsc && vite build",
    "preview": "vite preview"
  },
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-router-dom": "^6.22.0"
  },
  "devDependencies": {
    "@types/react": "^18.2.0",
    "@types/react-dom": "^18.2.0",
    "@vitejs/plugin-react": "^4.2.0",
    "typescript": "^5.3.0",
    "vite": "^5.1.0"
  }
}
```

#### `frontend/tsconfig.json`
```json
{
  "compilerOptions": {
    "target": "ES2020",
    "useDefineForClassFields": true,
    "lib": ["ES2020", "DOM", "DOM.Iterable"],
    "module": "ESNext",
    "skipLibCheck": true,
    "moduleResolution": "bundler",
    "allowImportingTsExtensions": true,
    "resolveJsonModule": true,
    "isolatedModules": true,
    "noEmit": true,
    "jsx": "react-jsx",
    "strict": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noFallthroughCasesInSwitch": true
  },
  "include": ["src"],
  "references": [{ "path": "./tsconfig.node.json" }]
}
```

#### `frontend/tsconfig.node.json`
```json
{
  "compilerOptions": {
    "composite": true,
    "skipLibCheck": true,
    "module": "ESNext",
    "moduleResolution": "bundler",
    "allowSyntheticDefaultImports": true
  },
  "include": ["vite.config.ts"]
}
```

#### `frontend/vite.config.ts`
```ts
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
  },
})
```

#### `frontend/src/vite-env.d.ts`
```ts
/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_SPOTIFY_CLIENT_ID: string
  readonly VITE_REDIRECT_URI: string
  readonly VITE_API_BASE_URL: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}
```

#### `frontend/index.html`
```html
<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>SoundFit</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.tsx"></script>
  </body>
</html>
```

#### `frontend/src/types/index.ts`
```ts
export interface Artist {
  id: string
  name: string
  genres: string[]
  images: { url: string; width: number; height: number }[]
  popularity: number
  external_urls: { spotify: string }
}

export interface OutfitRecommendation {
  title: string
  description: string
  aesthetic: string
  items: OutfitItem[]
}

export interface OutfitItem {
  name: string
  description: string
  search_links: SearchLink[]
}

export interface SearchLink {
  label: string
  url: string
}

export interface RecommendationResponse {
  artists: Artist[]
  style_profile: string
  recommendations: OutfitRecommendation[]
}
```

#### `frontend/src/hooks/useAuth.ts`
```ts
import { useState, useCallback } from 'react'

const TOKEN_KEY = 'soundfit_token'

export function useAuth() {
  const [accessToken, setAccessToken] = useState<string | null>(
    () => localStorage.getItem(TOKEN_KEY)
  )

  const setToken = useCallback((token: string) => {
    localStorage.setItem(TOKEN_KEY, token)
    setAccessToken(token)
  }, [])

  const clearToken = useCallback(() => {
    localStorage.removeItem(TOKEN_KEY)
    setAccessToken(null)
  }, [])

  return {
    accessToken,
    isAuthenticated: !!accessToken,
    setToken,
    clearToken,
  }
}
```

#### `frontend/src/services/api.ts`
```ts
import type { RecommendationResponse } from '../types'

const BASE_URL = import.meta.env.VITE_API_BASE_URL

export async function exchangeCodeForToken(code: string, codeVerifier: string): Promise<string> {
  const res = await fetch(`${BASE_URL}/auth/callback`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ code, code_verifier: codeVerifier }),
  })
  if (!res.ok) throw new Error('Token exchange failed')
  const data = await res.json()
  return data.access_token as string
}

export async function getRecommendations(accessToken: string): Promise<RecommendationResponse> {
  const res = await fetch(`${BASE_URL}/outfits/recommend`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${accessToken}`,
    },
  })
  if (!res.ok) throw new Error('Failed to get recommendations')
  return res.json() as Promise<RecommendationResponse>
}
```

#### `frontend/src/main.tsx`
```tsx
import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App'
import './index.css'

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
)
```

#### `frontend/src/App.tsx`
Set up React Router with three routes. Redirect `/dashboard` to `/` if unauthenticated.
```tsx
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { useAuth } from './hooks/useAuth'
import Login from './pages/Login'
import Callback from './pages/Callback'
import Dashboard from './pages/Dashboard'

export default function App() {
  const auth = useAuth()

  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Login isAuthenticated={auth.isAuthenticated} />} />
        <Route path="/callback" element={<Callback setToken={auth.setToken} />} />
        <Route
          path="/dashboard"
          element={
            auth.isAuthenticated
              ? <Dashboard accessToken={auth.accessToken!} clearToken={auth.clearToken} />
              : <Navigate to="/" replace />
          }
        />
      </Routes>
    </BrowserRouter>
  )
}
```

#### `frontend/src/pages/Login.tsx`
Full-page dark landing page. Implements Spotify PKCE OAuth:
1. Generate a random `codeVerifier` (43–128 chars, alphanumeric + `-._~`) using `crypto.getRandomValues`
2. SHA-256 hash it with `crypto.subtle.digest`, base64url encode to get `codeChallenge`
3. Store `codeVerifier` in `sessionStorage` under key `soundfit_pkce_verifier`
4. Build and navigate to the Spotify authorize URL with params: `client_id`, `response_type=code`, `redirect_uri`, `scope=user-top-read`, `code_challenge_method=S256`, `code_challenge`
5. If `isAuthenticated` is already true, render `<Navigate to="/dashboard" replace />`

UI: Centered layout, "SoundFit" heading, tagline "Your music, your style.", single "Connect with Spotify" button in Spotify green (`#1DB954`).

```ts
interface LoginProps {
  isAuthenticated: boolean
}
```

#### `frontend/src/pages/Callback.tsx`
Handles the OAuth return from Spotify:
1. On mount, read `code` from URL search params
2. Read `codeVerifier` from `sessionStorage` key `soundfit_pkce_verifier`
3. Call `exchangeCodeForToken(code, codeVerifier)` from `api.ts`
4. On success: call `setToken(token)`, clear sessionStorage key, navigate to `/dashboard`
5. On error: display error message with a link back to `/`
6. While loading: render `<LoadingScreen message="Connecting to Spotify..." />`

```ts
interface CallbackProps {
  setToken: (token: string) => void
}
```

#### `frontend/src/pages/Dashboard.tsx`
Main experience page:
1. On mount, call `getRecommendations(accessToken)`
2. While loading: `<LoadingScreen message="Analyzing your music taste..." />`
3. On error: error state with retry button
4. On success: full recommendations UI

Layout:
- Nav bar: "SoundFit" logo left, "Disconnect" button right (calls `clearToken`, navigates to `/`)
- "Your Top Artists" section: horizontal scrollable row of `<ArtistCard />` per artist
- Style profile card: paragraph showing `data.style_profile`
- "Your SoundFit" section: `<OutfitResults recommendations={data.recommendations} />`

```ts
interface DashboardProps {
  accessToken: string
  clearToken: () => void
}
```

#### `frontend/src/components/ArtistCard.tsx`
Shows artist image (first in array, fallback placeholder div if no image), name, and first genre. Links to Spotify profile via `external_urls.spotify`.

```ts
import type { Artist } from '../types'
interface ArtistCardProps { artist: Artist }
```

#### `frontend/src/components/OutfitResults.tsx`
For each `OutfitRecommendation`, render a card with: `aesthetic` badge, `title` heading, `description` paragraph, and a grid of outfit items. Each item shows its name, description, and `search_links` as pill buttons that open in a new tab.

```ts
import type { OutfitRecommendation } from '../types'
interface OutfitResultsProps { recommendations: OutfitRecommendation[] }
```

#### `frontend/src/components/LoadingScreen.tsx`
Full-page centered layout with CSS animated spinner and `message` prop as subtext.

```ts
interface LoadingScreenProps { message: string }
```

#### `frontend/src/index.css`
```css
:root {
  --color-bg: #0a0a0a;
  --color-surface: #141414;
  --color-surface-raised: #1e1e1e;
  --color-border: #2a2a2a;
  --color-text-primary: #f5f5f5;
  --color-text-secondary: #a0a0a0;
  --color-accent: #1DB954;
  --color-accent-hover: #1ed760;
  --font-sans: 'Inter', system-ui, sans-serif;
  --radius-md: 8px;
  --radius-lg: 14px;
}

* { box-sizing: border-box; margin: 0; padding: 0; }

body {
  background: var(--color-bg);
  color: var(--color-text-primary);
  font-family: var(--font-sans);
  min-height: 100vh;
}

a { color: inherit; text-decoration: none; }

button { cursor: pointer; border: none; font-family: inherit; }
```

All component styles go in this file using BEM class names (`.artist-card`, `.artist-card__image`, `.outfit-card__badge`, etc.). No inline style objects except for truly dynamic values like background image URLs.

---

### Backend Files

#### `backend/requirements.txt`
```
fastapi
uvicorn[standard]
httpx
python-dotenv
anthropic
beautifulsoup4
pydantic-settings
```

#### `backend/routers/__init__.py` — empty file
#### `backend/services/__init__.py` — empty file

#### `backend/config.py`
```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    spotify_client_id: str
    spotify_client_secret: str
    spotify_redirect_uri: str
    genius_access_token: str
    anthropic_api_key: str

    class Config:
        env_file = ".env"

settings = Settings()
```

#### `backend/models.py`
```python
from pydantic import BaseModel
from typing import List

class TokenExchangeRequest(BaseModel):
    code: str
    code_verifier: str

class TokenResponse(BaseModel):
    access_token: str

class SearchLink(BaseModel):
    label: str
    url: str

class OutfitItem(BaseModel):
    name: str
    description: str
    search_links: List[SearchLink]

class OutfitRecommendation(BaseModel):
    title: str
    description: str
    aesthetic: str
    items: List[OutfitItem]

class RecommendationResponse(BaseModel):
    artists: List[dict]
    style_profile: str
    recommendations: List[OutfitRecommendation]
```

#### `backend/main.py`
```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import spotify, outfits

app = FastAPI(title="SoundFit API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(spotify.router, prefix="/auth")
app.include_router(outfits.router, prefix="/outfits")

@app.get("/health")
def health():
    return {"status": "ok"}
```

#### `backend/routers/spotify.py`
```python
import httpx
from fastapi import APIRouter, HTTPException
from models import TokenExchangeRequest, TokenResponse
from config import settings

router = APIRouter()

@router.post("/callback", response_model=TokenResponse)
async def spotify_callback(body: TokenExchangeRequest):
    async with httpx.AsyncClient() as client:
        res = await client.post(
            "https://accounts.spotify.com/api/token",
            data={
                "grant_type": "authorization_code",
                "code": body.code,
                "redirect_uri": settings.spotify_redirect_uri,
                "client_id": settings.spotify_client_id,
                "code_verifier": body.code_verifier,
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
    if res.status_code != 200:
        raise HTTPException(status_code=400, detail="Spotify token exchange failed")
    return TokenResponse(access_token=res.json()["access_token"])
```

#### `backend/routers/outfits.py`
```python
from fastapi import APIRouter, HTTPException, Request
from services import spotify_client, genius_client, llm_service
from models import RecommendationResponse

router = APIRouter()

@router.post("/recommend", response_model=RecommendationResponse)
async def recommend(request: Request):
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing token")
    token = auth.split(" ", 1)[1]

    artists = await spotify_client.get_top_artists(token)

    lyrics_data = []
    for artist in artists:
        tracks = await spotify_client.get_top_tracks(token, artist["id"])
        for track in tracks[:3]:
            lyrics = await genius_client.get_lyrics(artist["name"], track)
            lyrics_data.append({
                "artist": artist["name"],
                "track": track,
                "lyrics": lyrics,
            })

    result = await llm_service.get_outfit_recommendations(artists, lyrics_data)
    return result
```

#### `backend/services/spotify_client.py`
```python
import httpx
from fastapi import HTTPException

SPOTIFY_BASE = "https://api.spotify.com/v1"

async def get_top_artists(token: str) -> list[dict]:
    async with httpx.AsyncClient() as client:
        res = await client.get(
            f"{SPOTIFY_BASE}/me/top/artists",
            params={"limit": 5, "time_range": "medium_term"},
            headers={"Authorization": f"Bearer {token}"},
        )
    if res.status_code != 200:
        raise HTTPException(status_code=400, detail="Failed to fetch top artists")
    return res.json()["items"]

async def get_top_tracks(token: str, artist_id: str) -> list[str]:
    async with httpx.AsyncClient() as client:
        res = await client.get(
            f"{SPOTIFY_BASE}/artists/{artist_id}/top-tracks",
            params={"market": "US"},
            headers={"Authorization": f"Bearer {token}"},
        )
    if res.status_code != 200:
        return []
    tracks = res.json().get("tracks", [])
    return [t["name"] for t in tracks[:3]]
```

#### `backend/services/genius_client.py`
```python
import httpx
from bs4 import BeautifulSoup
from config import settings

GENIUS_BASE = "https://api.genius.com"

async def search_song(artist: str, track: str) -> str | None:
    async with httpx.AsyncClient() as client:
        res = await client.get(
            f"{GENIUS_BASE}/search",
            params={"q": f"{artist} {track}"},
            headers={"Authorization": f"Bearer {settings.genius_access_token}"},
        )
    if res.status_code != 200:
        return None
    hits = res.json().get("response", {}).get("hits", [])
    for hit in hits:
        result = hit.get("result", {})
        primary_artist = result.get("primary_artist", {}).get("name", "")
        if artist.lower() in primary_artist.lower() or primary_artist.lower() in artist.lower():
            return result.get("url")
    return None

async def get_lyrics(artist: str, track: str) -> str:
    try:
        url = await search_song(artist, track)
        if not url:
            return ""
        async with httpx.AsyncClient(follow_redirects=True) as client:
            res = await client.get(url, headers={"User-Agent": "Mozilla/5.0"})
        soup = BeautifulSoup(res.text, "html.parser")
        containers = soup.find_all("div", attrs={"data-lyrics-container": "true"})
        lyrics = "\n".join(c.get_text(separator="\n") for c in containers)
        return lyrics.strip()[:3000]
    except Exception:
        return ""
```

#### `backend/services/llm_service.py`
```python
import json
import anthropic
from models import RecommendationResponse, OutfitRecommendation, OutfitItem, SearchLink
from config import settings

SYSTEM_PROMPT = """You are SoundFit, a fashion stylist AI. You analyze song lyrics to identify clothing references, color palettes, textures, moods, and aesthetic cues. From these signals you build outfit recommendations that reflect the user's music taste. You always respond with valid JSON only — no explanation, no markdown, no prose outside the JSON structure."""

def _build_prompt(artists: list[dict], lyrics_data: list[dict]) -> str:
    artist_names = ", ".join(a["name"] for a in artists)
    lyrics_block = ""
    for entry in lyrics_data:
        if entry["lyrics"]:
            lyrics_block += f"\n--- {entry['artist']} - {entry['track']} ---\n{entry['lyrics']}\n"

    return f"""Here are the top artists and song lyrics from a user's Spotify listening history.

Artists: {artist_names}

Lyrics samples:
{lyrics_block}

Based on these lyrics, identify the dominant aesthetics, clothing references, color palettes, and style vibes. Then generate exactly 3 outfit recommendations using this JSON schema:

{{
  "style_profile": "2-3 sentence description of the user's overall aesthetic",
  "recommendations": [
    {{
      "title": "Outfit name",
      "description": "2-3 sentence description of the outfit and why it fits the music",
      "aesthetic": "One word or short phrase e.g. dark academia, streetwear, soft grunge",
      "items": [
        {{
          "name": "Item name e.g. Oversized black hoodie",
          "description": "One sentence describing the specific item",
          "search_links": [
            {{ "label": "ASOS", "url": "https://www.asos.com/search/?q=oversized+black+hoodie" }},
            {{ "label": "Depop", "url": "https://www.depop.com/search/?q=oversized+black+hoodie" }},
            {{ "label": "Amazon", "url": "https://www.amazon.com/s?k=oversized+black+hoodie" }}
          ]
        }}
      ]
    }}
  ]
}}

Each outfit must have 4-5 items. For search_links, generate real search URLs for ASOS, Depop, and Amazon using the item name URL-encoded as the query. Return only the JSON object."""

async def get_outfit_recommendations(
    artists: list[dict],
    lyrics_data: list[dict],
) -> RecommendationResponse:
    client = anthropic.Anthropic(api_key=settings.anthropic_api_key)

    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=2000,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": _build_prompt(artists, lyrics_data)}],
    )

    raw = message.content[0].text.strip()
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[1].rsplit("```", 1)[0].strip()

    data = json.loads(raw)

    recommendations = [
        OutfitRecommendation(
            title=r["title"],
            description=r["description"],
            aesthetic=r["aesthetic"],
            items=[
                OutfitItem(
                    name=item["name"],
                    description=item["description"],
                    search_links=[
                        SearchLink(label=link["label"], url=link["url"])
                        for link in item["search_links"]
                    ],
                )
                for item in r["items"]
            ],
        )
        for r in data["recommendations"]
    ]

    return RecommendationResponse(
        artists=artists,
        style_profile=data["style_profile"],
        recommendations=recommendations,
    )
```

---

### Implementation Notes for Claude Code

- Implement every file completely — no `// TODO`, no `pass`, no placeholder stubs
- All TypeScript must compile cleanly with `tsc --noEmit` — no type errors, no unused imports
- Use `async/await` throughout — no `.then()` chains
- Handle loading, error, and empty states in every page component
- The Dashboard must not flash an empty state before data loads — use a loading gate
- Keep all styles in `index.css` using BEM class names and the CSS variables defined above
- The app should look clean and polished with the dark theme — generous spacing, subtle borders using `var(--color-border)`
- After creating all files, run `npm install` in `frontend/` and `pip install -r requirements.txt` in `backend/`
- Do not start the dev servers — just scaffold and install

---

## 9. Before You Run Claude Code

You need accounts and keys from three services:

**Spotify Developer**
1. Go to [developer.spotify.com/dashboard](https://developer.spotify.com/dashboard)
2. Create an app
3. Copy your **Client ID** (you don't need the client secret for PKCE, but grab it anyway for the backend `.env`)
4. Under "Redirect URIs", add: `http://localhost:5173/callback`
5. Save

**Genius API**
1. Go to [genius.com/api-clients](https://genius.com/api-clients)
2. Create an API client
3. Copy your **Client Access Token**

**Anthropic**
1. Go to [console.anthropic.com](https://console.anthropic.com)
2. Generate an **API key**

---

## 10. Running the App

```bash
# Terminal 1 — Frontend
cd soundfit/frontend
npm install
cp .env.example .env
# Fill in your VITE_SPOTIFY_CLIENT_ID
npm run dev

# Terminal 2 — Backend
cd soundfit/backend
pip install -r requirements.txt
cp .env.example .env
# Fill in all five keys
uvicorn main:app --reload
```

Then open [http://localhost:5173](http://localhost:5173).

> **Note on Genius scraping:** Genius occasionally changes their HTML structure, which can break the `data-lyrics-container` selector. If lyrics are consistently empty, inspect the Genius page source and update the selector in `genius_client.py`. The app handles missing lyrics gracefully — it just skips those tracks.
