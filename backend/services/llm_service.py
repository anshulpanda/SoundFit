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
- CLOTHING CUES: any explicit garment, brand, or accessory mentions in the lyrics
- CULTURAL REFERENCES: subcultures, eras, scenes (e.g. Y2K, grunge, hip-hop, indie, goth)
- COLOR PALETTE: colors implied by mood or explicit mentions
- LIFESTYLE SIGNALS: settings described (streets, clubs, nature, luxury, suburbia)

Return a JSON object with this structure:
{
  "style_profile": "2-3 sentences describing the aesthetic this song evokes. You MUST quote or directly reference at least one specific lyric line as evidence for the style direction.",
  "queries": [
    "specific shoppable fashion search query 1",
    "specific shoppable fashion search query 2",
    "specific shoppable fashion search query 3"
  ]
}

Rules for queries:
- Each query must be a specific, Google Shopping-ready phrase (e.g. "oversized vintage denim jacket 90s", "black satin slip dress gothic")
- Queries should cover different parts of an outfit (e.g. outerwear, bottoms, footwear, accessory)
- 2-3 queries total
- style_profile MUST cite a specific lyric — do not write generically
- Return ONLY the JSON object, no markdown"""

RANKING_SYSTEM_PROMPT = """You are a fashion stylist ranking shopping results by relevance to a style query.

Given a search query and a list of products, return the indices of the top 5 most relevant products in order from most to least relevant.

Consider: how well the product matches the aesthetic, style, and vibe of the query.

Return ONLY valid JSON: {"ranked": [list of integer indices]}"""

TASTE_SUMMARY_PROMPT = """You are a fashion stylist writing a short profile of someone's music taste for a style recommendation app.

Given data about a person's top 5 songs (with lyrics), write a 2-3 sentence summary of their overall aesthetic and what it says about their style sensibility.

You MUST:
- Reference at least 2 specific song titles or artists by name
- Quote or paraphrase at least one specific lyric line as evidence
- Be specific and evocative — not generic

Return ONLY a JSON object: {"taste_summary": "your summary here"}"""


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
    return data["style_profile"], data["queries"][:3]


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
            {"role": "user", "content": f"Query: {query}\n\nProducts:\n{product_list}"},
        ],
        temperature=0.2,
    )

    data = json.loads(response.choices[0].message.content)
    indices = data.get("ranked", list(range(min(5, len(products)))))

    ranked, seen = [], set()
    for i in indices:
        if isinstance(i, int) and 0 <= i < len(products) and i not in seen:
            ranked.append(products[i])
            seen.add(i)
    for i, p in enumerate(products):
        if len(ranked) >= 5:
            break
        if i not in seen:
            ranked.append(p)

    return ranked[:5]


async def get_track_recommendation(track: TrackWithLyrics) -> TrackRecommendation:
    style_profile, queries = await _generate_queries(track)

    product_lists = await asyncio.gather(
        *[search_products(q, num=10) for q in queries]
    )

    ranked_lists = await asyncio.gather(
        *[_rank_products(q, products) for q, products in zip(queries, product_lists)]
    )

    return TrackRecommendation(
        track_name=track.name,
        artist_name=track.artist_name,
        featured_artists=track.featured_artists,
        artist_image_url=track.artist_image_url,
        style_profile=style_profile,
        queries=[
            RankedQuery(query=q, products=products)
            for q, products in zip(queries, ranked_lists)
        ],
    )


async def get_taste_summary(tracks: list[TrackWithLyrics]) -> str:
    songs_block = "\n".join(
        f"- \"{t.name}\" by {t.artist_name}"
        + (f"\n  Lyrics excerpt: {t.lyrics[:400]}" if t.lyrics else "")
        for t in tracks
    )

    response = await _client.chat.completions.create(
        model="gpt-4o",
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": TASTE_SUMMARY_PROMPT},
            {"role": "user", "content": f"Top songs:\n{songs_block}"},
        ],
        temperature=0.7,
    )

    data = json.loads(response.choices[0].message.content)
    return data["taste_summary"]
