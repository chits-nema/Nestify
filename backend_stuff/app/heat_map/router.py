from __future__ import annotations
from fastapi import APIRouter, Body, HTTPException, Query
from pydantic import BaseModel
from typing import Any, Dict, List, Optional

from .heatmap_backend import (
    calculate_buying_power,
    calculate_buying_power_from_params,
    search_properties,
    get_affordability_heatmap,
)

router = APIRouter(prefix="/heatmap", tags=["heatmap"])


class HeatmapRequest(BaseModel):
    """Request model for heatmap generation."""
    salary: float                          # Monthly net household income
    monthly_rate: float                    # Desired monthly mortgage payment
    equity: float                          # Available equity/down payment
    city: str = "München"                  # Target city for property search
    property_type: str = "APARTMENTBUY"    # APARTMENTBUY or HOUSEBUY
    property_count: int = 200              # Number of properties to fetch


class BudgetOnlyRequest(BaseModel):
    """Request model for budget calculation only."""
    salary: float
    monthly_rate: float
    equity: float
    city: str = "München"
    fixed_period_years: Optional[int] = None


@router.post("/calculate")
async def calculate_heatmap(req: HeatmapRequest) -> Dict[str, Any]:
    """Generate affordability heatmap for a city based on user's budget.
    
    This endpoint:
    1. Calculates max buying power using Interhyp API
    2. Searches for real properties in the specified city
    3. Categorizes each property as affordable/stretch/out_of_range
    4. Returns properties with coordinates and a grid-based heatmap
    
    Affordability levels:
    - affordable (green): price <= 90% of budget
    - stretch (yellow): price between 90-110% of budget
    - out_of_range (red): price > 110% of budget
    """
    try:
        result = await get_affordability_heatmap(
            salary=req.salary,
            monthly_rate=req.monthly_rate,
            equity=req.equity,
            city=req.city,
            property_type=req.property_type,
            property_count=req.property_count,
        )
        return result
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc))


@router.post("/budget")
async def calculate_budget(req: BudgetOnlyRequest) -> Dict[str, Any]:
    """Calculate buying power only (without property search).
    
    Useful for quick budget estimates before generating full heatmap.
    """
    try:
        # Use provided fixed_period_years or default to 10
        fixed_period = req.fixed_period_years if req.fixed_period_years is not None else 10
        
        resp = await calculate_buying_power_from_params(
            salary=req.salary,
            monthly_rate=req.monthly_rate,
            equity=req.equity,
            city=req.city,
            fixed_period=fixed_period,
        )
        
        buying_power = (
            resp.get("priceBuilding") or
            resp.get("approxMaxBuyingPower") or
            resp.get("maxBuyingPower") or
            0
        )
        
        return {
            "buying_power": buying_power,
            "city": req.city,
            "raw_response": resp,
        }
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc))


@router.post("/buying_power")
async def buying_power(payload: Dict = Body(...)) -> Dict[str, Any]:
    """Proxy endpoint to calculate buying power with raw Interhyp payload."""
    try:
        resp = await calculate_buying_power(payload)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc))
    return resp


@router.get("/search")
async def search_city_properties(
    city: str = Query("München"),
    property_type: str = Query("APARTMENTBUY"),
    size: int = Query(50),
) -> Dict[str, Any]:
    """Search properties in a city (for testing/debugging)."""
    try:
        result = await search_properties(
            city=city,
            property_type=property_type,
            size=size,
        )
        return result
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc))


@router.post("/debug")
async def debug_heatmap(req: HeatmapRequest) -> Dict[str, Any]:
    """Debug endpoint showing step-by-step what's happening."""
    debug_info = {"steps": []}
    
    try:
        # Step 1: Budget calculation
        debug_info["steps"].append("Step 1: Calling Interhyp for budget calculation...")
        budget_response = await calculate_buying_power_from_params(
            salary=req.salary,
            monthly_rate=req.monthly_rate,
            equity=req.equity,
            city=req.city,
        )
        debug_info["budget_response"] = budget_response
        
        # Extract buying power
        scoring = budget_response.get("scoringResult", {})
        buying_power = (
            scoring.get("priceBuilding") or
            scoring.get("loanAmount") or
            budget_response.get("priceBuilding") or
            0
        )
        debug_info["extracted_buying_power"] = buying_power
        debug_info["steps"].append(f"✓ Buying power extracted: {buying_power}")
        
        # Step 2: Property search
        debug_info["steps"].append(f"Step 2: Searching properties in {req.city}...")
        search_response = await search_properties(
            city=req.city,
            property_type=req.property_type,
            size=req.property_count,
        )
        
        properties = search_response.get("results", [])
        total = search_response.get("total", 0)
        debug_info["thinkimmo_total"] = total
        debug_info["thinkimmo_returned"] = len(properties)
        debug_info["steps"].append(f"✓ ThinkImmo returned {len(properties)} properties (total: {total})")
        
        # Sample first property to check structure
        if properties:
            sample_prop = properties[0]
            debug_info["sample_property"] = {
                "id": sample_prop.get("id"),
                "title": sample_prop.get("title"),
                "price": sample_prop.get("buyingPrice"),
                "has_address": "address" in sample_prop,
                "address": sample_prop.get("address", {}),
                "has_lat": sample_prop.get("address", {}).get("lat") is not None,
                "has_lon": sample_prop.get("address", {}).get("lon") is not None,
            }
        else:
            debug_info["sample_property"] = None
            debug_info["steps"].append("⚠ No properties to sample")
        
        # Step 3: Check how many have coordinates
        props_with_coords = 0
        props_without_coords = 0
        for prop in properties:
            address = prop.get("address", {})
            if address.get("lat") is not None and address.get("lon") is not None:
                props_with_coords += 1
            else:
                props_without_coords += 1
        
        debug_info["properties_with_coordinates"] = props_with_coords
        debug_info["properties_without_coordinates"] = props_without_coords
        debug_info["steps"].append(f"✓ Properties with coordinates: {props_with_coords}/{len(properties)}")
        
        if props_with_coords == 0:
            debug_info["steps"].append("❌ NO PROPERTIES HAVE COORDINATES - This is the issue!")
        
        return debug_info
        
    except Exception as exc:
        debug_info["error"] = str(exc)
        debug_info["error_type"] = type(exc).__name__
        import traceback
        debug_info["traceback"] = traceback.format_exc()
        return debug_info