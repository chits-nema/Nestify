# 🎨 Pinterest Style Analyzer

## Overview
The Pinterest Style Analyzer uses AI to analyze your Pinterest board and find real properties that match your aesthetic preferences. It's like having a personal real estate stylist!

## How It Works

### 1. **Share Your Board** 📌
- User provides a Pinterest board URL (e.g., home decor, interior design)
- Selects target city for property search

### 2. **AI Analysis** 🤖
The backend analyzes:
- **Space Type**: Balcony, Garden, Outdoor spaces
- **Living Type**: Apartment, House, Studio
- **Style Preferences**: Modern, Rustic, Vintage, Minimalist
- **Board Context**: Overall aesthetic and focus

### 3. **Smart Matching** 🏡
Properties are scored based on:
- Physical features (balcony, garden, plot area)
- Style keywords in property descriptions
- Construction year (for vintage/rustic preferences)
- Visual aesthetics

## Features

### Frontend (`pinterest.html`, `pinterest.js`)

#### User Experience
- **3-Step Wizard**: Input → Analysis → Matches
- **Visual Style Profile**: See your detected preferences with icons and percentages
- **Board Context Card**: Understand what the AI sees in your board
- **Property Cards**: Rich cards with images, stats, and match reasons
- **Match Scoring**: Properties ranked by style compatibility

#### UI Components
- Clean, modern interface with purple gradient theme
- Animated loading states
- Responsive grid layouts
- Match badges (Excellent, Good, Fair, Low)
- Property stats (price, size, rooms)
- "Why this matches" explanations

### Backend (`pinterest_backend.py`, `router.py`)

#### Analysis Pipeline
1. **RSS Feed Parsing**: Extracts pins from Pinterest board
2. **Keyword Detection**: Identifies style features from titles/descriptions
3. **Context Analysis**: Determines primary focus and preferences
4. **Score Calculation**: Weights features based on board context
5. **Property Search**: Queries ThinkImmo API with detected preferences
6. **Smart Filtering**: Ranks properties by match score

#### Key Algorithms
- **Context-Aware Scoring**: Adjusts feature weights based on board theme
- **Keyword Matching**: Comprehensive dictionaries for German & English
- **Property Filtering**: Post-search ranking with detailed reasons

## API Endpoints

### POST `/pinterest/analyze`

Analyze a Pinterest board and find matching properties.

**Request:**
```json
{
  "board_url": "https://www.pinterest.com/username/board-name/",
  "city": "München"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "board_context": {
      "primary_focus": "outdoor_living",
      "space_type": "balcony_focus",
      "living_type": "apartment"
    },
    "feature_scores": {
      "Balcony": 0.85,
      "Modern": 0.62,
      "Apartment": 0.78
    },
    "properties": [...],
    "total_properties": 15,
    "search_params": {...}
  }
}
```

### GET `/pinterest/health`

Health check endpoint.

**Response:**
```json
{
  "status": "ok",
  "hf_api_configured": true
}
```

## Setup & Usage

### 1. Backend Setup

Ensure backend is running:
```bash
cd backend_stuff
uvicorn app.main:app --reload
```

Optional: Set Hugging Face API key for advanced analysis:
```bash
export HF_API_KEY="your-key-here"
```

### 2. Frontend Access

Open `pinterest.html` in your browser:
```bash
cd frontend_stuff
python -m http.server 8080
```

Visit: `http://localhost:8080/pinterest.html`

### 3. Using the Tool

