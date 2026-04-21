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
    featured_artists: list[str] = []
    artist_image_url: Optional[str] = None


class TopDataResponse(BaseModel):
    top_artists: list[Artist]
    top_tracks: list[Track]


class TrackWithLyrics(BaseModel):
    name: str
    artist_name: str
    featured_artists: list[str] = []
    artist_image_url: Optional[str] = None
    lyrics: Optional[str] = None


class Product(BaseModel):
    title: str
    link: str
    image_url: Optional[str] = None
    price: Optional[str] = None
    source: Optional[str] = None


class RankedQuery(BaseModel):
    query: str
    products: list[Product]


class TrackRecommendation(BaseModel):
    track_name: str
    artist_name: str
    featured_artists: list[str] = []
    artist_image_url: Optional[str] = None
    style_profile: str
    queries: list[RankedQuery]


class RecommendationsResponse(BaseModel):
    taste_summary: str
    recommendations: list[TrackRecommendation]
