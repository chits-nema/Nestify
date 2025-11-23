"""Heat map backend - Affordability mapping with real property data.

This module provides:
- Interhyp budget calculator API wrapper
- ThinkImmo property search integration
- Affordability categorization (green/yellow/red)
- Heatmap grid generation with real coordinates
"""
from __future__ import annotations

import asyncio
import math
from typing import Dict, List, Optional, Tuple, Any
from enum import Enum

import httpx
import logging

INTERHYP_URL = "https://www.interhyp.de/customer-generation/budget/calculateMaxBuyingPower"
THINKIMMO_URL = "https://thinkimmo-api.mgraetz.de/thinkimmo"

logger = logging.getLogger(__name__)


class AffordabilityLevel(str, Enum):
    AFFORDABLE = "affordable"      # Green: <= 90% of budget
    STRETCH = "stretch"            # Yellow: 90-110% of budget  
    OUT_OF_RANGE = "out_of_range"  # Red: > 110% of budget


# German state mappings
CITY_TO_STATE = {
    "münchen": "BY", "munich": "BY", "berlin": "BE", "hamburg": "HH",
    "köln": "NW", "cologne": "NW", "frankfurt": "HE", "stuttgart": "BW",
    "düsseldorf": "NW", "dortmund": "NW", "essen": "NW", "leipzig": "SN",
    "bremen": "HB", "dresden": "SN", "hannover": "NI", "nürnberg": "BY",
    "nuremberg": "BY", "duisburg": "NW", "bochum": "NW", "wuppertal": "NW",
    "bielefeld": "NW", "bonn": "NW", "münster": "NW", "karlsruhe": "BW",
    "mannheim": "BW", "augsburg": "BY", "wiesbaden": "HE", "mainz": "RP",
}

STATE_CODE_TO_FEDERAL = {
    "BY": "DE-BY", "BE": "DE-BE", "HH": "DE-HH", "NW": "DE-NW",
    "HE": "DE-HE", "BW": "DE-BW", "SN": "DE-SN", "HB": "DE-HB",
    "NI": "DE-NI", "RP": "DE-RP", "SH": "DE-SH", "SL": "DE-SL",
    "BB": "DE-BB", "MV": "DE-MV", "ST": "DE-ST", "TH": "DE-TH",
}

# Region mappings for ThinkImmo (full region names - matches Pinterest backend)
CITY_TO_REGION = {
    "münchen": "Bayern", "munich": "Bayern", "berlin": "Berlin", "hamburg": "Hamburg",
    "köln": "Nordrhein-Westfalen", "cologne": "Nordrhein-Westfalen",
    "frankfurt": "Hessen", "stuttgart": "Baden-Württemberg",
    "düsseldorf": "Nordrhein-Westfalen", "dortmund": "Nordrhein-Westfalen",
    "essen": "Nordrhein-Westfalen", "leipzig": "Sachsen", "bremen": "Bremen",
    "dresden": "Sachsen", "hannover": "Niedersachsen", "nürnberg": "Bayern",
    "nuremberg": "Bayern",
}


def transliterate_german(text: str) -> str:
    """Translate German umlauts for API compatibility."""
    if not text:
        return text
    mapping = {"ä": "ae", "ö": "oe", "ü": "ue", "Ä": "Ae", "Ö": "Oe", "Ü": "Ue", "ß": "ss"}
    return "".join(mapping.get(ch, ch) for ch in text)


def get_federal_state(city: str) -> str:
    """Get federal state code for Interhyp API from city name."""
    city_lower = city.lower().strip()
    state_code = CITY_TO_STATE.get(city_lower, "BY")
    return STATE_CODE_TO_FEDERAL.get(state_code, "DE-BY")


def get_region_code(city: str) -> str:
    """Get region code for ThinkImmo API from city name."""
    city_lower = city.lower().strip()
    return CITY_TO_STATE.get(city_lower, "BY")


def get_region_name(city: str) -> str:
    """Get full region name for ThinkImmo API (matches Pinterest backend)."""
    city_lower = city.lower().strip()
    return CITY_TO_REGION.get(city_lower, "Bayern")


async def calculate_buying_power_from_params(
    salary: float,
    monthly_rate: float,
    equity: float,
    city: str = "München",
    amortisation: float = 1.5,
    fixed_period: int = 10,
    total_time: int = 36,
    timeout: float = 10.0,
) -> Dict:
    """Calculate buying power using Interhyp API with city-based federal state."""
    federal_state = get_federal_state(city)
    
    payload = {
        "monthlyRate": monthly_rate,
        "equityCash": equity,
        "federalState": federal_state,
        "amortisation": amortisation,
        "fixedPeriod": fixed_period,
        "desiredTotalTime": total_time,
        "salary": salary,
        "additionalLoan": 0,
        "calculationMode": "TIMESPAN",
    }
    return await calculate_buying_power(payload, timeout=timeout)


