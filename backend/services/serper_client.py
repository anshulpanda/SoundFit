import httpx
from config import settings
from models import Product

SERPER_URL = "https://google.serper.dev/shopping"


async def search_products(query: str, num: int = 10) -> list[Product]:
    async with httpx.AsyncClient(timeout=10) as client:
        response = await client.post(
            SERPER_URL,
            headers={
                "X-API-KEY": settings.serper_api_key,
                "Content-Type": "application/json",
            },
            json={"q": query, "num": num},
        )

    if response.status_code != 200:
        print(f"[SoundFit] Serper error for '{query}': {response.status_code} {response.text}")
        return []

    items = response.json().get("shopping", [])
    print(f"[SoundFit] Serper returned {len(items)} products for '{query}'")

    return [
        Product(
            title=item.get("title", ""),
            link=item.get("link", ""),
            image_url=item.get("imageUrl"),
            price=item.get("price"),
            source=item.get("source"),
        )
        for item in items
        if item.get("title") and item.get("link")
    ]
