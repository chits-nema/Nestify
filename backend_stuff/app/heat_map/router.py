from __future__ import annotations

from fastapi import APIRouter, Body, HTTPException, Query
from typing import Any, Dict, List, Optional

from .heatmap_backend import (
    calculate_buying_power,
    calculate_buying_power_from_params,
    create_affordability_heatmap,
    generate_sample_properties,
)

router = APIRouter(prefix="/heatmap", tags=["heatmap"])


@router.post("/buying_power")
async def buying_power(payload: Dict = Body(...)) -> Dict[str, Any]:
    """Proxy endpoint to calculate buying power. Accepts the Interhyp payload.

    This endpoint always performs a live calculation against the Interhyp API.
    """
    try:
        resp = await calculate_buying_power(payload)
    except Exception as exc:  # pragma: no cover - surface errors to caller
        raise HTTPException(status_code=502, detail=str(exc))
    return resp


@router.get("/sample_properties")
def sample_properties(
    lat: float = Query(48.137154),
    lon: float = Query(11.576124),
    radius_km: float = Query(10.0),
    count: int = Query(200),
) -> List[Dict]:
    """Return generated sample properties around a center point."""
    props = generate_sample_properties(center=(lat, lon), radius_km=radius_km, count=count)
    return props


@router.post("/grid")
async def heatmap_grid(
    buying_power_payload: Optional[Dict] = Body(None),
    salary: Optional[float] = Body(None),
    monthly_rate: Optional[float] = Body(None),
    equity: Optional[float] = Body(None),
    grid_rows: int = Body(50),
    grid_cols: int = Body(50),
) -> Dict[str, Any]:
    """Create an affordability heatmap grid.

    Either provide a full Interhyp payload as the body, or provide salary/monthly_rate/equity.
    The endpoint will compute buying power by calling the live Interhyp API and then produce a grid.
    """
    # determine buying power
    if buying_power_payload:
        resp = await calculate_buying_power(buying_power_payload)
        buying_power = resp.get("approxMaxBuyingPower") or resp.get("maxBuyingPower") or resp
    else:
        if salary is None or monthly_rate is None or equity is None:
            raise HTTPException(status_code=400, detail="Provide either a full payload or salary, monthly_rate and equity")
        resp = await calculate_buying_power_from_params(salary=salary, monthly_rate=monthly_rate, equity=equity)
        buying_power = resp.get("approxMaxBuyingPower") or resp.get("maxBuyingPower") or resp

    # create sample properties and grid
    props = generate_sample_properties(count=500)
    grid = create_affordability_heatmap(props, float(buying_power) if isinstance(buying_power, (int, float)) else float(resp.get("approxMaxBuyingPower", 0)), grid_size=(grid_rows, grid_cols))
    return {"buying_power_response": resp, "heatmap": grid}