async def calculate_buying_power(payload: Dict, timeout: float = 10.0) -> Dict:
    """Call Interhyp API to calculate max buying power."""
    logger.info("calculate_buying_power: calling Interhyp endpoint")
    async with httpx.AsyncClient(timeout=timeout) as client:
        r = await client.post(INTERHYP_URL, json=payload, headers={"Content-Type": "application/json"})
        r.raise_for_status()
        return r.json()


async def search_properties(
    city: str,
    property_type: str = "APARTMENTBUY",
    size: int = 200,
    from_index: int = 0,
    timeout: float = 20.0,
) -> Dict:
    """Search properties via ThinkImmo API (matches Pinterest backend implementation)."""
    norm_city = transliterate_german(city)
    region = get_region_name(city)
    region_code = get_region_code(city)
    
    # Use geoSearches like Pinterest for better results
    payload = {
        "active": True,
        "type": property_type,
        "sortBy": "desc",
        "sortKey": "publishDate",
        "from": from_index,
        "size": size,
        "geoSearches": {
            "geoSearchQuery": city,
            "geoSearchType": "town",
            "region": region
        }
    }
    
    logger.info(f"search_properties: searching for {property_type} (size: {size})")
    logger.info(f"ThinkImmo payload: {payload}")
    
    async with httpx.AsyncClient(timeout=timeout) as client:
        r = await client.post(THINKIMMO_URL, json=payload, headers={
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "NestifyHackathonClient/1.0",
        })
        
        logger.info(f"ThinkImmo response status: {r.status_code}")
        
        if r.status_code in (200, 201):
            data = r.json()
            logger.info(f"ThinkImmo returned {data.get('total', 0)} properties")
            return data
        else:
            logger.warning(f"ThinkImmo returned status {r.status_code}: {r.text[:200]}")
            return {"total": 0, "results": []}


def categorize_affordability(price: float, budget: float) -> AffordabilityLevel:
    """Categorize property affordability based on budget.
    
    - Affordable (green): price <= 90% of budget
    - Stretch (yellow): price between 90-110% of budget
    - Out of range (red): price > 110% of budget
    """
    if budget <= 0:
        return AffordabilityLevel.OUT_OF_RANGE
    
    ratio = price / budget
    
    if ratio <= 0.9:
        return AffordabilityLevel.AFFORDABLE
    elif ratio <= 1.1:
        return AffordabilityLevel.STRETCH
    else:
        return AffordabilityLevel.OUT_OF_RANGE


def process_properties_for_heatmap(
    properties: List[Dict],
    budget: float,
    filter_city: Optional[str] = None,
) -> List[Dict]:
    """Process properties and add affordability categorization and coordinates.
    
    Args:
        properties: Raw properties from ThinkImmo
        budget: Max buying power for affordability calculation
        filter_city: Optional city name to filter by (case-insensitive)
    """
    processed = []
    
    for prop in properties:
        price = prop.get("buyingPrice", 0)
        if not price or price <= 0:
            continue
        
        # Extract coordinates from address
        address = prop.get("address", {})
        lat = address.get("lat")
        lon = address.get("lon")
        
        # Skip if no coordinates
        if lat is None or lon is None:
            continue
        
        # Filter by city if specified
        if filter_city:
            prop_city = address.get("_normalized_city") or address.get("city") or ""
            if filter_city.lower() not in prop_city.lower():
                continue
        
        level = categorize_affordability(price, budget)
        
        processed.append({
            "id": prop.get("id"),
            "title": prop.get("title", "Unknown"),
            "price": price,
            "lat": lat,
            "lon": lon,
            "sqm": prop.get("squareMeter"),
            "rooms": prop.get("rooms"),
            "affordability": level.value,
            "price_ratio": round(price / budget, 2) if budget > 0 else None,
            "city": address.get("city") or address.get("_normalized_city"),
            "postcode": address.get("postcode") or prop.get("zip"),
            "image": prop.get("images", [{}])[0].get("originalUrl") if prop.get("images") else None,
            "platform_url": prop.get("platforms", [{}])[0].get("url") if prop.get("platforms") else None,
        })
    
    return processed


