# SoundFit Implementation Plan

## Overview

Full-stack implementation of SoundFit using **Next.js 14 (App Router)** for the frontend and **FastAPI** for the backend. Design follows `DESIGN.md` — Spotify-inspired dark theme (`#121212` base, `#1ed760` accent, pill geometry, heavy shadows).

---

## Prerequisites

### API Keys & Registrations

1. **Spotify Developer App**
   - Go to https://developer.spotify.com/dashboard → Create App
   - Set Redirect URI: `http://localhost:3000/callback`
   - Note your **Client ID** and **Client Secret**
   - Required scopes: `user-top-read`

2. **Anthropic API Key** — https://console.anthropic.com

3. **Genius API Token** (optional — lyrics enrichment) — https://genius.com/api-clients

---

## Step 1 — Scaffold the Project

### 1.1 Backend (FastAPI)

```bash
mkdir -p soundfit/backend/routers soundfit/backend/services
cd soundfit/backend
python -m venv venv && source venv/bin/activate
pip install fastapi uvicorn[standard] httpx python-dotenv anthropic beautifulsoup4 pydantic-settings
pip freeze > requirements.txt
```

Create `backend/.env`:
```env
SPOTIFY_CLIENT_ID=your_spotify_client_id
SPOTIFY_CLIENT_SECRET=your_spotify_client_secret
SPOTIFY_REDIRECT_URI=http://localhost:3000/callback
GENIUS_ACCESS_TOKEN=your_genius_access_token
ANTHROPIC_API_KEY=your_anthropic_api_key
```

### 1.2 Frontend (Next.js 14)

```bash
cd soundfit
npx create-next-app@latest frontend --typescript --eslint --tailwind no --app --src-dir --import-alias "@/*"
cd frontend
```

Create `frontend/.env.local`:
```env
NEXT_PUBLIC_SPOTIFY_CLIENT_ID=your_spotify_client_id
NEXT_PUBLIC_REDIRECT_URI=http://localhost:3000/callback
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

---

## Step 2 — Backend: Config & Models

### `backend/config.py`

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    spotify_client_id: str
    spotify_client_secret: str
    spotify_redirect_uri: str
    genius_access_token: str = ""
    anthropic_api_key: str

    class Config:
        env_file = ".env"

settings = Settings()
```

### `backend/models.py`

```python
from pydantic import BaseModel
from typing import Optional

class TokenExchangeRequest(BaseModel):
    code: str
    code_verifier: str

class TokenExchangeResponse(BaseModel):
    access_token: str
    token_type: str
    expires_in: int
    refresh_token: Optional[str] = None
    scope: str

class Artist(BaseModel):
    id: str
    name: str
    genres: list[str]
    image_url: Optional[str] = None

class Track(BaseModel):
    id: str
    name: str
    artist_name: str

class TopDataResponse(BaseModel):
    top_artists: list[Artist]
    top_tracks: list[Track]
```

### `backend/main.py`

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import spotify, outfits

