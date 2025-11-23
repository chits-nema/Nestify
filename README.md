# 🏡 Nestify

> **Real estate for the generation that can't adult** - Making home hunting less traumatic, one aesthetic at a time.

Your Pinterest board knows you better than Zillow ever will. Nestify is the Gen Z/Millennial real estate platform that actually gets your vibe.

## 🎯 The Problem

You're drowning in student debt, your savings account is crying, and every property listing looks like it was designed in 2003. Meanwhile, you've spent 47 hours curating the perfect cottagecore/dark academia Pinterest board but somehow that doesn't translate to "three-bedroom apartment with good natural lighting."

**We fixed that.**

## ✨ Features

### 📌 Pinterest-Powered Property Matching
Drop your Pinterest board URL and watch AI magic happen. Our system analyzes your aesthetic preferences (cottagecore? modern minimalist? dark moody vibes?) and matches you with properties that actually fit your style. Because if you have to adult, at least make it aesthetic.

### 🧮 Budget Calculator That Doesn't Judge
Calculate what you can actually afford without the existential dread. Factors in:
- Buying price (the scary number)
- Notary fees (the "wait, what?" tax)
- Real estate agent commission (the "seriously?" fee)
- Property transfer tax (because why not)

Get real numbers, not false hope.

### 🗺️ Heat Map of Dreams (and Nightmares)
Visual affordability heat map because reading spreadsheets is so 2015. See where properties are:
- 💚 Affordable (you can eat AND pay rent)
- 💛 Stretch goal (ramen diet engaged)
- 🔴 LOL no (maybe in another life)

### 🤖 AI Advisor That Gets It
Chat with our AI that understands your budget constraints, lifestyle needs, and the fact that "well-lit" doesn't mean "bright enough to perform surgery." Ask anything:
- "Can I afford a place with a balcony in Munich?"
- "What neighborhoods won't bankrupt me?"
- "Is cottagecore realistic on a junior dev salary?"

### 🔥 Tinder-Style Swipe Mode
Because apparently, we swipe for everything now. Swipe right on properties you vibe with, left on the ones that give you anxiety. It's like dating, but the commitment is bigger and scarier.

## 🚀 Tech Stack

