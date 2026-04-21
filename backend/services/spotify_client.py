import httpx
from models import Artist, Track

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

    tracks = []
    for t in items:
        all_artists = t.get("artists", [])
        primary = all_artists[0]["name"] if all_artists else "Unknown"
        featured = [a["name"] for a in all_artists[1:]]

        # Use the album art as a proxy artist image
        album_images = t.get("album", {}).get("images", [])
        artist_image_url = album_images[0]["url"] if album_images else None

        tracks.append(Track(
            id=t["id"],
            name=t["name"],
            artist_name=primary,
            featured_artists=featured,
            artist_image_url=artist_image_url,
        ))

    return tracks
