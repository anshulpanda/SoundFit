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


class TrackWithLyrics(BaseModel):
    name: str
    artist_name: str
    lyrics: Optional[str] = None


class OutfitItem(BaseModel):
    name: str
    description: str
    search_links: dict[str, str]


class Outfit(BaseModel):
    name: str
    vibe: str
    items: list[OutfitItem]


class OutfitRecommendation(BaseModel):
    track_name: str
    artist_name: str
    style_profile: str
    outfits: list[Outfit]


class RecommendationsResponse(BaseModel):
    recommendations: list[OutfitRecommendation]