**Step 1 - Get Pinterest Board URL:**
1. Go to Pinterest
2. Open a board (yours or someone else's)
3. Copy the URL from browser address bar
4. Examples:
   - `https://www.pinterest.com/username/home-decor/`
   - `https://www.pinterest.com/username/apartment-living/`

**Step 2 - Paste & Analyze:**
1. Paste URL into input field
2. Select target city (München, Berlin, etc.)
3. Click "Analyze My Style" ✨

**Step 3 - Review Results:**
- See your style profile breakdown
- View matched properties ranked by compatibility
- Read "Why this matches" for each property

## Feature Detection

### Space Features
- **Balcony**: Small outdoor space, typical for apartments
- **Garden**: Larger outdoor space, typical for houses
- **Terrace**: Medium outdoor space
- **Patio**: Ground-level outdoor area

### Living Types
- **Apartment**: Urban, multi-unit, city living
- **House**: Standalone, suburban, more space
- **Studio**: Compact, single-room living

### Style Categories
- **Modern**: Clean lines, minimalist, contemporary
- **Rustic**: Wood, farmhouse, cozy, natural
- **Vintage**: Classic, antique, traditional, historic

## Example Boards

### Good Pinterest Boards to Try:

**Apartment Living:**
- Small balcony decor boards
- Cozy apartment interior boards
- Urban living inspiration

**House Hunting:**
- Garden design boards
- Exterior home design boards
- Backyard inspiration

**Style-Specific:**
- Modern minimalist homes
- Rustic farmhouse interiors
- Vintage cottage aesthetics

## Technical Details

### URL Handling
The backend automatically converts Pinterest URLs to RSS format:
- Input: `https://www.pinterest.com/user/board/`
- Converted: `https://www.pinterest.com/user/board.rss`

### Scoring Algorithm
```python
# Base feature score from keyword frequency
base_score = keyword_matches / total_pins

# Context adjustment
if board_focuses_on_balconies:
    balcony_score *= 1.5

# Property matching
match_score = 0
if property.has_balcony and user_wants_balcony:
    match_score += 5
if style_keywords_in_title:
    match_score += keyword_matches * 2
```

### Property Ranking
Properties sorted by:
1. **Feature Match**: Has requested features (balcony, garden)
2. **Style Match**: Keywords in title match preferences
3. **Context Fit**: Aligns with board's primary focus

## Customization

### Add New Style Categories

Edit `pinterest_backend.py`:
```python
self.feature_keywords = {
    'YourStyle': [
        'keyword1', 'keyword2', 'keyword3'
    ]
}
```

### Adjust Scoring Weights

Modify `_calculate_feature_scores()`:
```python
if context['primary_focus'] == 'your_focus':
    scores['YourFeature'] *= 2.0  # Boost this feature
```

### Change UI Colors

Edit `pinterest.css`:
```css
.feature-card {
    background: your-color;
}
```

## Troubleshooting

### "Invalid Pinterest URL"
- Ensure URL contains "pinterest.com"
- Use board URLs, not profile URLs
- Format: `pinterest.com/username/board-name/`

### "No properties found"
- Try a board with more pins (15+)
- Make sure board has clear home/decor theme
- Try a different city with more listings

### "No distinct features detected"
- Board may be too mixed/varied
- Use boards focused on specific styles
- Add more pins to the board

### Backend Errors
- Check backend is running: `curl http://127.0.0.1:8000/pinterest/health`
- Verify RSS feed accessible: Try opening `.rss` URL in browser
- Check logs for detailed errors

## Performance

### Speed
- RSS parsing: < 2 seconds
- Feature analysis: < 1 second
- Property search: 2-5 seconds
- **Total**: Usually 3-8 seconds

### Accuracy
- Works best with focused boards (15+ pins)
- Clear themes = better matching
- German keywords supported for local market

## Privacy & Data

- **No Pinterest Login Required**: Uses public RSS feeds
- **No Data Stored**: Analysis happens in real-time
- **No Personal Info**: Only board URL processed
- **Public Boards Only**: Private boards not accessible

## Future Enhancements

- [ ] Image analysis using computer vision
- [ ] Color palette extraction
- [ ] Room-by-room style detection
- [ ] Save favorite style profiles
- [ ] Compare multiple boards
- [ ] Export property matches
- [ ] Social sharing of style profiles
- [ ] Integration with budget calculator

## Browser Support

- ✅ Chrome/Edge (recommended)
- ✅ Firefox
- ✅ Safari
- ✅ Mobile browsers (responsive design)

## Credits

- **Pinterest RSS**: Public RSS feeds for board data
- **ThinkImmo API**: Property search integration
- **AI Analysis**: Keyword-based feature detection
- **Design**: Custom responsive interface

---

**Enjoy finding homes that match your style!** 🎨🏡
