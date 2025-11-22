from __future__ import annotations

from typing import Optional, Dict, Any

from fastapi import FastAPI
from pydantic import BaseModel

from .heatmap_backend import calculate_buying_power
from .router import router as heatmap_router


app = FastAPI(title="Nestify Heatmap API")
app.include_router(heatmap_router)


class BudgetRequest(BaseModel):
    salary: float
    monthly_rate: float
    state: str = "DE-BY"
    equity: float = 0.0
    has_fixed_period: bool = False
    fixed_period: Optional[int] = None
    rate_leasing_loans: float = 0.0
    amortisation: float = 1.5
    desired_total_time: int = 36


@app.get("/health")
async def health() -> Dict[str, str]:
    return {"status": "ok"}


def _extract_max_buying_power(resp: Any) -> Optional[float]:
    """Try to pull a numeric buying-power value from Interhyp response.

    Returns the first sensible numeric field found or None.
    """
    # Prefer specific fields commonly returned by the Interhyp JSON
    preferred_keys = ("priceBuilding", "loanAmount", "approxMaxBuyingPower", "maxBuyingPower", "value", "price")

    def _deep_search(obj):
        # If dict, check preferred keys first then recurse
        if isinstance(obj, dict):
            for k in preferred_keys:
                if k in obj and isinstance(obj[k], (int, float)):
                    return float(obj[k])
            for v in obj.values():
                found = _deep_search(v)
                if found is not None:
                    return found
        elif isinstance(obj, list):
            for item in obj:
                found = _deep_search(item)
                if found is not None:
                    return found
        elif isinstance(obj, (int, float)):
            # fallback: return a numeric leaf
            return float(obj)
        return None

    return _deep_search(resp)


@app.post("/test_budget")
async def test_budget(req: BudgetRequest) -> Dict[str, Any]:
    """Build Interhyp payload, call the live service and return normalized result."""
    fixed_period = req.fixed_period if req.has_fixed_period and req.fixed_period is not None else 10

    payload = {
        "monthlyRate": req.monthly_rate,
        "equityCash": req.equity,
        "federalState": req.state,
        "amortisation": req.amortisation,
        "fixedPeriod": fixed_period,
        "desiredTotalTime": req.desired_total_time,
        "salary": req.salary,
        "additionalLoan": req.rate_leasing_loans,
        "calculationMode": "TIMESPAN",
    }

    resp = await calculate_buying_power(payload)
    max_bp = _extract_max_buying_power(resp)
    return {"maxBuyingPower": max_bp, "raw": resp}


