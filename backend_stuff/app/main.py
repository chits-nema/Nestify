from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .heat_map.router import router as heatmap_router
from .pinterest.router import router as pinterest_router

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


@app.get("/health")
async def health():
    return {"status": "ok", "service": "nestify-backend"}


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
    ] = "APARTMENTBUY"


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

    payload = {
        "active": True,
        "type": req.propertyType,
        "sortBy": "desc",
        "sortKey": "pricePerSqm",
        "from": req.from_index,
        "size": req.size,
        "geoSearches": {
            "geoSearchQuery": norm_city,
            "geoSearchType": "town",
            "region": norm_region,
        },
    }
    
    payload = {
    "active": True,
    "type": req.propertyType,
    "sortBy": "desc",
    "sortKey": "pricePerSqm",
    "from": req.from_index,
    "size": req.size,
    # "geoSearches": {
    #     "geoSearchQuery": norm_city,
    #     "geoSearchType": "town",
    #     "region": norm_region,
    # }
    }


    print("\n>>> PAYLOAD SENT TO THINKIMMO")
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
            return data

        print(">>> ThinkImmo returned 0 results, using demo data instead")
        demo = _demo_results(
            note=f"ThinkImmo status {resp.status_code} total=0; using demo data.",
        )
        demo["thinkimmo_raw"] = data
        return demo

    print(">>> Non-success status from ThinkImmo, using demo data")
    demo = _demo_results(
        note=f"ThinkImmo status {resp.status_code}; using demo data.",
    )
    demo["thinkimmo_body"] = resp.text[:300]
    return demo


# ---------- demo data (for swipe + listings if ThinkImmo empty) ----------

def _demo_results(note: str = "") -> dict:
    return {
        "total": 6,
        "results": [
            {
                "id": "demo-1",
                "title": "Sunny Loft in Munich",
                "buyingPrice": 450000,
                "squareMeter": 60,
                "rooms": 2,
                "address": {"city": "Munich", "displayName": "Munich City Center"},
                "images": [
                    {
                        "originalUrl": "https://via.placeholder.com/800x500?text=Sunny+Loft"
                    }
                ],
            },
            {
                "id": "demo-2",
                "title": "Cozy Studio in Schwabing",
                "buyingPrice": 320000,
                "squareMeter": 35,
                "rooms": 1,
                "address": {"city": "Munich", "displayName": "Schwabing"},
                "images": [
                    {
                        "originalUrl": "https://via.placeholder.com/800x500?text=Cozy+Studio"
                    }
                ],
            },
            {
                "id": "demo-3",
                "title": "Shared Flat near TUM",
                "buyingPrice": 280000,
                "squareMeter": 45,
                "rooms": 2,
                "address": {"city": "Munich", "displayName": "Near University"},
                "images": [
                    {
                        "originalUrl": "https://via.placeholder.com/800x500?text=Shared+Flat"
                    }
                ],
            },
            {
                "id": "demo-4",
                "title": "Riverside Apartment",
                "buyingPrice": 520000,
                "squareMeter": 70,
                "rooms": 3,
                "address": {"city": "Munich", "displayName": "Isar Riverside"},
                "images": [
                    {
                        "originalUrl": "https://via.placeholder.com/800x500?text=Riverside+Apartment"
                    }
                ],
            },
            {
                "id": "demo-5",
                "title": "Modern Student Studio",
                "buyingPrice": 250000,
                "squareMeter": 28,
                "rooms": 1,
                "address": {"city": "Munich", "displayName": "Student District"},
                "images": [
                    {
                        "originalUrl": "https://via.placeholder.com/800x500?text=Student+Studio"
                    }
                ],
            },
            {
                "id": "demo-6",
                "title": "Family-Friendly Apartment",
                "buyingPrice": 600000,
                "squareMeter": 85,
                "rooms": 4,
                "address": {"city": "Munich", "displayName": "Quiet Neighborhood"},
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
