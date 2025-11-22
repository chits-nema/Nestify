import asyncio
import json

from backend_stuff.app.heat_map.heatmap_backend import calculate_buying_power, approximate_buying_power

INTERHYP_URL = "https://www.interhyp.de/customer-generation/budget/calculateMaxBuyingPower"

payload = {
    "monthlyRate": 3000,
    "equityCash": 100000,
    "federalState": "DE-BY",
    "amortisation": 1.5,
    "fixedPeriod": 10,
    "desiredTotalTime": 36,
    "salary": 10000,
    "additionalLoan": 0,
    "calculationMode": "TIMESPAN",
}


async def main():
    print("Payload:\n", json.dumps(payload, indent=2))
    approx = approximate_buying_power(payload)
    print("Approximate (heuristic) buying power:", approx)
    try:
        resp = await calculate_buying_power(payload)
        # Try to extract a sensible numeric field if present
        numeric = None
        if isinstance(resp, dict):
            for key in ("approxMaxBuyingPower", "maxBuyingPower", "value", "price"):
                if key in resp and isinstance(resp[key], (int, float)):
                    numeric = resp[key]
                    break
        print('\nInterhyp raw response (first 2000 chars):')
        try:
            print(json.dumps(resp)[:2000])
        except Exception:
            print(str(resp)[:2000])
        print('\nExtracted numeric if any:', numeric)
    except Exception as e:
        print("Error calling Interhyp:", type(e).__name__, e)


if __name__ == "__main__":
    asyncio.run(main())
