# 🤖 Nestify Chatbot Integration

## Overview
The Nestify chatbot is an AI-powered home buying advisor that provides personalized guidance based on user budget, liked properties, and preferences.

## Files Structure

```
frontend_stuff/
├── chatbot.js           # Main chatbot frontend logic
├── test_chatbot.html    # Standalone test page
├── index.html           # Updated with chatbot script
└── styles.css           # Updated with chatbot styles

backend_stuff/app/chatbot/
├── advisor.py           # AI advisor logic
└── router.py            # FastAPI endpoints
```

## Features

### 1. **Floating Chat Widget**
- Always accessible via floating button in bottom-right corner
- Smooth animations and responsive design
- Mobile-friendly interface

### 2. **Context-Aware Responses**
- Automatically includes user's budget from calculator
- References liked properties from swipe mode
- Maintains conversation history

### 3. **Smart Advice**
- Personalized recommendations based on preferences
- Budget analysis and affordability checks
- Neighborhood insights and comparisons
- German real estate market expertise

## API Endpoints

### POST `/chatbot/chat`
Chat with the AI advisor

**Request:**
```json
{
  "message": "What can I afford with my budget?",
  "user_budget": 500000,
  "liked_properties": [...],
  "conversation_history": [...]
}
```

**Response:**
```json
{
  "success": true,
  "response": "Based on your budget of €500,000...",
  "timestamp": null
}
```

### POST `/chatbot/affordability`
Check if a property is affordable

**Request:**
```json
{
  "property_price": 450000,
  "user_budget": 500000
}
```

**Response:**
```json
{
  "success": true,
  "analysis": {
    "affordable": true,
    "status": "affordable",
    "percentage": 90.0,
    "difference": 50000,
    "message": "This property fits your budget with €50,000 to spare."
  }
}
```

### GET `/chatbot/health`
Health check endpoint

## Usage

### 1. Start Backend
```bash
cd backend_stuff
uvicorn app.main:app --reload
```

### 2. Open Frontend
Open `index.html` or `test_chatbot.html` in your browser

### 3. Interact with Chatbot
- Click the 💬 button in bottom-right corner
- Ask questions about home buying
- Get personalized advice based on your data

## Example Conversations

### Budget Questions
**User:** "What can I afford with my budget?"
**Bot:** Analyzes budget and liked properties to provide realistic recommendations

### Location Advice
**User:** "Which neighborhoods should I consider?"
**Bot:** Suggests areas based on budget, preferences, and commute needs

### Property Analysis
**User:** "Is this property a good deal?"
**Bot:** Evaluates price per square meter, location value, and budget fit

## Customization

### Modify AI Behavior
Edit `backend_stuff/app/chatbot/advisor.py`:
- Update `system_prompt` for different personality
- Modify `_build_context()` to include more user data
- Enhance `_fallback_response()` for better offline experience

### Style Changes
Edit chatbot styles in `frontend_stuff/styles.css`:
- Search for `/* Chatbot Styles */` section
- Customize colors, sizes, animations

### Add Features
In `frontend_stuff/chatbot.js`:
- Add quick reply buttons
- Include property cards in chat
- Add voice input support

## OpenAI Integration

### Setup API Key
```bash
# Set environment variable
export OPENAI_API_KEY="your-key-here"

# Or in .env file
OPENAI_API_KEY=your-key-here
```

### API Key Priority
1. Constructor parameter
2. Environment variable
3. Fallback responses (no AI)

## Testing

### Manual Testing
1. Open `test_chatbot.html`
2. Test with mock data (budget €500,000, 2 liked properties)
3. Try various questions

### Backend Testing
```bash
# Test chat endpoint
curl -X POST http://127.0.0.1:8000/chatbot/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"Hello", "user_budget":500000}'

# Test affordability
curl -X POST http://127.0.0.1:8000/chatbot/affordability \
  -H "Content-Type: application/json" \
  -d '{"property_price":450000, "user_budget":500000}'

# Health check
curl http://127.0.0.1:8000/chatbot/health
```

## Troubleshooting

### Chatbot Button Not Appearing
- Check that `chatbot.js` is loaded in HTML
- Verify CSS is loaded correctly
- Check browser console for errors

### No API Response
- Ensure backend is running on port 8000
- Check CORS settings in backend
- Verify API endpoint URLs in `chatbot.js`

### OpenAI Errors
- Verify API key is set correctly
- Check OpenAI account has credits
- Review error messages in backend logs

## Mobile Responsiveness
- Full-screen chat on mobile devices
- Touch-optimized controls
- Responsive text input

## Future Enhancements
- [ ] Property image sharing in chat
- [ ] Quick reply buttons (e.g., "Check my budget", "Show recommendations")
- [ ] Voice input/output support
- [ ] Multi-language support (German/English)
- [ ] Chat history persistence
- [ ] Property comparison in chat
- [ ] Appointment scheduling with agents
- [ ] Mortgage calculator integration

## Browser Compatibility
- Chrome/Edge: ✅ Full support
- Firefox: ✅ Full support
- Safari: ✅ Full support
- Mobile browsers: ✅ Responsive design