def create_heatmap_grid(
    properties: List[Dict],
    grid_size: Tuple[int, int] = (30, 30),
) -> Dict:
    """Create a grid-based heatmap from processed properties.
    
    Returns grid cells with counts by affordability level.
    """
    if not properties:
        return {"grid": [], "bbox": None, "stats": {}}
    
    lats = [p["lat"] for p in properties]
    lons = [p["lon"] for p in properties]
    
    minlat, maxlat = min(lats), max(lats)
    minlon, maxlon = min(lons), max(lons)
    
    # Add small padding
    lat_pad = (maxlat - minlat) * 0.05 or 0.01
    lon_pad = (maxlon - minlon) * 0.05 or 0.01
    minlat -= lat_pad
    maxlat += lat_pad
    minlon -= lon_pad
    maxlon += lon_pad
    
    rows, cols = grid_size
    
    # Initialize grid with affordability counts
    grid = [[{"affordable": 0, "stretch": 0, "out_of_range": 0, "total": 0} 
             for _ in range(cols)] for _ in range(rows)]
    
    stats = {"affordable": 0, "stretch": 0, "out_of_range": 0, "total": 0}
    
    for p in properties:
        lat, lon = p["lat"], p["lon"]
        level = p["affordability"]
        
        # Map to grid indices
        r = int((lat - minlat) / (maxlat - minlat + 1e-12) * (rows - 1))
        c = int((lon - minlon) / (maxlon - minlon + 1e-12) * (cols - 1))
        r = max(0, min(rows - 1, r))
        c = max(0, min(cols - 1, c))
        
        grid[r][c][level] += 1
        grid[r][c]["total"] += 1
        stats[level] += 1
        stats["total"] += 1
    
    # Calculate cell centers for frontend
    cell_height = (maxlat - minlat) / rows
    cell_width = (maxlon - minlon) / cols
    
    return {
        "grid": grid,
        "bbox": {
            "minLat": minlat, "maxLat": maxlat,
            "minLon": minlon, "maxLon": maxlon,
        },
        "gridSize": {"rows": rows, "cols": cols},
        "cellSize": {"height": cell_height, "width": cell_width},
        "stats": stats,
    }


async def get_affordability_heatmap(
    salary: float,
    monthly_rate: float,
    equity: float,
    city: str = "München",
    property_type: str = "APARTMENTBUY",
    property_count: int = 200,
) -> Dict[str, Any]:
    """Main function: Calculate budget and generate affordability heatmap.
    
    Returns buying power, processed properties, and heatmap grid.
    """
    # Step 1: Calculate buying power
    budget_response = await calculate_buying_power_from_params(
        salary=salary,
        monthly_rate=monthly_rate,
        equity=equity,
        city=city,
    )
    
    # Extract max buying power from response
    # Check nested scoringResult first
    scoring = budget_response.get("scoringResult", {})
    buying_power = (
        scoring.get("priceBuilding") or
        scoring.get("loanAmount") or
        budget_response.get("priceBuilding") or
        budget_response.get("approxMaxBuyingPower") or
        budget_response.get("maxBuyingPower") or
        0
    )
    
    logger.info(f"Extracted buying power: {buying_power} from budget response")
    
    # Step 2: Search properties in the city
    search_response = await search_properties(
        city=city,
        property_type=property_type,
        size=property_count,
    )
    
    properties = search_response.get("results", [])
    total_found = search_response.get("total", 0)
    
    logger.info(f"Found {total_found} properties from ThinkImmo")
    
    if not properties:
        logger.warning(f"No properties returned. Response: {search_response}")
    
    # Step 3: Process properties with affordability levels and city filter
    processed = process_properties_for_heatmap(properties, buying_power, filter_city=city)
    
    logger.info(f"Processed {len(processed)} properties with coordinates (filtered for {city})")
    
    if not processed:
        logger.warning(f"No properties match city '{city}' or have coordinates. Raw count was {len(properties)}")
    
    # Step 4: Generate heatmap grid
    heatmap = create_heatmap_grid(processed)
    
    return {
        "buying_power": buying_power,
        "budget_response": budget_response,
        "city": city,
        "total_properties_found": total_found,
        "properties_with_coords": len(processed),
        "properties": processed,
        "heatmap": heatmap,
    }


__all__ = [
    "calculate_buying_power",
    "calculate_buying_power_from_params",
    "search_properties",
    "categorize_affordability",
    "process_properties_for_heatmap",
    "create_heatmap_grid",
    "get_affordability_heatmap",
    "AffordabilityLevel",
]