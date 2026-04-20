import httpx

LYRICS_API_BASE = "https://api.lyrics.ovh/v1"


async def get_lyrics(artist: str, title: str) -> str | None:
    url = f"{LYRICS_API_BASE}/{artist}/{title}"
    try:
        async with httpx.AsyncClient(timeout=8) as client:
            response = await client.get(url)
        if response.status_code != 200:
            print(f"[SoundFit] Lyrics not found for '{title}' by {artist} (status {response.status_code})")
            return None
        lyrics = response.json().get("lyrics")
        print(f"[SoundFit] Lyrics fetched for '{title}' by {artist}: {lyrics[:80] if lyrics else 'empty'}...")
        return lyrics
    except Exception as e:
        print(f"[SoundFit] Lyrics fetch error for '{title}' by {artist}: {e}")
        return None
