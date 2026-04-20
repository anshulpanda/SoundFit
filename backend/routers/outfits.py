import asyncio
import traceback
from fastapi import APIRouter, HTTPException, Header
from models import TopDataResponse, TrackWithLyrics, RecommendationsResponse
from services.spotify_client import get_top_artists, get_top_tracks
from services.lyrics_client import get_lyrics
from services.llm_service import get_outfit_recommendations

router = APIRouter()


@router.get("/top-data", response_model=TopDataResponse)
async def get_top_data(authorization: str = Header(...)):
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization header")

    access_token = authorization.removeprefix("Bearer ")

    try:
        top_artists, top_tracks = await asyncio.gather(
            get_top_artists(access_token, limit=5),
            get_top_tracks(access_token, limit=5),
        )
    except Exception as e:
        print("[SoundFit] Spotify API error:")
        traceback.print_exc()
        raise HTTPException(status_code=502, detail=f"Spotify API error: {str(e)}")

    return TopDataResponse(top_artists=top_artists, top_tracks=top_tracks)


@router.get("/recommend", response_model=RecommendationsResponse)
async def get_recommendations(authorization: str = Header(...)):
    """
    Full pipeline: fetch top 5 tracks → get lyrics → generate outfit recs via LLM.
    """
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization header")

    access_token = authorization.removeprefix("Bearer ")

    # 1. Fetch top tracks from Spotify
    try:
        tracks = await get_top_tracks(access_token, limit=5)
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=502, detail=f"Spotify API error: {str(e)}")

    # 2. Fetch lyrics for all tracks concurrently
    lyrics_results = await asyncio.gather(
        *[get_lyrics(t.artist_name, t.name) for t in tracks]
    )

    tracks_with_lyrics = [
        TrackWithLyrics(name=t.name, artist_name=t.artist_name, lyrics=lyrics)
        for t, lyrics in zip(tracks, lyrics_results)
    ]

    # 3. Generate outfit recommendations for each track concurrently
    try:
        recommendations = await asyncio.gather(
            *[get_outfit_recommendations(t) for t in tracks_with_lyrics]
        )
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=502, detail=f"LLM error: {str(e)}")

    return RecommendationsResponse(recommendations=list(recommendations))
