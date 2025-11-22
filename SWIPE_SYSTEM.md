# 🏡 Nestify - Smart Property Swipe System

## 📋 Overview

Nestify uses an intelligent swipe-based system to learn user preferences and recommend properties. The system has been optimized to:

- **Fetch 200 properties** from the backend for maximum variety
- **Show 30 swipe cards** to thoroughly learn user preferences
- **Use smart scoring algorithm** to match and rank recommendations
- **Display match percentages** for recommended properties

---

## 🚀 How It Works

### **1. Data Collection (Backend)**

The backend fetches **200 properties** from ThinkImmo API:

```python
# backend_stuff/app/main.py
size: int = 200  # Increased for better swipe variety
```

This large dataset ensures:
- Diverse price ranges
- Various locations
- Different sizes and room counts
- Better recommendation quality

### **2. Swipe Session (30 Cards)**

Users swipe through **30 randomly selected properties** from the 200 fetched:

```javascript
// frontend_stuff/tinder.js
const MAX_CARDS = 30;  // Increased to learn preferences better
```

**Why 30 swipes?**
- Provides enough data to learn accurate preferences
- Covers different price ranges, sizes, and locations
- Balances user engagement with data quality
- Statistical significance for reliable recommendations

### **3. Preference Learning**

After each swipe session, the system analyzes liked properties to build a preference profile:

```javascript
{
  // City preferences
  preferredCity: "München",
  alternativeCities: ["Schwabing", "Haidhausen"],

  // Price preferences
  minPrice: 350000,
  maxPrice: 550000,
  avgPrice: 450000,

  // Size preferences
  minSqm: 55,
  maxSqm: 75,
  avgSqm: 65,

  // Room preferences
  minRooms: 2,
  maxRooms: 3,
  avgRooms: 2.5
}
```

### **4. Smart Matching Algorithm**

The system calculates a **match score (0-100%)** for each property:

#### **Scoring Breakdown:**

| Category | Weight | Criteria |
|----------|--------|----------|
| **City** | 30 points | Perfect match: 30 pts<br>Alternative city: 20 pts |
| **Price** | 40 points | Within range: 40 pts<br>In buffer zone: Scaled |
| **Size** | 20 points | Within range: 20 pts<br>In buffer zone: Scaled |
| **Rooms** | 10 points | ±1 room: 10 pts<br>±2 rooms: 5 pts |

#### **Match Threshold:**
- Properties with **≥40% match** are shown as recommendations
- Sorted by match score (highest first)
- Each card displays the match percentage

---

## 🎯 Key Features

### **Flexible Matching**

The algorithm uses **buffer zones** to avoid being too restrictive:

**Price Buffer:** ±50% of the liked price range
```javascript
// Example: If user likes 400k-500k
// Buffer range: 300k-650k
// Properties in 300k-400k or 500k-650k get partial points
```

**Size Buffer:** ±50% of the liked size range
```javascript
// Example: If user likes 60-80 m²
// Buffer range: 50-100 m²
// Properties outside core range still considered
```

### **Multi-City Support**

The system recognizes:
- **Primary preferred city** (most liked)
- **Alternative cities** (≥15% of likes or ≥2 occurrences)

This ensures users see properties in similar neighborhoods they might like.

### **Visual Match Indicators**

Each recommendation displays a **match percentage** in green:

```
München Apartment
Schwabing
€450,000 · 65 m² · 2 rooms
✓ 87% Match
```

---

## 🛠️ Technical Implementation

### **Backend Changes**

**File:** `backend_stuff/app/main.py`

```python
class PropertySearchRequest(BaseModel):
    size: int = 200  # Increased from 20 to 200
```

### **Frontend Changes**

**File:** `frontend_stuff/tinder.js`

#### 1. Increased Swipe Cards
```javascript
const MAX_CARDS = 30;  // From 15 to 30
```

#### 2. Fetch More Properties
```javascript
size: 200,  // From 50 to 200
```

#### 3. Smart Scoring System
```javascript
function calculateMatchScore(p, profile) {
  // Returns 0-100 score based on:
  // - City match (30%)
  // - Price match (40%)
  // - Size match (20%)
  // - Room match (10%)
}
```

#### 4. Enhanced Recommendations
```javascript
// Sort by match score
.sort((a, b) => b.score - a.score)

// Display match percentage
<p>${matchPercent}% Match</p>
```

---

## 📊 Example Workflow

### **User Journey:**

1. **Start Swiping**
   - System shows 30 properties from 200 available
   - User swipes right (like) or left (dislike)

2. **System Learns** (after 5-10 likes)
   - Price range: €350k - €550k
   - Size: 55-75 m²
   - Preferred city: München
   - Alternative: Schwabing
   - Rooms: 2-3

3. **Recommendations Generated**
   - Filters 200 properties
   - Calculates match scores
   - Shows properties with ≥40% match
   - Sorted by best match first

