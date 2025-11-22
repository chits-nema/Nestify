from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Literal
import httpx

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

THINKIMMO_URL = "https://thinkimmo-api.mgraetz.de/thinkimmo"


class PropertySearchRequest(BaseModel):
    city: str
    region: str
    size: int = 20
    from_index: int = 0
    propertyType: Literal[
        "APPARTMENTBUY",
        "HOUSEBUY",
        "LANDBUY",
        "GARAGEBUY",
        "OFFICEBUY",
    ] = "APPARTMENTBUY"


@app.post("/api/properties/search")
async def search_properties(req: PropertySearchRequest):
    payload = {
        "active": True,
        "type": req.propertyType,
        "sortBy": "asc",
        "sortKey": "pricePerSqm",
        "from": req.from_index,
        "size": req.size,
        "geoSearches": {
            "geoSearchQuery": req.city,   # e.g. "Munich"
            "geoSearchType": "city",
            "region": req.region,         # e.g. "BY"
        },
    }

    print(">>> SENDING TO THINKIMMO:", payload)

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(THINKIMMO_URL, json=payload)
    except Exception as e:
        print(">>> ERROR calling ThinkImmo:", e)
        return {"results": [], "total": 0, "error": "ThinkImmo unreachable"}

    print(">>> THINKIMMO STATUS:", resp.status_code)
    print(">>> THINKIMMO BODY:", resp.text[:300])

    # If ThinkImmo returns 200, pass through real data
    if resp.status_code == 200:
        return resp.json()

    # If ThinkImmo returns 404 or something else, use fallback demo data
    # so your Tinder UI still works for the hackathon.
    demo_results = {
        "total": 3,
        "results": [
            {
                "title": "Demo Loft in Munich",
                "buyingPrice": 450000,
                "squareMeter": 60,
                "rooms": 2,
                "address": {"city": "Munich", "displayName": "Munich City Center"},
                "images": [
                    {
                        "originalUrl": "https://via.placeholder.com/600x400?text=Demo+Loft"
                    }
                ],
            },
            {
                "title": "Cozy Studio in Schwabing",
                "buyingPrice": 320000,
                "squareMeter": 35,
                "rooms": 1,
                "address": {"city": "Munich", "displayName": "Schwabing"},
                "images": [
                    {
                        "originalUrl": "https://via.placeholder.com/600x400?text=Demo+Studio"
                    }
                ],
            },
            {
                "title": "Shared Flat near Uni",
                "buyingPrice": 280000,
                "squareMeter": 45,
                "rooms": 2,
                "address": {"city": "Munich", "displayName": "Near University"},
                "images": [
                    {
                        "originalUrl": "https://via.placeholder.com/600x400?text=Demo+Flat"
                    }
                ],
            },
        ],
    }

    return {
        "total": demo_results["total"],
        "results": demo_results["results"],
        "note": "ThinkImmo returned status "
        + str(resp.status_code)
        + ", serving demo data.",
    }
