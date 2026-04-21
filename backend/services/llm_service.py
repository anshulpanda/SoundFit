import json
import asyncio
from openai import AsyncOpenAI
from config import settings
from models import TrackWithLyrics, TrackRecommendation, RankedQuery, Product
from services.serper_client import search_products

_client = AsyncOpenAI(api_key=settings.openai_api_key)

QUERY_SYSTEM_PROMPT = """You are a fashion stylist who reads song lyrics and derives shoppable outfit searches.

Given a song's name, artist, and lyrics, analyze:
- VIBE & MOOD: emotional tone (dark, euphoric, tender, aggressive, dreamy, nostalgic, etc.)
- CLOTHING CUES: any explicit garment, brand, or accessory mentions
- CULTURAL REFERENCES: subcultures, eras, scenes (e.g. Y2K, grunge, hip-hop, indie, goth)
- COLOR PALETTE: colors implied by mood or explicit mentions
- LIFESTYLE SIGNALS: settings described (streets, clubs, nature, luxury, suburbia)

Return a JSON object with this structure:
{
  "style_profile": "2-3 sentences describing the aesthetic this song evokes",
  "queries": [
    "specific shoppable fashion search query 1",
    "specific shoppable fashion search query 2",
    "specific shoppable fashion search query 3"
  ]
}

Rules for queries:
- Each query must be a specific, Google-shoppable phrase (e.g. "oversized vintage denim jacket 90s", "black satin slip dress gothic")
- Queries should cover different aspects of the outfit (e.g. outerwear, bottoms, footwear, accessory)
- 2-3 queries total
- Return ONLY the JSON object"""

RANKING_SYSTEM_PROMPT = """You are a fashion stylist ranking shopping results by relevance to a style query.

Given a search query and a list of products, return the indices of the top 5 most relevant products in order from most to least relevant.

Consider: how well the product matches the aesthetic, style, and vibe of the query.

Return ONLY a JSON array of integer indices (0-based), e.g. [2, 0, 4, 1, 3]"""


async def _generate_queries(track: TrackWithLyrics) -> tuple[str, list[str]]:
    lyrics_section = (
        f"Lyrics:\n{track.lyrics[:2000]}"
        if track.lyrics
        else "Lyrics: Not available — base recommendations on the artist and song title alone."
    )
    user_message = f"Song: \"{track.name}\" by {track.artist_name}\n\n{lyrics_section}"

    print(f"[SoundFit] Generating queries for '{track.name}'...")

    response = await _client.chat.completions.create(
        model="gpt-4o",
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": QUERY_SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
        ],
        temperature=0.8,
    )

    data = json.loads(response.choices[0].message.content)
    style_profile = data["style_profile"]
    queries = data["queries"][:3]

    print(f"[SoundFit] Queries for '{track.name}': {queries}")
    return style_profile, queries


async def _rank_products(query: str, products: list[Product]) -> list[Product]:
    if not products:
        return []

    product_list = "\n".join(
        f"{i}. {p.title} ({p.source or 'unknown'}) — {p.price or 'no price'}"
        for i, p in enumerate(products)
    )

    response = await _client.chat.completions.create(
        model="gpt-4o-mini",
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": RANKING_SYSTEM_PROMPT},
            {"role": "user", "content": f"Query: {query}\n\nProducts:\n{product_list}\n\nReturn JSON: {{\"ranked\": [indices]}}"},
        ],
        temperature=0.2,
    )

    data = json.loads(response.choices[0].message.content)
    indices = data.get("ranked", list(range(min(5, len(products)))))

    ranked = []
    seen = set()
    for i in indices:
        if isinstance(i, int) and 0 <= i < len(products) and i not in seen:
            ranked.append(products[i])
            seen.add(i)

    # Fill remaining slots if ranking returned fewer than 5
    for i, p in enumerate(products):
        if len(ranked) >= 5:
            break
        if i not in seen:
            ranked.append(p)

    return ranked[:5]


async def get_track_recommendation(track: TrackWithLyrics) -> TrackRecommendation:
    style_profile, queries = await _generate_queries(track)

    # Fetch products for all queries concurrently
    product_lists = await asyncio.gather(
        *[search_products(q, num=10) for q in queries]
    )

    # Rank products for each query concurrently
    ranked_lists = await asyncio.gather(
        *[_rank_products(q, products) for q, products in zip(queries, product_lists)]
    )

    ranked_queries = [
        RankedQuery(query=q, products=products)
        for q, products in zip(queries, ranked_lists)
    ]

    return TrackRecommendation(
        track_name=track.name,
        artist_name=track.artist_name,
        style_profile=style_profile,
        queries=ranked_queries,
    )
