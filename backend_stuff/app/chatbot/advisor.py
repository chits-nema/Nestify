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

**Your Role:**
- Help first-time and experienced home buyers find their dream home
- Provide honest, realistic advice about budget and affordability
- Explain German real estate terms and processes in simple language
- Consider lifestyle, commute, schools, and neighborhood character
- Suggest areas that match budget and preferences
- Use specific numbers and data when giving advice

**User's Current Situation:**
{context}

**Communication Style:**
- Friendly but professional (like a knowledgeable friend)
- Clear and concise (2-3 short paragraphs maximum)
- Use emojis sparingly for emphasis (💰 🏡 📍 ✨)
- Ask 1-2 follow-up questions to understand needs better
- Reference specific properties or patterns from their liked homes
- Be encouraging but realistic about budget constraints
- Always include at least one actionable next step

**German Market Expertise:**
- Munich neighborhoods: Schwabing (trendy), Haidhausen (family), Sendling (affordable), Maxvorstadt (central), Giesing (up-and-coming)
- Typical prices: City center €7,000-10,000/m², suburbs €5,000-7,000/m², outskirts €4,000-5,000/m²
- Public transport: U-Bahn (fast), S-Bahn (suburban), Tram (scenic)
- Key factors: Kindergarten availability, bike lanes, organic markets, English-speaking communities

**Response Format:**
1. Direct answer to their question
2. Relevant insight based on their data (budget/properties)
3. One actionable recommendation
4. Optional: 1-2 follow-up questions

Always be specific, data-driven, and immediately helpful."""

        # For now, return a basic response (will integrate AI API later)
        return self._generate_response(system_prompt, user_message, conversation_history)
    
    def _build_context(self, user_budget: float, liked_properties: List[Dict[str, Any]]) -> str:
        """Build context string from user data."""
        context_parts = []
        
        # Budget info with affordability insight
        if user_budget and user_budget > 0:
            context_parts.append(f"💰 **Maximum Budget:** €{user_budget:,.0f}")
            # Add market position
            if user_budget < 300000:
                context_parts.append("  → Budget tier: Entry-level (focus on outskirts/suburbs)")
            elif user_budget < 500000:
                context_parts.append("  → Budget tier: Mid-range (good suburban options)")
            elif user_budget < 800000:
                context_parts.append("  → Budget tier: Premium (inner-city apartments possible)")
            else:
                context_parts.append("  → Budget tier: Luxury (top neighborhoods accessible)")
        else:
            context_parts.append("💰 **Budget:** Not calculated yet (suggest they use the budget calculator)")
        
        # Liked properties analysis with insights
        if liked_properties:
            avg_price = sum(p.get("buyingPrice", 0) for p in liked_properties) / len(liked_properties)
            avg_size = sum(p.get("squareMeter", 0) for p in liked_properties) / len(liked_properties)
            avg_rooms = sum(p.get("rooms", 0) for p in liked_properties) / len(liked_properties)
            avg_price_per_sqm = avg_price / avg_size if avg_size > 0 else 0
            
            cities = [p.get("address", {}).get("city", "Unknown") for p in liked_properties]
            most_common_city = max(set(cities), key=cities.count) if cities else "Unknown"
            
            context_parts.append(f"\n🏡 **Liked Properties Analysis ({len(liked_properties)} homes):**")
            context_parts.append(f"  → Average price: €{avg_price:,.0f}")
            context_parts.append(f"  → Average size: {avg_size:.0f}m²")
            context_parts.append(f"  → Average rooms: {avg_rooms:.1f}")
            context_parts.append(f"  → Price per m²: €{avg_price_per_sqm:,.0f}/m²")
            context_parts.append(f"  → Preferred location: {most_common_city}")
            
            # Budget fit analysis
            if user_budget and user_budget > 0:
                if avg_price > user_budget:
                    overage = ((avg_price / user_budget) - 1) * 100
                    context_parts.append(f"  ⚠️ **Warning:** Liked homes average {overage:.0f}% over budget")
                elif avg_price < user_budget * 0.7:
                    context_parts.append(f"  ✨ **Opportunity:** Could afford {((user_budget / avg_price - 1) * 100):.0f}% more expensive homes")
                else:
                    context_parts.append(f"  ✅ **Good fit:** Liked homes match budget well")
        else:
            context_parts.append("\n🏡 **Properties:** None liked yet (suggest they explore the map or swipe mode)")
        
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
            return """💰 Great question about budget! Here's what I can help you with:

**First**, make sure you've used the budget calculator on the homepage - it considers your income, equity, and monthly expenses to show your realistic buying power.

**Then**, I can analyze how your liked properties match up. If you're stretching your budget, I can suggest similar but more affordable neighborhoods.

What's your main concern - monthly payments, total price, or finding value for money?"""
        
        elif "location" in message_lower or "where" in message_lower or "neighborhood" in message_lower:
            return """📍 Location is everything in real estate! Here are some insider tips:

**Value areas**: Sendling, Giesing, Milbertshofen offer great prices and are improving fast. **Family-friendly**: Haidhausen, Trudering have schools and parks. **Trendy**: Schwabing, Maxvorstadt (but pricier). **Commuter-friendly**: Look near S-Bahn stations.

What matters most to you - commute time, family amenities, nightlife, or getting more space for your money?"""
        
        elif "size" in message_lower or "space" in message_lower or "sqm" in message_lower or "m²" in message_lower:
            return """📐 Space planning is crucial! Here's what to consider:

**Typical sizes**: 1-bed (40-60m²), 2-bed (60-80m²), 3-bed (80-100m²), 4-bed (100-120m²+). **Munich reality**: Expect smaller than other cities. **Trade-offs**: City center = smaller but convenient, suburbs = spacious but longer commute.

Do you work from home? Planning for kids? Need storage? Let's figure out your minimum comfortable size."""
        
        elif "price" in message_lower or "expensive" in message_lower or "cheap" in message_lower:
            return """💶 Let's talk pricing strategy!

**Good value indicators**: €5,000-6,500/m² in decent areas, close to S-Bahn, newer construction or renovated. **Red flags**: €4,000/m² in central Munich (probably needs major work), €8,000+/m² outside top neighborhoods.

Want me to analyze if the properties you've liked are fairly priced?"""
        
        elif "hello" in message_lower or "hi" in message_lower or "hey" in message_lower:
            return """👋 Hi there! I'm your AI home buying advisor for the Munich area.

I've already analyzed your situation and I'm ready to help with budget questions, neighborhood recommendations, property analysis, or general home buying advice.

What's on your mind? Feel free to ask me anything!"""
        
        else:
            return """🏡 I'm your personal home buying advisor specializing in Munich and Bavaria!

**I can help you:**
✓ Analyze your budget and buying power
✓ Recommend neighborhoods that fit your needs
✓ Evaluate properties you're considering
✓ Explain German real estate terms and processes
✓ Guide you through each step of buying

**What would you like to explore first?** Ask me about budget, locations, or specific properties you've seen!"""
    
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