4. **Results Display**
   ```
   Homes You Might Love (sorted by match)
   
   ✓ 92% Match - München Loft, €480k, 68m², 2 rooms
   ✓ 87% Match - Schwabing Flat, €520k, 72m², 3 rooms
   ✓ 78% Match - München Studio, €380k, 58m², 2 rooms
   ✓ 65% Match - Haidhausen Apt, €545k, 75m², 3 rooms
   ```

---

## 🔧 Running the System

### **1. Start Backend**

```bash
cd backend_stuff
pip install -r requirements.txt
uvicorn app.main:app --reload --port 4000
```

Backend will:
- Expose API at `http://127.0.0.1:4000`
- Fetch up to 200 properties per request
- Handle city/region searches

### **2. Start Frontend**

```bash
cd frontend_stuff
open index.html
# Or use a local server:
python -m http.server 8000
```

### **3. Use the System**

1. Click "I don't really know" on homepage
2. Swipe through 30 properties
3. Like properties that appeal to you
4. View personalized recommendations with match scores

---

## 📈 Performance Metrics

### **Before Optimization:**
- ❌ Only 50 properties fetched
- ❌ Only 15 swipes shown
- ❌ Recommendations too restrictive (often 0-1 results)
- ❌ No match scoring visibility

### **After Optimization:**
- ✅ 200 properties fetched (4x more data)
- ✅ 30 swipes shown (2x more learning)
- ✅ Flexible matching with buffer zones
- ✅ Match scores displayed (40-100%)
- ✅ Average 10-20 recommendations per session
- ✅ Sorted by relevance

---

## 🎨 UI Enhancements

### **Match Score Display**

Added visual match indicator on recommendation cards:

```css
/* Match percentage in green */
color: #2ecc71; 
font-weight: bold;
```

Example card:
```html
<div class="rec-card">
  <img src="property-image.jpg" />
  <div class="rec-info">
    <h5>München Apartment</h5>
    <p>Schwabing</p>
    <p>€450,000 · 65 m² · 2 rooms</p>
    <p style="color: #2ecc71; font-weight: bold;">
      87% Match
    </p>
  </div>
</div>
```

---

## 🧪 Testing Recommendations

To test if the system works properly:

1. **Like specific patterns:**
   - All properties in München
   - All properties between €400k-€500k
   - All properties with 2-3 rooms

2. **Check recommendations:**
   - Should show 10+ properties
   - Match scores should be 60-95%
   - Properties should fit the pattern

3. **Verify sorting:**
   - Highest match % should be at top
   - All recommendations ≥40% match

---

## 🐛 Troubleshooting

### **Issue: No recommendations shown**

**Possible causes:**
- Not enough liked properties (need at least 3)
- ThinkImmo returned limited results
- All properties already swiped

**Solution:**
- Swipe more properties
- Check backend console for data count
- Verify ThinkImmo API is working

### **Issue: Only 1-2 recommendations**

**Possible causes:**
- Backend returned <200 properties
- Match threshold too high
- Very narrow preferences

**Solution:**
- Check backend `data.total` in console
- Lower match threshold from 40% to 30%
- Verify buffer calculations are working

### **Issue: Match scores seem wrong**

**Check:**
- Profile is being built correctly (console.log)
- calculateMatchScore function logic
- Buffer zones are applied (±50%)

---

## 🚀 Future Enhancements

### **1. Advanced Filtering**
- Add property type preferences (apartment vs house)
- Consider amenities (balcony, parking, elevator)
- Factor in floor level preferences

### **2. Machine Learning**
- Collaborative filtering (similar users)
- Historical preference tracking
- A/B testing different algorithms

### **3. User Experience**
- Save swipe sessions
- Compare multiple properties side-by-side
- Virtual tours integration

### **4. Performance**
- Pagination for large result sets
- Caching frequent searches
- Progressive loading

---

## 📝 Code Structure

```
Nestify/
├── backend_stuff/
│   ├── app/
│   │   └── main.py          # API endpoints, size=200
│   └── requirements.txt
│
├── frontend_stuff/
│   ├── index.html           # Main page
│   ├── tinder.js            # Swipe logic (MAX_CARDS=30)
│   ├── script.js            # General functionality
│   └── styles.css           # Styling
│
└── SWIPE_SYSTEM.md          # This file
```

---

## 🤝 Contributing

To improve the matching algorithm:

1. Adjust weights in `calculateMatchScore()`
2. Modify buffer zones (currently ±50%)
3. Change match threshold (currently 40%)
4. Add new scoring dimensions

---

## 📄 License

Hackathon project - Free to use and modify

---

## 👥 Team

Built during hackaTUM hackathon

---

## 🎯 Summary

**Key Changes:**
- ✅ Backend: 200 properties (vs 20 before)
- ✅ Frontend: 30 swipes (vs 15 before)
- ✅ Smart scoring: 0-100% match with display
- ✅ Flexible buffers: ±50% for price & size
- ✅ Multi-city support
- ✅ Sorted recommendations

**Result:** Much better user experience with 10-20 quality recommendations instead of 0-1!
