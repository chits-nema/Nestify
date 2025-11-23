from __future__ import annotations

from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .heat_map.router import router as heatmap_router
from .pinterest.router import router as pinterest_router
from .chatbot.router import router as chatbot_router

app = FastAPI(title="Nestify Backend")

# very permissive CORS for local development; lock this down in production
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(heatmap_router)
app.include_router(pinterest_router)
app.include_router(chatbot_router)


@app.get("/health")
async def health():
    return {"status": "ok", "service": "nestify-backend"}


# ---------- ThinkImmo Property Search ----------


# ---------- Property Search Integration ----------
from pydantic import BaseModel
from typing import Literal
import httpx

THINKIMMO_URL = "https://thinkimmo-api.mgraetz.de/thinkimmo"


# ---------- helpers ----------

def transliterate_german(text: str) -> str:
    """Translate German umlauts as required by ThinkImmo docs."""
    if not text:
        return text
    mapping = {
        "ä": "ae", "ö": "oe", "ü": "ue",
        "Ä": "Ae", "Ö": "Oe", "Ü": "Ue",
        "ß": "ss",
    }
    return "".join(mapping.get(ch, ch) for ch in text)


class PropertySearchRequest(BaseModel):
    city: str = "München"
    region: str = "Bayern"
    size: int = 200  # Increased for better swipe variety
    from_index: int = 0
    propertyType: Literal[
        "APARTMENTBUY",
        "HOUSEBUY",
        "LANDBUY",
        "GARAGEBUY",
        "OFFICEBUY",
        "ALL"  # Add option for all types
    ] = "ALL"  # Default to all types for swipe


# ---------- main search endpoint ----------

@app.post("/api/properties/search")
async def search_properties(req: PropertySearchRequest):
    """
    Proxy to ThinkImmo.
    - Uses umlaut transliteration
    - Sends geoSearchType='town'
    - Treats 200/201 as success
    - If ThinkImmo returns 0 results or errors, falls back to demo data.
    """

    norm_city = transliterate_german(req.city)
    norm_region = transliterate_german(req.region)

    # Use same geo search as Pinterest for better results
    payload = {
        "active": True,
        "sortBy": "desc",
        "sortKey": "publishDate",
        "from": req.from_index,
        "size": req.size,
        "geoSearches": {
            "geoSearchQuery": req.city,
            "geoSearchType": "town",
            "region": req.region
        }
    }
    
    # Only add type filter if not searching for all types
    if req.propertyType != "ALL":
        payload["type"] = req.propertyType


    print("\n>>> PAYLOAD SENT TO THINKIMMO")
    print(f">>> City: {req.city} -> {norm_city}, Region: {req.region} -> {norm_region}")
    print(payload)

    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "User-Agent": "NestifyHackathonClient/1.0",
    }

    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            resp = await client.post(THINKIMMO_URL, json=payload, headers=headers)
    except Exception as e:
        print(">>> ERROR contacting ThinkImmo:", e)
        return _demo_results(note="ThinkImmo unreachable")

    print(">>> THINKIMMO STATUS:", resp.status_code)

    try:
        data = resp.json()
    except Exception:
        data = {"total": 0, "results": []}

    # Treat 200 and 201 as "OK"
    if resp.status_code in (200, 201):
        total = data.get("total", 0)
        results = data.get("results", [])

        if total > 0 and results:
            print(f">>> SUCCESS with {total} listings from ThinkImmo")
            print(f">>> Returning {len(results)} results in response")
            print(f">>> First result keys: {list(results[0].keys()) if results else 'N/A'}")
            return data

        print(f">>> ThinkImmo returned 0 results for {norm_city}, {norm_region}")
        print(f">>> Response data: {data}")
        demo = _demo_results(
            note=f"ThinkImmo status {resp.status_code} total=0 for {norm_city}; using demo data.",
            city=norm_city,
            region=norm_region
        )
        demo["thinkimmo_raw"] = data
        return demo

    print(">>> Non-success status from ThinkImmo, using demo data")
    demo = _demo_results(
        note=f"ThinkImmo status {resp.status_code}; using demo data.",
        city=norm_city,
        region=norm_region
    )
    demo["thinkimmo_body"] = resp.text[:300]
    return demo


# ---------- demo data (for swipe + listings if ThinkImmo empty) ----------

def _demo_results(note: str = "", city: str = "Munich", region: str = "Bayern") -> dict:
    return {
        "total": 6,
        "results": [
            {
                "id": "demo-1",
                "title": f"Sunny Loft in {city}",
                "buyingPrice": 450000,
                "squareMeter": 60,
                "rooms": 2,
                "address": {"city": city, "displayName": f"{city} City Center", "region": region},
                "images": [
                    {
                        "originalUrl": "https://via.placeholder.com/800x500?text=Sunny+Loft"
                    }
                ],
            },
            {
                "id": "demo-2",
                "title": f"Cozy Studio in {city}",
                "buyingPrice": 320000,
                "squareMeter": 35,
                "rooms": 1,
                "address": {"city": city, "displayName": f"{city} Downtown", "region": region},
                "images": [
                    {
                        "originalUrl": "https://via.placeholder.com/800x500?text=Cozy+Studio"
                    }
                ],
            },
            {
                "id": "demo-3",
                "title": f"Shared Flat in {city}",
                "buyingPrice": 280000,
                "squareMeter": 45,
                "rooms": 2,
                "address": {"city": city, "displayName": f"{city} University Area", "region": region},
                "images": [
                    {
                        "originalUrl": "https://via.placeholder.com/800x500?text=Shared+Flat"
                    }
                ],
            },
            {
                "id": "demo-4",
                "title": f"Riverside Apartment in {city}",
                "buyingPrice": 520000,
                "squareMeter": 70,
                "rooms": 3,
                "address": {"city": city, "displayName": f"{city} Riverside", "region": region},
                "images": [
                    {
                        "originalUrl": "https://via.placeholder.com/800x500?text=Riverside+Apartment"
                    }
                ],
            },
            {
                "id": "demo-5",
                "title": f"Modern Student Studio in {city}",
                "buyingPrice": 250000,
                "squareMeter": 28,
                "rooms": 1,
                "address": {"city": city, "displayName": f"{city} Student District", "region": region},
                "images": [
                    {
                        "originalUrl": "https://via.placeholder.com/800x500?text=Student+Studio"
                    }
                ],
            },
            {
                "id": "demo-6",
                "title": f"Family-Friendly Apartment in {city}",
                "buyingPrice": 600000,
                "squareMeter": 85,
                "rooms": 4,
                "address": {"city": city, "displayName": f"{city} Quiet Neighborhood", "region": region},
                "images": [
                    {
                        "originalUrl": "https://via.placeholder.com/800x500?text=Family+Apartment"
                    }
                ],
            },
        ],
        "source": "mocked-demo-data",
        "note": note,
    }