**Frontend:**
- Vanilla JS, HTML5, CSS3 (we kept it simple because hackathon deadlines are real)
- Inter font family (typography that slaps)
- Font Awesome icons (because we're fancy like that)

**Backend:**
- Python FastAPI (fast and async, unlike the housing market)
- OpenAI GPT-4o-mini (for the smart stuff)
- ThinkImmo API integration (actual real estate data)
- Pinterest RSS feed parsing (Pinterest board → property preferences pipeline)

**Features:**
- Semantic analysis with keyword matching + AI enhancement
- German property title filtering (because we're targeting the German market)
- Board context interpretation (house vs apartment, garden vs balcony)
- Construction year filtering (vintage lovers, we got you)
- Confidence scoring with blended AI + keyword analysis

## 🎮 Getting Started

### Prerequisites
```bash
# The usual suspects
Node.js (optional, for frontend dev)
Python 3.8+
pip
A Pinterest board full of home inspiration
Unrealistic housing expectations (optional but likely)
```

### Installation

1. **Clone the repo**
```bash
git clone https://github.com/chits-nema/Nestify.git
cd Nestify
```

2. **Set up the backend**
```bash
cd backend_stuff
pip install -r requirements.txt
```

3. **Configure environment variables**
```bash
# Create a .env file or set these in your shell
export OPENAI_API_KEY="your-openai-key-here"
export HF_API_KEY="your-huggingface-key-here"  # optional
```

4. **Start the backend**
```bash
uvicorn app.main:app --reload --port 8000
```

5. **Open the frontend**
```bash
cd frontend_stuff
# Just open index.html in your browser
# Or use a simple server:
python -m http.server 3000
```

Navigate to `http://localhost:3000` and start adulting (kind of).

## 📁 Project Structure

```
Nestify/
├── frontend_stuff/
│   ├── index.html              # Landing page
│   ├── styles.css              # Main stylesheet (blue-white-green company colors)
│   ├── script.js               # Budget calculator logic
│   ├── swipe.js                # Tinder-style swipe mode
│   ├── pinterest.js            # Pinterest analyzer frontend
│   ├── pinterest.css           # Pinterest-specific styling
│   ├── chatbot.js              # AI advisor chat interface
│   └── budget.js               # Budget calculation utilities
│
├── backend_stuff/
│   ├── app/
│   │   ├── main.py             # FastAPI app entry point
│   │   ├── config.py           # Configuration settings
│   │   ├── models.py           # Data models
│   │   ├── chatbot/            # AI advisor backend
│   │   │   ├── advisor.py      # OpenAI chat logic
│   │   │   └── router.py       # Chat API endpoints
│   │   ├── heat_map/           # Heat map generation
│   │   │   ├── heatmap_backend.py
│   │   │   └── router.py
│   │   └── pinterest/          # Pinterest analyzer
│   │       ├── pinterest_backend.py  # Core analysis logic
│   │       └── router.py       # Pinterest API endpoints
│   └── requirements.txt        # Python dependencies
│
├── README.md                   # You are here
├── ALGORITHM_IMPROVEMENTS.md   # Because we had ideas at 3am
└── SWIPE_SYSTEM.md            # Documentation for the swipe feature
```

## 🎨 Color Palette

We went full corporate branding mode:
- **Primary Blue**: `#2E7D99` (trustworthy professional vibes)
- **Secondary Green**: `#4CAF50` (money green but make it friendly)
- **Light Green**: `#81C784`, `#E8F5E9` (soft backgrounds)
- **Accents**: Teal, cyan, and cool whites

No warm beiges or terracotta allowed. We had a whole journey about this.

## 🏗️ How It Works

### Pinterest → Property Pipeline

1. **User drops Pinterest board URL** (the easy part)
2. **Backend parses RSS feed** (Pinterest's gift to developers)
3. **AI analyzes pins for aesthetic preferences:**
   - Keyword matching (200+ keywords across 10 categories)
   - Theme detection (cottagecore, farmhouse, modern, dark academia)
   - Feature confidence scoring (house vs apartment, balcony vs garden)
4. **OpenAI enhances understanding** (semantic analysis FTW)
5. **ThinkImmo API query** (actual property data)
6. **German keyword filtering** (charmant, altbau, neubau, etc.)
7. **Property scoring & ranking:**
   - Construction year matching
   - Property type alignment
   - Garden/balcony preferences
   - Style keyword matching
8. **Frontend displays clickable results** (tap to see listings)

### Budget Calculator Math

```
Total Cost = Buying Price 
           + Notary Fees (1.5% + VAT)
           + Real Estate Commission (7.14% incl. VAT)
           + Property Transfer Tax (3.5% - 6.5% depending on state)
```

Yeah, it hurts. We know.

## 🤝 Contributing

This was built for a hackathon in record time with questionable amounts of caffeine. PRs welcome, judgment not welcome.

## 📜 License

MIT License - Use it, fork it, make it better. Just don't sell it to a soulless real estate company.

## 🎤 The Team

Built by developers who are also trying to figure out this whole "homeownership" thing. We feel your pain.

## 🙏 Acknowledgments

- Pinterest for the RSS feeds
- OpenAI for making us look smarter than we are
- ThinkImmo API for the actual property data
- Coffee, for existing
- Stack Overflow, obviously
- Every millennial/Gen Z-er who's ever said "I'll never afford a house"

## 🐛 Known Issues

- Sometimes the AI is too real about your budget limitations
- The swipe feature might cause decision paralysis
- Pinterest boards with 500+ pins take a minute (it's analyzing your entire personality)
- We're all still broke after building this

---

**Built with 💚 (and mild housing market anxiety) for the generation that deserves better real estate tools.**

*Now go find your dream home. Or at least a place with good WiFi and natural lighting.*
- Location
- Number of bedrooms and bathrooms
- Square footage
- Favorite toggle button

### Responsive Design
The website is fully responsive and adapts to different screen sizes for optimal viewing on all devices.

## Technologies Used

- HTML5
- CSS3 (with modern features like Grid, Flexbox, and animations)
- JavaScript (ES6+)
- No external dependencies - vanilla JavaScript only!

## License

This project is open source and available for personal and educational use.