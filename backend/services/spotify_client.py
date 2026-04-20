import asyncio
import httpx
from models import Artist, Track
from services.lyrics_client import get_lyrics

SPOTIFY_API_BASE = "https://api.spotify.com/v1"


async def get_top_artists(access_token: str, limit: int = 5) -> list[Artist]:
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{SPOTIFY_API_BASE}/me/top/artists",
            params={"limit": limit, "time_range": "short_term"},
            headers={"Authorization": f"Bearer {access_token}"},
        )
    response.raise_for_status()
    items = response.json()["items"]

    return [
        Artist(
            id=a["id"],
            name=a["name"],
            genres=a.get("genres", []),
            image_url=a["images"][0]["url"] if a.get("images") else None,
        )
        for a in items
    ]


async def get_top_tracks(access_token: str, limit: int = 5) -> list[Track]:
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{SPOTIFY_API_BASE}/me/top/tracks",
            params={"limit": limit, "time_range": "short_term"},
            headers={"Authorization": f"Bearer {access_token}"},
        )
    response.raise_for_status()
    items = response.json()["items"]

    tracks = [
        Track(id=t["id"], name=t["name"], artist_name=t["artists"][0]["name"])
        for t in items
    ]

    # Fetch lyrics for all tracks concurrently
    lyrics_results = await asyncio.gather(
        *[get_lyrics(t.artist_name, t.name) for t in tracks]
    )

    print("[SoundFit] Top 5 tracks with lyrics (last 4 weeks):")
    for i, (track, lyrics) in enumerate(zip(tracks, lyrics_results), 1):
        print(f"  {i}. {track.name} — {track.artist_name}")
        print(f"     Lyrics: {lyrics[:120] if lyrics else 'Not found'}")

    return tracks
