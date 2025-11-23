from __future__ import annotations

from fastapi import APIRouter, Body, HTTPException
from typing import Any, Dict, Optional
import os

from .pinterest_backend import PinterestPropertyAnalyzer

router = APIRouter(prefix="/pinterest", tags=["pinterest"])

# Optional API keys
HF_API_KEY = os.environ.get("HF_API_KEY", "")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
analyzer = PinterestPropertyAnalyzer(HF_API_KEY, OPENAI_API_KEY)


def _convert_to_rss_url(url: str) -> str:
    url = url.rstrip("/")
    if url.endswith('.rss'):
        return url
    if 'pinterest.com' in url and not url.endswith('.rss'):
        return f"{url}.rss"
    raise ValueError("Invalid Pinterest URL. Please provide a valid Pinterest board URL.")


@router.post("/analyze")
async def analyze_board(body: Dict[str, Any] = Body(...)) -> Dict[str, Any]:
    board_url = body.get('board_url')
    city = body.get('city')
    if not board_url or not city:
        raise HTTPException(status_code=400, detail="board_url and city are required")
    try:
        rss_url = _convert_to_rss_url(board_url)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    try:
        result = analyzer.process_pinterest_board(rss_url, {'city': city})
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))

    return {
        'success': True,
        'data': {
            'board_context': result.get('board_context', {}),
            'feature_scores': result.get('feature_scores', {}),
            'properties': result.get('properties', []),
            'total_properties': result.get('total_properties', 0),
            'search_params': {k: v for k, v in result.get('search_payload', {}).items() if k != '_metadata'}
        }
    }


@router.get('/health')
async def pinterest_health():
    return {'status': 'ok', 'hf_api_configured': bool(HF_API_KEY)}
