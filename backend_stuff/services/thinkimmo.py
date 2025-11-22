"""
ThinkImmo API Service
Handles all communication with ThinkImmo property search API
"""

import httpx
from typing import Dict, Any, Literal


THINKIMMO_URL = "https://thinkimmo-api.mgraetz.de/thinkimmo"


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


def get_demo_results(note: str = "", region: str = "Bayern") -> Dict[str, Any]:
    """
    Return demo property data for fallback when ThinkImmo is unavailable
    """
    return {
        "total": 6,
        "results": [
            {
                "id": "demo-1",
                "title": "Spacious Loft in City Center",
                "buyingPrice": 450000,
                "squareMeter": 75,
                "rooms": 2,
                "address": {"city": "Munich", "displayName": "Central District", "region": region},
                "images": [
                    {
                        "originalUrl": "https://via.placeholder.com/800x500?text=Modern+Loft"
                    }
                ],
            },
            {
                "id": "demo-2",
                "title": "Cozy 1BR Near Park",
                "buyingPrice": 320000,
                "squareMeter": 55,
                "rooms": 1.5,
                "address": {"city": "Munich", "displayName": "Green Quarter", "region": region},
                "images": [
                    {
                        "originalUrl": "https://via.placeholder.com/800x500?text=Park+View+Apartment"
                    }
                ],
            },
            {
                "id": "demo-3",
                "title": "Luxury Penthouse with Terrace",
                "buyingPrice": 980000,
                "squareMeter": 120,
                "rooms": 3,
                "address": {"city": "Munich", "displayName": "Premium Heights", "region": region},
                "images": [
                    {
                        "originalUrl": "https://via.placeholder.com/800x500?text=Penthouse+Luxury"
                    }
                ],
            },
            {
                "id": "demo-4",
                "title": "Renovated 2BR in Old Town",
                "buyingPrice": 540000,
                "squareMeter": 68,
                "rooms": 2,
                "address": {"city": "Munich", "displayName": "Historic Center", "region": region},
                "images": [
                    {
                        "originalUrl": "https://via.placeholder.com/800x500?text=Old+Town+Charm"
                    }
                ],
            },
            {
                "id": "demo-5",
                "title": "Modern Studio for Students",
                "buyingPrice": 250000,
                "squareMeter": 28,
                "rooms": 1,
                "address": {"city": "Munich", "displayName": "Student District", "region": region},
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
                "address": {"city": "Munich", "displayName": "Quiet Neighborhood", "region": region},
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


async def search_properties(
    city: str,
    region: str,
    property_type: Literal[
        "APARTMENTBUY",
        "HOUSEBUY",
        "LANDBUY",
        "GARAGEBUY",
        "OFFICEBUY",
    ],
    size: int = 200,
    from_index: int = 0
) -> Dict[str, Any]:
    """
    Search properties via ThinkImmo API
    
    Args:
        city: City name (e.g., "München")
        region: Region name (e.g., "Bayern")
        property_type: Type of property to search
        size: Number of results to fetch
        from_index: Starting index for pagination
    
    Returns:
        Dictionary with search results or demo data on failure
    """
    norm_city = transliterate_german(city)
    norm_region = transliterate_german(region)

    payload = {
        "active": True,
        "type": property_type,
        "sortBy": "desc",
        "sortKey": "pricePerSqm",
        "from": from_index,
        "size": size,
        "geoSearches": {
            "geoSearchQuery": norm_city,
            "geoSearchType": "town",
            "region": norm_region,
        }
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
        return get_demo_results(note="ThinkImmo unreachable", region=norm_region)

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
            
            # Add region to each property if not already present
            for prop in results:
                if "address" in prop and "region" not in prop["address"]:
                    prop["address"]["region"] = norm_region
            
            return data

        print(">>> ThinkImmo returned 0 results, using demo data instead")
        demo = get_demo_results(
            note=f"ThinkImmo status {resp.status_code} total=0; using demo data.",
            region=norm_region
        )
        demo["thinkimmo_raw"] = data
        return demo

    print(">>> Non-success status from ThinkImmo, using demo data")
    demo = get_demo_results(
        note=f"ThinkImmo status {resp.status_code}; using demo data.",
        region=norm_region
    )
    demo["thinkimmo_body"] = resp.text[:300]
    return demo
