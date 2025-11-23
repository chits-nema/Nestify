"""FastAPI router for AI chatbot advisor."""

from fastapi import APIRouter, Body, HTTPException
from typing import List, Dict, Any, Optional
from pydantic import BaseModel

from .advisor import HomeAdvisor

router = APIRouter(prefix="/chatbot", tags=["chatbot"])

# Initialize advisor
advisor = HomeAdvisor()


class ChatRequest(BaseModel):
    """Chat message request from user."""
    message: str
    user_budget: Optional[float] = None
    liked_properties: Optional[List[Dict[str, Any]]] = None
    conversation_history: Optional[List[Dict[str, str]]] = None


class AffordabilityRequest(BaseModel):
    """Request to check if a property is affordable."""
    property_price: float
    user_budget: float


@router.post("/chat")
async def chat(request: ChatRequest) -> Dict[str, Any]:
    """
    Chat with the AI home buying advisor.
    
    Provide your budget, liked properties, and question to get personalized advice.
    """
    try:
        advice = advisor.generate_advice(
            user_budget=request.user_budget or 0,
            liked_properties=request.liked_properties or [],
            user_message=request.message,
            conversation_history=request.conversation_history or []
        )
        
        return {
            "success": True,
            "response": advice,
            "timestamp": None  # Could add timestamp here
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/affordability")
async def check_affordability(request: AffordabilityRequest) -> Dict[str, Any]:
    """
    Check if a property is affordable within user's budget.
    
    Returns detailed affordability analysis.
    """
    try:
        analysis = advisor.analyze_affordability(
            property_price=request.property_price,
            user_budget=request.user_budget
        )
        
        return {
            "success": True,
            "analysis": analysis
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def chatbot_health():
    """Health check for chatbot service."""
    return {
        "status": "ok",
        "service": "home-advisor-chatbot"
    }
