"""AI Home Buying Advisor - Provides personalized advice based on budget and preferences."""

from typing import List, Dict, Any, Optional
import os
from openai import OpenAI


class HomeAdvisor:
    """AI advisor that helps users find their dream home within budget."""
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize the advisor with optional API key for AI service."""
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY", "")
        self.client = OpenAI(api_key=self.api_key) if self.api_key else None
        
    def generate_advice(
        self, 
        user_budget: float,
        liked_properties: List[Dict[str, Any]],
        user_message: str,
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> str:
        """
        Generate personalized home buying advice.
        
        Args:
            user_budget: Maximum buying power from budget calculator
            liked_properties: List of properties user has liked
            user_message: Current user question/message
            conversation_history: Previous messages in the conversation
            
        Returns:
            AI-generated advice text
        """
        # Build context from user data
        context = self._build_context(user_budget, liked_properties)
        
        # Create system prompt
        system_prompt = f"""You are an expert real estate advisor specializing in the German housing market, particularly Munich and Bavaria.

Your Role:
- Help first-time and experienced home buyers find their dream home
- Provide honest, realistic advice about budget and affordability
- Explain German real estate terms and processes in simple language
- Consider lifestyle, commute, schools, and neighborhood character
- Suggest areas that match budget and preferences

User's Current Situation:
{context}

Communication Style:
- Friendly but professional
- Clear and concise (2-3 short paragraphs max)
- Ask follow-up questions to understand needs better
- Reference user's liked properties when relevant
- Be encouraging but realistic about budget constraints

German Market Knowledge:
- Understand Munich neighborhoods (Schwabing, Haidhausen, Sendling, etc.)
- Know typical price ranges per square meter
- Aware of commute times, public transport (U-Bahn, S-Bahn)
- Consider factors like schools, parks, shopping, nightlife

Always provide actionable advice the user can act on immediately."""

        # For now, return a basic response (will integrate AI API later)
        return self._generate_response(system_prompt, user_message, conversation_history)
    
    def _build_context(self, user_budget: float, liked_properties: List[Dict[str, Any]]) -> str:
        """Build context string from user data."""
        context_parts = []
        
        # Budget info
        if user_budget and user_budget > 0:
            context_parts.append(f"- Maximum Budget: €{user_budget:,.0f}")
        else:
            context_parts.append("- No budget set yet")
        
        # Liked properties analysis
        if liked_properties:
            avg_price = sum(p.get("buyingPrice", 0) for p in liked_properties) / len(liked_properties)
            avg_size = sum(p.get("squareMeter", 0) for p in liked_properties) / len(liked_properties)
            avg_rooms = sum(p.get("rooms", 0) for p in liked_properties) / len(liked_properties)
            
            cities = [p.get("address", {}).get("city", "Unknown") for p in liked_properties]
            most_common_city = max(set(cities), key=cities.count) if cities else "Unknown"
            
            context_parts.append(f"- Liked {len(liked_properties)} properties")
            context_parts.append(f"- Average price of liked homes: €{avg_price:,.0f}")
            context_parts.append(f"- Average size: {avg_size:.0f}m²")
            context_parts.append(f"- Average rooms: {avg_rooms:.1f}")
            context_parts.append(f"- Preferred location: {most_common_city}")
        else:
            context_parts.append("- No properties liked yet")
        
        return "\n".join(context_parts)
    
    def _generate_response(
        self, 
        system_prompt: str, 
        user_message: str,
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> str:
        """Generate AI response using OpenAI API."""
        
        # If no API key, use fallback responses
        if not self.client:
            return self._fallback_response(user_message)
        
        try:
            # Build messages for OpenAI
            messages = [
                {"role": "system", "content": system_prompt}
            ]
            
            # Add conversation history if available
            if conversation_history:
                messages.extend(conversation_history)
            
            # Add current user message
            messages.append({"role": "user", "content": user_message})
            
            # Call OpenAI API
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=messages,
                max_tokens=500,
                temperature=0.7
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            print(f"OpenAI API error: {e}")
            return self._fallback_response(user_message)
    
    def _fallback_response(self, user_message: str) -> str:
        """Fallback rule-based responses when API unavailable."""
        message_lower = user_message.lower()
        
        if "budget" in message_lower or "afford" in message_lower:
            return """Based on your budget and the properties you've liked, I can help you understand what's realistic. 

Your liked properties show your preferences, and I can suggest similar homes within your price range. Would you like me to analyze if your current selections fit your budget?"""
        
        elif "location" in message_lower or "where" in message_lower:
            return """Location is crucial! I've noticed your preferences from the homes you've liked. 

Some areas offer better value for money while others are pricier but closer to amenities. What's most important to you - proximity to work, schools, public transport, or green spaces?"""
        
        elif "size" in message_lower or "space" in message_lower:
            return """Let's talk about space! The properties you've liked give me insight into your size preferences.

Consider: Do you need space for a home office? Planning to expand your family? More space often means higher prices, so let's find the sweet spot for your needs and budget."""
        
        else:
            return """Hi! I'm your personal home buying advisor. 

I can help you:
- Understand what you can afford with your budget
- Analyze the properties you've liked
- Suggest areas and features that match your preferences
- Guide you through the home buying process

What would you like to know?"""
    
    def analyze_affordability(
        self, 
        property_price: float, 
        user_budget: float
    ) -> Dict[str, Any]:
        """Analyze if a property is affordable and provide insights."""
        
        if not user_budget or user_budget <= 0:
            return {
                "affordable": None,
                "message": "Please calculate your budget first to see affordability insights."
            }
        
        percentage = (property_price / user_budget) * 100
        difference = user_budget - property_price
        
        if property_price <= user_budget:
            if percentage <= 80:
                status = "comfortably_affordable"
                message = f"This property is well within your budget! You'd have €{difference:,.0f} cushion for renovations or emergencies."
            elif percentage <= 95:
                status = "affordable"
                message = f"This property fits your budget with €{difference:,.0f} to spare."
            else:
                status = "tight_but_affordable"
                message = f"This property is at the top of your budget. Only €{difference:,.0f} remaining."
        else:
            status = "over_budget"
            message = f"This property exceeds your budget by €{abs(difference):,.0f} ({percentage - 100:.1f}% over)."
        
        return {
            "affordable": property_price <= user_budget,
            "status": status,
            "percentage": round(percentage, 1),
            "difference": difference,
            "message": message
        }
