import asyncio
import traceback
from fastapi import APIRouter, HTTPException, Header
from models import TopDataResponse, TrackWithLyrics, RecommendationsResponse
from services.spotify_client import get_top_artists, get_top_tracks
from services.lyrics_client import get_lyrics
from services.llm_service import get_track_recommendation, get_taste_summary

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
        traceback.print_exc()
        raise HTTPException(status_code=502, detail=f"Spotify API error: {str(e)}")

    return TopDataResponse(top_artists=top_artists, top_tracks=top_tracks)


@router.get("/recommend", response_model=RecommendationsResponse)
async def get_recommendations(authorization: str = Header(...)):
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization header")

    access_token = authorization.removeprefix("Bearer ")

    try:
        tracks = await get_top_tracks(access_token, limit=5)
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=502, detail=f"Spotify API error: {str(e)}")

    lyrics_results = await asyncio.gather(
        *[get_lyrics(t.artist_name, t.name) for t in tracks]
    )

    tracks_with_lyrics = [
        TrackWithLyrics(
            name=t.name,
            artist_name=t.artist_name,
            featured_artists=t.featured_artists,
            artist_image_url=t.artist_image_url,
            lyrics=lyrics,
        )
        for t, lyrics in zip(tracks, lyrics_results)
    ]

    try:
        taste_summary, *rec_results = await asyncio.gather(
            get_taste_summary(tracks_with_lyrics),
            *[get_track_recommendation(t) for t in tracks_with_lyrics],
        )
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=502, detail=f"LLM error: {str(e)}")

    return RecommendationsResponse(
        taste_summary=taste_summary,
        recommendations=list(rec_results),
    )
