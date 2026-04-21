import httpx
from fastapi import APIRouter, HTTPException
from models import TokenExchangeRequest, TokenExchangeResponse
from config import settings

router = APIRouter()

SPOTIFY_TOKEN_URL = "https://accounts.spotify.com/api/token"


@router.post("/callback", response_model=TokenExchangeResponse)
async def exchange_token(body: TokenExchangeRequest):
    """Exchange Spotify authorization code + PKCE verifier for an access token."""
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
        raise HTTPException(
            status_code=400,
            detail=f"Spotify token exchange failed: {response.text}",
        )

    return response.json()

