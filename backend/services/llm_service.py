import json
from openai import AsyncOpenAI
from config import settings
from models import TrackWithLyrics, OutfitRecommendation, Outfit, OutfitItem

_client = AsyncOpenAI(api_key=settings.openai_api_key)

SYSTEM_PROMPT = """You are a fashion stylist who derives outfit recommendations from music.

When given a song's name, artist, and lyrics, analyze:
1. VIBE & MOOD — the emotional tone (dark, euphoric, tender, aggressive, dreamy, etc.)
2. CLOTHING CUES — any explicit mentions of garments, brands, or accessories in the lyrics
3. CULTURAL REFERENCES — scenes, subcultures, eras, or aesthetics referenced
4. COLOR PALETTE — colors implied by the mood, imagery, or explicit mentions
5. LIFESTYLE SIGNALS — settings described (streets, clubs, nature, luxury, etc.)

Return a JSON object with this exact structure:
{
  "style_profile": "2-3 sentence summary of the aesthetic derived from this song",
  "outfits": [
    {
      "name": "Short outfit name",
      "vibe": "One-line vibe description",
      "items": [
        {
          "name": "Item name (e.g. Oversized black leather jacket)",
          "description": "Why this item fits the song's aesthetic",
          "search_links": {
            "asos": "https://www.asos.com/search/?q=oversized+black+leather+jacket",
            "depop": "https://www.depop.com/search/?q=oversized+black+leather+jacket",
            "amazon": "https://www.amazon.com/s?k=oversized+black+leather+jacket"
          }
        }
      ]
    }
  ]
}

Rules:
- Return exactly 2 outfits per song
- Each outfit has exactly 4 items
- Search link queries must be URL-encoded (spaces as +)
- Return ONLY the JSON object, no markdown, no explanation
"""


def _build_search_links(item_name: str) -> dict[str, str]:
    query = item_name.lower().replace(" ", "+")
    return {
        "asos": f"https://www.asos.com/search/?q={query}",
        "depop": f"https://www.depop.com/search/?q={query}",
        "amazon": f"https://www.amazon.com/s?k={query}",
    }


async def get_outfit_recommendations(track: TrackWithLyrics) -> OutfitRecommendation:
    lyrics_section = (
        f"Lyrics:\n{track.lyrics[:2000]}"
        if track.lyrics
        else "Lyrics: Not available — base recommendations on the artist and song title alone."
    )

    user_message = f"Song: \"{track.name}\" by {track.artist_name}\n\n{lyrics_section}"

    print(f"[SoundFit] Generating outfit recs for '{track.name}' by {track.artist_name}...")

    response = await _client.chat.completions.create(
        model="gpt-4o",
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
        ],
        temperature=0.8,
    )

    raw = response.choices[0].message.content
    data = json.loads(raw)

    outfits = [
        Outfit(
            name=o["name"],
            vibe=o["vibe"],
            items=[
                OutfitItem(
                    name=item["name"],
                    description=item["description"],
                    search_links=_build_search_links(item["name"]),
                )
                for item in o["items"]
            ],
        )
        for o in data["outfits"]
    ]

    print(f"[SoundFit] Recs ready for '{track.name}': {[o.name for o in outfits]}")

    return OutfitRecommendation(
        track_name=track.name,
        artist_name=track.artist_name,
        style_profile=data["style_profile"],
        outfits=outfits,
    )
