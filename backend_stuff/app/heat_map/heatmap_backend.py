"""Heat map backend helpers for affordability mapping.

This module provides:
- wrappers around the Interhyp budget calculator API (async, httpx)
- helpers to generate sample property points and compute affordability

The functions are designed to be used by a FastAPI route later. All
calculations performed here call the live Interhyp endpoint.
"""
from __future__ import annotations

import asyncio
import math
import os
import random
from typing import Dict, Iterable, List, Optional, Tuple

import httpx
import logging

INTERHYP_URL = "https://www.interhyp.de/customer-generation/budget/calculateMaxBuyingPower"

logger = logging.getLogger(__name__)



async def calculate_buying_power_from_params(
	salary: float,
	monthly_rate: float,
	equity: float,
	federal_state: str = "DE-BY",
	amortisation: float = 1.5,
	fixed_period: int = 10,
	total_time: int = 36,
	timeout: float = 10.0,
) -> Dict:
	"""Calculate buying power by building a payload and delegating to
	:func:`calculate_buying_power`.

	This always performs a live call to the Interhyp endpoint.
	"""
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
	"""Call Interhyp API to calculate max buying power.

	Args:
		payload: JSON serializable payload expected by Interhyp.
		timeout: request timeout in seconds.

	Returns:
		Parsed JSON response as a dictionary. Raises on HTTP/network errors.
	"""
	# Always call the live Interhyp endpoint. This function no longer supports
	# mock or environment overrides — it performs a real HTTP POST and returns
	# the parsed JSON response or raises on network/HTTP errors.
	logger.info("calculate_buying_power: calling Interhyp endpoint %s", INTERHYP_URL)
	async with httpx.AsyncClient(timeout=timeout) as client:
		r = await client.post(
			INTERHYP_URL,
			json=payload,
			headers={"Content-Type": "application/json"},
		)
		r.raise_for_status()
		logger.info("calculate_buying_power: Interhyp response status=%s", r.status_code)
		return r.json()


def generate_sample_properties(
	center: Tuple[float, float] = (48.137154, 11.576124),
	radius_km: float = 10.0,
	count: int = 500,
	price_min: int = 80000,
	price_max: int = 1200000,
) -> List[Dict]:
	"""Generate a list of sample property points within a circle around
	``center`` (lat, lon).

	Each property is represented as a dict: {"lat": ..., "lon": ..., "price": ...}
	Prices are sampled and biased by distance (closer to center -> more expensive)
	so the heatmap looks plausible.
	"""
	lat_center, lon_center = center
	props: List[Dict] = []
	for i in range(count):
		# random distance and angle
		d = random.random() ** 0.5 * radius_km  # sqrt to bias toward center
		theta = random.random() * 2 * math.pi
		# rough conversion: 1 deg lat ~= 111 km, lon scale by cos(lat)
		delta_lat = (d * math.cos(theta)) / 111.0
		delta_lon = (d * math.sin(theta)) / (111.0 * math.cos(math.radians(lat_center)) or 1)
		lat = lat_center + delta_lat
		lon = lon_center + delta_lon

		# price biased: closer -> higher price
		distance_factor = max(0.0, 1.0 - (d / (radius_km + 1e-6)))
		price = int(
			price_min + (price_max - price_min) * (distance_factor ** 1.5) * random.uniform(0.6, 1.4)
		)
		props.append({"lat": lat, "lon": lon, "price": price})
	return props


def compute_affordable_points(properties: Iterable[Dict], buying_power: float) -> List[Dict]:
	"""Return the subset of properties affordable within the buying power.

	Each returned entry is the input dict with an extra key "affordable": True.
	"""
	result: List[Dict] = []
	for p in properties:
		try:
			price = float(p.get("price", 0))
		except Exception:
			price = 0.0
		affordable = price <= float(buying_power)
		r = dict(p)
		r["affordable"] = affordable
		result.append(r)
	return result


def create_affordability_heatmap(properties: Iterable[Dict], buying_power: float, grid_size: Tuple[int, int] = (50, 50)) -> Dict:
	"""Create a simple grid-based heatmap (counts of affordable properties per cell).

	Returns a dict with keys: grid (2D list), bbox (minlat, minlon, maxlat, maxlon), and counts.
	This is intentionally lightweight — the frontend can convert counts to color scale.
	"""
	props = list(properties)
	if not props:
		return {"grid": [], "bbox": None, "counts": 0}

	lats = [p["lat"] for p in props]
	lons = [p["lon"] for p in props]
	minlat, maxlat = min(lats), max(lats)
	minlon, maxlon = min(lons), max(lons)

	rows, cols = grid_size
	# initialize grid
	grid = [[0 for _ in range(cols)] for _ in range(rows)]
	counts = 0
	for p in props:
		if p.get("price", float("inf")) <= buying_power:
			# map lat/lon into grid indices
			# clamp to edges
			try:
				r = int((p["lat"] - minlat) / (maxlat - minlat + 1e-12) * (rows - 1))
				c = int((p["lon"] - minlon) / (maxlon - minlon + 1e-12) * (cols - 1))
			except Exception:
				continue
			r = max(0, min(rows - 1, r))
			c = max(0, min(cols - 1, c))
			grid[r][c] += 1
			counts += 1

	return {"grid": grid, "bbox": (minlat, minlon, maxlat, maxlon), "counts": counts}


def approximate_buying_power(payload: Dict) -> int:
	"""Return a simple rule-of-thumb estimate for buying power from the payload.

	This is NOT the Interhyp calculation — it's a quick heuristic useful for
	local verification and comparison when testing the live API.
	"""
	try:
		salary = float(payload.get("salary", 0))
		monthly = float(payload.get("monthlyRate", 0))
		equity = float(payload.get("equityCash", 0))
	except Exception:
		salary = 0.0
		monthly = 0.0
		equity = 0.0
	# simple heuristic: years of salary + 20x annualized monthly payments + equity
	return int(salary * 12 * 3 + monthly * 12 * 20 + equity)


__all__ = [
	"calculate_buying_power",
	"calculate_buying_power_from_params",
	"generate_sample_properties",
	"compute_affordable_points",
	"create_affordability_heatmap",
]