app = FastAPI(title="SoundFit API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(spotify.router, prefix="/auth", tags=["auth"])
app.include_router(outfits.router, prefix="/outfits", tags=["outfits"])

@app.get("/health")
async def health():
    return {"status": "ok"}
```

---

## Step 3 — Backend: Spotify OAuth Token Exchange

### `backend/routers/spotify.py`

```python
import httpx
from fastapi import APIRouter, HTTPException
from models import TokenExchangeRequest, TokenExchangeResponse
from config import settings

router = APIRouter()
SPOTIFY_TOKEN_URL = "https://accounts.spotify.com/api/token"

@router.post("/callback", response_model=TokenExchangeResponse)
async def exchange_token(body: TokenExchangeRequest):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            SPOTIFY_TOKEN_URL,
            data={
                "grant_type": "authorization_code",
                "code": body.code,
                "redirect_uri": settings.spotify_redirect_uri,
                "client_id": settings.spotify_client_id,
                "code_verifier": body.code_verifier,
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
    if response.status_code != 200:
        raise HTTPException(status_code=400, detail=f"Token exchange failed: {response.text}")
    return response.json()
```

---

## Step 4 — Backend: Fetch Top Artists & Tracks

### `backend/services/spotify_client.py`

```python
import httpx
from models import Artist, Track

SPOTIFY_API_BASE = "https://api.spotify.com/v1"

async def get_top_artists(access_token: str, limit: int = 5) -> list[Artist]:
    async with httpx.AsyncClient() as client:
        r = await client.get(
            f"{SPOTIFY_API_BASE}/me/top/artists",
            params={"limit": limit, "time_range": "medium_term"},
            headers={"Authorization": f"Bearer {access_token}"},
        )
    r.raise_for_status()
    return [
        Artist(id=a["id"], name=a["name"], genres=a["genres"],
               image_url=a["images"][0]["url"] if a["images"] else None)
        for a in r.json()["items"]
    ]

async def get_top_tracks(access_token: str, limit: int = 5) -> list[Track]:
    async with httpx.AsyncClient() as client:
        r = await client.get(
            f"{SPOTIFY_API_BASE}/me/top/tracks",
            params={"limit": limit, "time_range": "medium_term"},
            headers={"Authorization": f"Bearer {access_token}"},
        )
    r.raise_for_status()
    return [
        Track(id=t["id"], name=t["name"], artist_name=t["artists"][0]["name"])
        for t in r.json()["items"]
    ]
```

### `backend/routers/outfits.py`

```python
import asyncio
from fastapi import APIRouter, HTTPException, Header
from models import TopDataResponse
from services.spotify_client import get_top_artists, get_top_tracks

router = APIRouter()

@router.get("/top-data", response_model=TopDataResponse)
async def get_top_data(authorization: str = Header(...)):
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization header")
    token = authorization.removeprefix("Bearer ")
    try:
        artists, tracks = await asyncio.gather(
            get_top_artists(token, limit=5),
            get_top_tracks(token, limit=5),
        )
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Spotify API error: {str(e)}")
    return TopDataResponse(top_artists=artists, top_tracks=tracks)
```

---

## Step 5 — Frontend: Design System (globals.css)

Create `frontend/src/app/globals.css` with CSS custom properties from DESIGN.md:
- Background: `#121212` base, `#181818`/`#1f1f1f` surfaces
- Accent: `#1ed760` (Spotify Green)
- Text: `#ffffff` primary, `#b3b3b3` secondary
- Fonts: SpotifyMixUI with Helvetica Neue fallback
- Shadows: heavy `rgba(0,0,0,0.5) 0px 8px 24px` for dialogs, medium for cards
- Border radius scale: 6px cards, 500px/9999px pills, 50% circles

---

## Step 6 — Frontend: TypeScript Types

### `frontend/src/types/index.ts`

```typescript
export interface Artist {
  id: string;
  name: string;
  genres: string[];
  image_url: string | null;
}

export interface Track {
  id: string;
  name: string;
  artist_name: string;
}

export interface TopData {
  top_artists: Artist[];
  top_tracks: Track[];
}

export interface SpotifyTokenResponse {
  access_token: string;
  token_type: string;
  expires_in: int;
  refresh_token?: string;
  scope: string;
}
```

---

## Step 7 — Frontend: PKCE Auth Hook

### `frontend/src/hooks/useAuth.ts` (client-only)

- `generateRandomString(64)` using `crypto.getRandomValues`
- `sha256` + `base64UrlEncode` using `crypto.subtle.digest`
- Stores `code_verifier` in `sessionStorage`
- Stores `access_token` in `localStorage`
- `login()` → redirects to `https://accounts.spotify.com/authorize`
- `storeToken(token)` → saves to localStorage + sets state
- `logout()` → clears localStorage

---

## Step 8 — Frontend: API Service

### `frontend/src/services/api.ts`

```typescript
const BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL;

export async function fetchTopData(accessToken: string): Promise<TopData> {
  const res = await fetch(`${BASE_URL}/outfits/top-data`, {
    headers: { Authorization: `Bearer ${accessToken}` },
  });
  if (!res.ok) throw new Error("Failed to fetch top data");
  return res.json();
}
```

---

## Step 9 — Frontend: Pages (App Router)

### Route Structure
```
src/app/
├── layout.tsx          Root layout with metadata + font CSS vars
├── page.tsx            Login page — "Connect with Spotify" CTA
├── globals.css         Full design system
├── callback/
│   └── page.tsx        Token exchange → redirects to /dashboard
└── dashboard/
    └── page.tsx        Top 5 artists grid + top 5 tracks list
```

### `src/app/page.tsx` (Login)
- Full-screen dark (`#121212`) centered layout
- SoundFit logo/title in white SpotifyMixUI
- Tagline in `#b3b3b3`
- "Connect with Spotify" → large pill button, `#1ed760` background, `#000000` text
- Uppercase label, `letter-spacing: 2px`

### `src/app/callback/page.tsx`
- `"use client"` directive
- `useEffect` reads `?code` from `useSearchParams()`
- Reads `pkce_code_verifier` from `sessionStorage`
- `POST /auth/callback` → stores token → `router.push("/dashboard")`
- Shows "Connecting to Spotify..." loading state while processing

### `src/app/dashboard/page.tsx`
- `"use client"` directive
- Reads `access_token` from `localStorage` on mount
- `GET /outfits/top-data` → renders results
- **Top 5 Artists**: horizontal scrollable grid of dark cards (`#181818`, 6px radius)
  - Artist image (circle, 80px), name bold white, genres in `#b3b3b3`
  - Card hover: background lightens to `#252525`, shadow `rgba(0,0,0,0.3) 0px 8px 8px`
- **Top 5 Tracks**: numbered list
  - Track name bold white, artist in `#b3b3b3`
  - Row hover: `#181818` background
- Logout button: outlined pill (`1px solid #4d4d4d`, transparent bg, white text)

---

## Step 10 — Running the Application

### Start Backend
```bash
cd backend && source venv/bin/activate
uvicorn main:app --reload --port 8000
```

### Start Frontend
```bash
cd frontend && npm run dev
# Runs at http://localhost:3000
```

---

## Complete Data Flow

```
1. User visits http://localhost:3000
   └─ Login page (dark, Spotify-styled CTA)

2. Click "Connect with Spotify"
   ├─ PKCE: generate code_verifier + code_challenge
   ├─ Save code_verifier to sessionStorage
   └─ Redirect → https://accounts.spotify.com/authorize?...

3. Spotify OAuth consent → redirects to http://localhost:3000/callback?code=...

4. /callback page
   ├─ Read code from URL (useSearchParams)
   ├─ Read code_verifier from sessionStorage
   └─ POST http://localhost:8000/auth/callback { code, code_verifier }
         ↓ FastAPI exchanges with Spotify → returns access_token
   ├─ Save access_token to localStorage
   └─ router.push("/dashboard")

5. /dashboard page
   └─ GET http://localhost:8000/outfits/top-data (Bearer token)
         ↓ FastAPI: asyncio.gather(top_artists, top_tracks) from Spotify
   └─ Render top 5 artists + top 5 tracks with Spotify dark design
```

---

## File Creation Order

**Backend** (already scaffolded):
1. `backend/config.py`
2. `backend/models.py`
3. `backend/services/__init__.py`
4. `backend/services/spotify_client.py`
5. `backend/routers/__init__.py`
6. `backend/routers/spotify.py`
7. `backend/routers/outfits.py`
8. `backend/main.py`

**Frontend** (Next.js):
9. `frontend/package.json`
10. `frontend/next.config.ts`
11. `frontend/tsconfig.json`
12. `frontend/src/app/globals.css`
13. `frontend/src/app/layout.tsx`
14. `frontend/src/types/index.ts`
15. `frontend/src/hooks/useAuth.ts`
16. `frontend/src/services/api.ts`
17. `frontend/src/app/page.tsx`
18. `frontend/src/app/callback/page.tsx`
19. `frontend/src/app/dashboard/page.tsx`
