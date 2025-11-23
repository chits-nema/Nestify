# pinterest_analyzer.py - FIXED with better contextual understanding

import feedparser
import requests
from typing import List, Dict
import re
from collections import defaultdict
import json
import os
from openai import OpenAI

class PinterestPropertyAnalyzer:
    def __init__(self, hf_api_key: str = None, openai_api_key: str = None):
        self.hf_api_key = hf_api_key
        self.headers = {"Authorization": f"Bearer {hf_api_key}"} if hf_api_key else {}
        self.openai_api_key = openai_api_key or os.environ.get("OPENAI_API_KEY")
        self.openai_client = OpenAI(api_key=self.openai_api_key) if self.openai_api_key else None
        
        # MORE SPECIFIC keywords with better aesthetic detection
        self.feature_keywords = {
            # APARTMENTS - very specific urban living keywords
            'Apartment': [
                'apartment', 'flat', 'condo', 'loft', 'studio', 'wohnung',
                'city living', 'urban', 'downtown', 'high rise', 'apartment balcony',
                'tiny balcony', 'small balcony', 'apt', 'rental', 'renter',
                'cozy balcony', 'balcony decor', 'patio decorating'
            ],
            
            # HOUSES - expanded with cottage/farmhouse indicators
            'House': [
                'house', 'home', 'villa', 'cottage', 'farmhouse', 'cabin', 'colonial',
                'standalone', 'detached', 'single family', 'driveway', 'front yard',
                'backyard', 'yard', 'exterior', 'facade', 'porch', 'veranda'
            ],
            
            # BALCONY - small urban outdoor space
            'Balcony': [
                'balcony', 'balkon', 'terrace', 'patio', 'small balcony',
                'tiny balcony', 'apartment balcony', 'city balcony', 'urban balcony',
                'balcony decor', 'balcony garden', 'balcony furniture', 'balcony setup',
                'cozy balcony', 'balcony with plants', 'balcony view'
            ],
            
            # GARDEN - large outdoor space (distinct from balcony)
            'Garden': [
                'garden', 'backyard', 'yard', 'lawn', 'landscaping', 'outdoor space',
                'cottage garden', 'wild garden', 'english garden', 'garden path',
                'flower garden', 'herb garden', 'garden bed', 'garden border'
            ],
            
            # STYLE FEATURES - greatly expanded
            'Modern': [
                'modern', 'contemporary', 'minimalist', 'sleek', 'clean', 'industrial',
                'scandinavian', 'bauhaus', 'mid-century', 'minimalism', 'nordic'
            ],
            
            'Rustic': [
                'rustic', 'farmhouse', 'country', 'cottage', 'cozy', 'cabin', 'barn',
                'cottagecore', 'farmcore', 'countryside', 'rural', 'provincial',
                'stone', 'brick', 'timber', 'beam', 'reclaimed', 'weathered',
                'worn', 'patina', 'aged', 'natural', 'organic', 'earthy'
            ],
            
            'Vintage': [
                'vintage', 'antique', 'retro', 'classic', 'traditional', 'victorian',
                'historic', 'old', 'heritage', 'period', 'timeless', 'nostalgic',
                '16th century', '17th century', '18th century', 'colonial', 'old-fashioned'
            ],
            
            # NEW: Dark/Moody aesthetic
            'Dark': [
                'dark', 'moody', 'dramatic', 'gothic', 'black', 'charcoal', 'noir',
                'dark aesthetic', 'dark interior', 'dark cottagecore', 'dark academia'
            ],
            
            # NEW: Natural/Organic elements
            'Natural': [
                'natural', 'organic', 'botanical', 'plant', 'greenery', 'foliage',
                'wood', 'wooden', 'timber', 'stone', 'earth tone', 'neutral',
                'linen', 'cotton', 'wool', 'jute', 'rattan', 'wicker'
            ]
        }
        
        self.city_to_region = {
            'münchen': 'Bayern', 'munich': 'Bayern', 'berlin': 'Berlin',
            'hamburg': 'Hamburg', 'köln': 'Nordrhein-Westfalen',
            'frankfurt': 'Hessen', 'stuttgart': 'Baden-Württemberg',
        }
    
    def process_pinterest_board(self, rss_url: str, location: Dict) -> Dict:
        """Main processing pipeline"""
        pins = self._parse_rss_feed(rss_url)
        print(f"Found {len(pins)} pins")
        
        analyzed_pins = self._analyze_all_pins(pins)
        
        # NEW: Analyze overall board context BEFORE scoring
        board_context = self._analyze_board_context(analyzed_pins)
        print(f"\n🎨 Board Context Analysis:")
        print(f"  Primary Focus: {board_context['primary_focus']}")
        print(f"  Space Type: {board_context['space_type']}")
        print(f"  Living Type: {board_context['living_type']}")
        
        feature_scores = self._calculate_feature_scores(analyzed_pins, board_context)
        print(f"\n📊 Adjusted Feature Scores: {feature_scores}")
        
        search_payload = self._build_thinkimmo_payload(feature_scores, location, board_context)
        properties = self._query_thinkimmo(search_payload)
        
        return {
            'analyzed_pins': analyzed_pins,
            'board_context': board_context,
            'feature_scores': feature_scores,
            'search_payload': search_payload,
            'properties': properties,
            'total_properties': len(properties)
        }
    
    def _parse_rss_feed(self, rss_url: str) -> List[Dict]:
        """Parse Pinterest RSS feed"""
        feed = feedparser.parse(rss_url)
        pins = []
        
        for entry in feed.entries:
            description_html = entry.get('description', '')
            image_url = self._extract_image_url(description_html)
            caption = self._extract_caption(description_html)
            
            if image_url:
                pins.append({
                    'title': entry.get('title', ''),
                    'description': description_html,
                    'caption': caption,  # Extracted clean caption text
                    'image_url': image_url,
                    'link': entry.get('link', '')
                })
        
        return pins
    
    def _extract_image_url(self, description: str) -> str:
        """Extract image URL from RSS description"""
        match = re.search(r'src="([^"]+)"', description)
        return match.group(1) if match else None
    
    def _extract_caption(self, description: str) -> str:
        """Extract clean caption text from RSS description HTML"""
        # Remove HTML tags
        caption = re.sub(r'<[^>]+>', '', description)
        # Decode HTML entities
        caption = caption.replace('&quot;', '"').replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>')
        # Clean up whitespace
        caption = ' '.join(caption.split())
        return caption.strip()
    
# pinterest_analyzer.py - Update _analyze_board_context

    def _analyze_board_context(self, analyzed_pins: List[Dict]) -> Dict:
        """Analyze the OVERALL board context to understand the vibe"""
        all_text = ' '.join([
            f"{pin['pin']['title']} {pin['pin'].get('caption', '')} {pin['pin']['description']}" 
            for pin in analyzed_pins
        ]).lower()
        
        # Count specific indicators
        balcony_indicators = ['balcony', 'balkon', 'patio', 'terrace', 'small balcony', 'tiny balcony', 'apartment balcony', 'terrasse']
        garden_indicators = ['backyard', 'garden', 'yard', 'lawn', 'outdoor space', 'garten']
        apartment_indicators = ['apartment', 'flat', 'loft', 'studio', 'condo', 'city', 'urban', 'downtown', 'rental', 'renter', 'wohnung']
        house_indicators = ['house', 'haus', 'villa', 'cottage', 'standalone', 'single family', 'einfamilienhaus', 'villa']
        
        balcony_count = sum(all_text.count(word) for word in balcony_indicators)
        garden_count = sum(all_text.count(word) for word in garden_indicators)
        apartment_count = sum(all_text.count(word) for word in apartment_indicators)
        house_count = sum(all_text.count(word) for word in house_indicators)
        
        print(f"\n🔍 Context Clues:")
        print(f"  Balcony/Terrace mentions: {balcony_count}")
        print(f"  Garden mentions: {garden_count}")
        print(f"  Apartment mentions: {apartment_count}")
        print(f"  House mentions: {house_count}")
        
        # Determine primary focus
        if balcony_count > garden_count * 1.5:
            primary_focus = 'balcony'
        elif garden_count > balcony_count * 1.5:
            primary_focus = 'garden'
        else:
            primary_focus = 'outdoor_space'
        
        # Determine space type
        if balcony_count > 3:
            space_type = 'small_urban'
        elif garden_count > 3:
            space_type = 'large_suburban'
        else:
            space_type = 'mixed'
        
        # Determine living type - MORE SENSITIVE
        # Even 1-2 house mentions should count if apartment mentions are low
        if apartment_count > house_count * 1.5 or balcony_count > garden_count * 1.5:
            living_type = 'apartment'
        elif house_count > apartment_count or house_count >= 2:  # Changed: house_count >= 2 is enough
            living_type = 'house'
        else:
            living_type = 'mixed'
        
        print(f"\n🏠 Interpretation:")
        print(f"  Living type: {living_type}")
        print(f"  Primary focus: {primary_focus}")
        print(f"  Space type: {space_type}")
        
        return {
            'primary_focus': primary_focus,
            'space_type': space_type,
            'living_type': living_type,
            'balcony_mentions': balcony_count,
            'garden_mentions': garden_count,
            'apartment_mentions': apartment_count,
            'house_mentions': house_count
        }
    
    def _analyze_all_pins(self, pins: List[Dict]) -> List[Dict]:
        """Analyze all pins with text analysis"""
        analyzed = []
        
        for i, pin in enumerate(pins):
            print(f"Analyzing pin {i+1}/{len(pins)}: {pin['title'][:50]}...")
            
            text_features = self._analyze_text(pin['title'], pin.get('caption', ''), pin.get('description', ''))
            # For now, skip image analysis (not working well enough)
            image_features = {}
            combined_features = text_features  # Just use text for now
            
            analyzed.append({
                'pin': pin,
                'text_features': text_features,
                'image_features': image_features,
                'combined_features': combined_features
            })
        
        # ENHANCEMENT: Use OpenAI to boost confidence with semantic understanding
        if self.openai_client and len(analyzed) > 0:
            analyzed = self._enhance_with_openai(analyzed)
        
        return analyzed
    
    def _analyze_text(self, title: str, caption: str, description: str) -> Dict[str, float]:
        """Analyze text for property features with enhanced semantic understanding"""
        # Prioritize clean caption text, but also include title and full description for comprehensive analysis
        text = f"{title} {caption} {description}".lower()
        detected = {}
        
        # Enhanced keyword matching with weighted scoring
        for feature, keywords in self.feature_keywords.items():
            match_count = 0
            matched_keywords = []
            
            for keyword in keywords:
                if keyword in text:
                    match_count += 1
                    matched_keywords.append(keyword)
            
            if match_count > 0:
                # Better scoring: more matches = higher confidence
                base_score = match_count / len(keywords)
                # Boost score significantly for multiple matches
                # Use power scaling to give stronger signals for multiple matches
                boosted_score = min(1.0, (base_score ** 0.6) * 8)
                detected[feature] = boosted_score
        
        # THEME DETECTION: Analyze overall aesthetic
        # Cottagecore/Farmhouse themes
        cottagecore_indicators = ['cottage', 'farmhouse', 'countryside', 'cozy', 'rustic', 'charm']
        if sum(1 for word in cottagecore_indicators if word in text) >= 2:
            detected['Rustic'] = max(detected.get('Rustic', 0), 0.85)
            detected['House'] = max(detected.get('House', 0), 0.75)
        
        # Colonial/Historic themes
        if any(word in text for word in ['colonial', '16th', '17th', '18th', 'century', 'historic']):
            detected['Vintage'] = max(detected.get('Vintage', 0), 0.85)
            detected['House'] = max(detected.get('House', 0), 0.75)
        
        # Interior vs Exterior detection
        interior_words = ['interior', 'living room', 'bedroom', 'kitchen', 'bathroom', 'room']
        exterior_words = ['exterior', 'facade', 'garden', 'yard', 'outdoor']
        
        has_interior = any(word in text for word in interior_words)
        has_exterior = any(word in text for word in exterior_words)
        
        # If mostly interior focus, slightly boost style features
        if has_interior and not has_exterior:
            for feature in ['Rustic', 'Vintage', 'Modern', 'Dark', 'Natural']:
                if feature in detected:
                    detected[feature] = min(1.0, detected[feature] * 1.2)
        
        # SPECIAL RULE: If "balcony" appears, strongly favor Apartment over House
        if 'balcony' in text or 'balkon' in text:
            detected['Apartment'] = max(detected.get('Apartment', 0), 0.8)
            # Reduce house score
            if 'House' in detected:
                detected['House'] = detected['House'] * 0.3
        
        # SPECIAL RULE: "apartment" or "flat" keywords should boost Apartment
        if any(word in text for word in ['apartment', 'flat', 'loft', 'studio', 'condo']):
            detected['Apartment'] = max(detected.get('Apartment', 0), 0.9)
        
        # SPECIAL RULE: Strong house indicators
        house_strong_indicators = ['farmhouse', 'cottage', 'cabin', 'villa', 'colonial']
        if any(word in text for word in house_strong_indicators):
            detected['House'] = max(detected.get('House', 0), 0.85)
        
        return detected
    
    def _enhance_with_openai(self, analyzed_pins: List[Dict]) -> List[Dict]:
        """Use OpenAI to enhance feature detection with semantic understanding"""
        print("\n🤖 Enhancing analysis with OpenAI...")
        
        try:
            # Compile board summary
            board_summary = "\n".join([
                f"Pin {i+1}: {pin['pin']['title'][:100]}" + 
                (f" - {pin['pin'].get('caption', '')[:150]}" if pin['pin'].get('caption') else "")
                for i, pin in enumerate(analyzed_pins[:10])  # Use first 10 pins for efficiency
            ])
            
            prompt = f"""Analyze this Pinterest board and rate the confidence (0-100%) for each feature category.

Board pins:
{board_summary}

Feature categories:
- Apartment: Urban apartment living
- House: Detached houses, cottages, farmhouses
- Balcony: Small outdoor spaces, balconies, terraces
- Garden: Large outdoor spaces, gardens, yards
- Modern: Contemporary, minimalist, sleek design
- Rustic: Farmhouse, cottage, cozy, natural materials
- Vintage: Antique, historic, traditional, classic
- Dark: Dark, moody, dramatic aesthetics
- Natural: Organic, botanical, natural materials

Provide confidence ratings as JSON:
{{
  "Apartment": 0-100,
  "House": 0-100,
  ...
}}

Only include features with confidence > 10%."""
            
            response = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are an expert at analyzing aesthetic preferences from Pinterest boards. Provide confidence ratings based on the overall theme and style."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                response_format={"type": "json_object"}
            )
            
            openai_scores = json.loads(response.choices[0].message.content)
            print(f"✅ OpenAI scores: {openai_scores}")
            
            # Boost existing features based on OpenAI confidence
            for pin_data in analyzed_pins:
                for feature, openai_score in openai_scores.items():
                    if feature in pin_data['combined_features']:
                        # Blend keyword score with OpenAI semantic understanding
                        current_score = pin_data['combined_features'][feature]
                        openai_normalized = openai_score / 100.0
                        # Weighted average: 60% keyword, 40% OpenAI
                        blended_score = (current_score * 0.6) + (openai_normalized * 0.4)
                        pin_data['combined_features'][feature] = min(1.0, blended_score * 1.3)
                    elif openai_score > 30:  # Add features OpenAI detected strongly
                        pin_data['combined_features'][feature] = (openai_score / 100.0) * 0.7
            
        except Exception as e:
            print(f"⚠️ OpenAI enhancement failed: {e}")
            # Continue without enhancement
        
        return analyzed_pins
    
# pinterest_analyzer.py - Update _calculate_feature_scores

    def _calculate_feature_scores(self, analyzed_pins: List[Dict], board_context: Dict) -> Dict[str, Dict]:
        """Calculate aggregate scores with context-aware adjustments"""
        aggregate_scores = defaultdict(list)
        
        for analyzed in analyzed_pins:
            for feature, score in analyzed['combined_features'].items():
                aggregate_scores[feature].append(score)
        
        final_scores = {}
        total_pins = len(analyzed_pins)
        
        for feature, scores in aggregate_scores.items():
            avg_score = sum(scores) / len(scores)
            frequency = len(scores) / total_pins
            
            # IMPROVED: More generous confidence calculation
            # Use power scaling to boost confidence while keeping it bounded
            base_confidence = (avg_score ** 0.7) * (frequency ** 0.5) * 2.2
            confidence = min(1.0, base_confidence)
            
            # CONTEXT-BASED ADJUSTMENTS
            if board_context['living_type'] == 'apartment':
                if feature == 'Apartment':
                    confidence = min(1.0, confidence * 2.5)  # Strong boost
                elif feature == 'House':
                    confidence = confidence * 0.2  # Strong reduction
            
            elif board_context['living_type'] == 'house':
                if feature == 'House':
                    confidence = min(1.0, confidence * 3.0)  # STRONG BOOST for house
                elif feature == 'Apartment':
                    confidence = confidence * 0.2  # Reduce apartment
            
            if board_context['primary_focus'] == 'balcony':
                if feature == 'Balcony':
                    confidence = min(1.0, confidence * 1.8)
                elif feature == 'Garden':
                    confidence = confidence * 0.4
            
            elif board_context['primary_focus'] == 'garden':
                if feature == 'Garden':
                    confidence = min(1.0, confidence * 1.8)
                elif feature == 'Balcony':
                    confidence = confidence * 0.4
            
            final_scores[feature] = {
                'avg_score': round(avg_score, 3),
                'frequency': round(frequency, 3),
                'confidence': round(confidence, 3),
                'count': len(scores)
            }
        
        return final_scores
    
# pinterest_analyzer.py - Update _build_thinkimmo_payload method

    def _build_thinkimmo_payload(self, feature_scores: Dict, location: Dict, board_context: Dict) -> Dict:

        """Build request payload for ThinkImmo API"""
        sorted_features = sorted(
            feature_scores.items(), 
            key=lambda x: x[1]['confidence'], 
            reverse=True
        )
        
        print(f"\n🎯 All detected features (sorted by confidence):")
        for feature, scores in sorted_features:
            print(f"  {feature}: {scores['confidence']:.3f}")
        
        # USE TOP 3 FEATURES ONLY for focused matching
        # This ensures we prioritize the strongest signals from the board
        confident_features = sorted_features[:3]
        
        print(f"\n✅ Using top 3 features:")
        for feature, scores in confident_features:
            print(f"  {feature}: {scores['confidence']:.3f}")
        

        
        # Determine property type
        property_types = [(f, s) for f, s in confident_features if f in ['Apartment', 'House']]
        
        immo_type = "APARTMENTBUY"
        house_preference = False
        
        if property_types:
            top_type = property_types[0][0]
            if top_type == 'House':
                immo_type = "HOUSEBUY"
                house_preference = True
                print(f"  → Property type: HOUSE")
            else:
                immo_type = "APARTMENTBUY"
                print(f"  → Property type: APARTMENT")
        else:
            # NO property type detected - use context
            # Check if "house" appears more than "apartment" in features
            house_score = next((s['confidence'] for f, s in sorted_features if f == 'House'), 0)
            apartment_score = next((s['confidence'] for f, s in sorted_features if f == 'Apartment'), 0)
            
            if house_score > apartment_score:
                immo_type = "HOUSEBUY"
                house_preference = True
                print(f"  → Property type: HOUSE (by score: {house_score:.3f} > {apartment_score:.3f})")
            else:
                print(f"  → Property type: APARTMENT (default)")
        
        city = location.get('city', 'München')
        city_lower = city.lower()
        region = self.city_to_region.get(city_lower, 'Bayern')
        
        payload = {
            "active": True,
            "type": immo_type,
            "sortBy": "desc",
            "sortKey": "publishDate",
            "from": 0,
            "size": 100,  # Increased from 20 to 100 for more results with images
            "geoSearches": {
                "geoSearchQuery": city,
                "geoSearchType": "town",
                "region": region
            }
        }
        
        # More lenient thresholds for feature detection
        detected_features = {
            'garden': any(f == 'Garden' and s['confidence'] > 0.15 for f, s in confident_features),  # Lowered
            'balcony': any(f == 'Balcony' and s['confidence'] > 0.15 for f, s in confident_features),  # Lowered
            'house_preference': house_preference
        }
        
        # Include ALL style preferences with confidence > 0.05 (very permissive)
        style_features = ['Modern', 'Rustic', 'Vintage', 'Dark', 'Natural']
        style_prefs = [
            {'feature': f, **s} for f, s in confident_features 
            if f in style_features and s['confidence'] > 0.05
        ]
        
        # If no style detected, add top style feature anyway
        if not style_prefs:
            style_candidates = [(f, s) for f, s in sorted_features if f in style_features]
            if style_candidates:
                top_style = style_candidates[0]
                style_prefs = [{'feature': top_style[0], **top_style[1]}]
        
        print(f"\n🎨 Style preferences: {[p['feature'] for p in style_prefs]}")
        print(f"🌳 Features wanted: garden={detected_features['garden']}, balcony={detected_features['balcony']}")
        
        payload['_metadata'] = {
            'detected_features': detected_features,
            'style_preferences': style_prefs,
            'board_context': board_context
        }
        
        return payload   
    
    def _query_thinkimmo(self, payload: Dict) -> List[Dict]:
        """Query ThinkImmo API"""
        metadata = payload.pop('_metadata', {})
        detected_features = metadata.get('detected_features', {})
        style_prefs = metadata.get('style_preferences', [])
        board_context = metadata.get('board_context', {})
        
        try:
            print(f"\n🔎 Querying ThinkImmo API...")
            
            response = requests.post(
                'https://thinkimmo-api.mgraetz.de/thinkimmo',
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            
            response.raise_for_status()
            data = response.json()
            
            properties = data.get('results', [])
            filtered_properties = self._filter_properties(properties, detected_features, style_prefs, board_context)
            
            return filtered_properties
            
        except Exception as e:
            print(f"Error querying ThinkImmo API: {e}")
            return []
    
    def _filter_properties(self, properties: List[Dict], 
                          detected_features: Dict[str, bool],
                          style_prefs: List[Dict],
                          board_context: Dict) -> List[Dict]:
        """Post-filter and score properties with board context awareness"""
        
        # Define German keywords that indicate style matches in titles
        required_keywords = {
            'rustic': ['charmant', 'gemütlich', 'charme', 'character', 'doppelhaushälfte', 
                      'reihenhaus', 'familientraum', 'traditionell', 'klassisch', 'landhaus'],
            'vintage': ['altbau', 'historisch', 'klassisch', 'charm', 'charme', 'denkmalschutz',
                       'jahrhundertwende', 'jugendstil', 'klassiker', 'tradition', 'villa'],
            'modern': ['modern', 'neu', 'neubau', 'zeitgemäß', 'contemporary', 'exklusiv', 
                      'stylisch', 'hochwertig', 'elegant', 'urban', 'penthouse', 'loft'],
            'dark': ['edel', 'elegant', 'exklusiv', 'luxus', 'sophisticated'],
            'natural': ['grün', 'garten', 'natur', 'ökologisch', 'nachhaltig', 'begrünt'],
            'balcony': ['balkon', 'terrasse', 'loggia', 'dachterrasse', 'südbalkon', 
                       'westbalkon', 'ostbalkon', 'balkon/terrasse'],
            'garden': ['garten', 'gartenanteil', 'eigengarten', 'grundstück', 'grünfläche',
                      'außenbereich', 'gartennutzung'],
            'house': ['haus', 'einfamilienhaus', 'doppelhaushälfte', 'reihenhaus', 'villa',
                     'einfamilien', 'zweifamilienhaus'],
            'apartment': ['wohnung', 'apartment', 'eigentumswohnung', 'maisonette', 'penthouse']
        }
        
        # Get all detected features for filtering (styles + property types)
        all_detected_features = style_prefs.copy()
        
        # Add property type and outdoor space features from detected_features
        if detected_features.get('house_preference'):
            all_detected_features.append({'feature': 'House', 'confidence': 0.5})
        if detected_features.get('garden'):
            all_detected_features.append({'feature': 'Garden', 'confidence': 0.5})
        if detected_features.get('balcony'):
            all_detected_features.append({'feature': 'Balcony', 'confidence': 0.5})
        
        # Get features that have keyword lists
        dominant_styles = [p['feature'].lower() for p in all_detected_features if p['feature'].lower() in required_keywords]
        
        print(f"\n🔍 Filtering properties by German keywords for styles: {dominant_styles}")
        
        scored_properties = []
        
        for prop in properties:
            title = (prop.get('title') or '').lower()
            description = (prop.get('description') or '').lower()
            
            # PRE-FILTER: Check if title contains relevant keywords for detected styles
            if dominant_styles:
                has_keyword_match = False
                for style in dominant_styles:
                    if style in required_keywords:
                        keywords = required_keywords[style]
                        if any(kw in title for kw in keywords):
                            has_keyword_match = True
                            break
                
                # Skip properties that don't match style keywords in title
                if not has_keyword_match:
                    continue
            
            match_score = 0
            reasons = []
            
            # Check if property has balcony/garden fields
            has_balcony = prop.get('balcony', False)
            has_garden = prop.get('garden', False)
            
            # Also infer from other fields
            plot_area = prop.get('plotArea', 0)
            num_floors = prop.get('numberOfFloors', 0)
            
            # Scoring
            if detected_features.get('balcony'):
                if has_balcony:
                    match_score += 5
                    reasons.append('Has balcony')
                elif num_floors > 1:
                    match_score += 2
                    reasons.append(f'Multi-floor ({num_floors})')
            
            if detected_features.get('garden'):
                if has_garden:
                    match_score += 5
                    reasons.append('Has garden')
                elif plot_area > 50:
                    match_score += 3
                    reasons.append(f'Plot: {plot_area}m²')
            
            # Style matching - expanded German keywords
            full_text = f"{title} {description}"
            
            style_keywords = {
                'rustic': [
                    'charmant', 'gemütlich', 'traditionell', 'familientraum', 'klassisch',
                    'landhaus', 'bauernhaus', 'rustikal', 'holz', 'natürlich', 'warm',
                    'behaglic', 'urig', 'charme', 'character', 'doppelhaushälfte'
                ],
                'modern': [
                    'modern', 'neu', 'neubau', 'exklusiv', 'stilvoll', 'urban',
                    'zeitgemäß', 'contemporary', 'minimalistisch', 'elegant', 'hochwertig'
                ],
                'vintage': [
                    'altbau', 'klassisch', 'historisch', 'charm', 'klassiker',
                    'tradition', 'denkmalschutz', 'jahrhundertwende', 'jugendstil', 'antik'
                ],
                'dark': [
                    'dunkel', 'edel', 'elegant', 'exklusiv', 'luxus', 'sophisticated'
                ],
                'natural': [
                    'grün', 'garten', 'natur', 'ökologisch', 'nachhaltig', 'natürlich',
                    'holz', 'bio', 'umwelt', 'öko'
                ]
            }
            
            for pref in style_prefs:
                feature = pref['feature'].lower()
                confidence = pref['confidence']
                
                if feature in style_keywords:
                    keywords = style_keywords[feature]
                    matches = [kw for kw in keywords if kw in full_text]
                    if matches:
                        # Higher boost for style matches
                        score_boost = confidence * len(matches) * 3
                        match_score += score_boost
                        reasons.append(f'{feature.title()}: {", ".join(matches[:3])}')
            
            # Strict year filtering for vintage/rustic styles
            construction_year = prop.get('constructionYear', None)
            has_vintage_rustic = any(p['feature'].lower() in ['rustic', 'vintage'] for p in style_prefs)
            
            if construction_year:
                # For vintage/rustic boards, strongly prefer pre-1920s properties
                if has_vintage_rustic:
                    if construction_year <= 1920:
                        # Excellent match for truly old properties
                        age_bonus = 5.0
                        match_score += age_bonus
                        reasons.append(f'Historic property ({construction_year})')
                    elif construction_year <= 1950:
                        # Good match for mid-century
                        age_bonus = 2.0
                        match_score += age_bonus
                        reasons.append(f'Built {construction_year}')
                    elif construction_year > 1990:
                        # Penalize modern properties for vintage/rustic boards
                        match_score *= 0.5
                else:
                    # For non-vintage boards, slight bonus for character
                    if construction_year < 1980:
                        age_bonus = 1.0
                        match_score += age_bonus
                        reasons.append(f'Built {construction_year}')
            
            # Use board context for property type filtering
            living_type = board_context.get('living_type', 'mixed')
            property_type = prop.get('realEstateType', '').lower()
            
            # Boost or penalize based on living type interpretation
            if living_type == 'house':
                if 'house' in property_type or 'villa' in property_type or 'einfamilienhaus' in property_type:
                    match_score *= 1.5
                    reasons.append('Property type matches board preference')
                elif 'apartment' in property_type or 'wohnung' in property_type:
                    match_score *= 0.3  # Strong penalty for apartments on house boards
            elif living_type == 'apartment':
                if 'apartment' in property_type or 'wohnung' in property_type:
                    match_score *= 1.5
                    reasons.append('Property type matches board preference')
                elif 'house' in property_type:
                    match_score *= 0.3  # Strong penalty for houses on apartment boards
            
            # Use garden/outdoor space from board context
            primary_focus = board_context.get('primary_focus', '')
            if primary_focus == 'garden' and prop.get('garden', False):
                match_score += 3.0
                reasons.append('Has garden (board preference)')
            elif primary_focus == 'balcony' and prop.get('balcony', False):
                match_score += 3.0
                reasons.append('Has balcony (board preference)')
            
            # Extract image URL from images array
            images = prop.get('images', [])
            if images and len(images) > 0:
                prop['image'] = images[0].get('originalUrl', '')
            else:
                prop['image'] = ''
            
            # Extract the actual platform URL from the response (this is the correct link to the listing)
            platforms = prop.get('platforms', [])
            if platforms and len(platforms) > 0:
                prop['link'] = platforms[0].get('url', '')
            else:
                prop['link'] = ''
            
            prop['match_score'] = round(match_score, 2)
            prop['match_reasons'] = reasons
            scored_properties.append(prop)
        
        sorted_props = sorted(scored_properties, key=lambda x: x.get('match_score', 0), reverse=True)
        
        print(f"\n📊 Top 3 matches:")
        for i, prop in enumerate(sorted_props[:3], 1):
            print(f"  {i}. Score {prop['match_score']}: {prop.get('title', '')[:60]}")
            if prop.get('match_reasons'):
                print(f"     Why: {', '.join(prop['match_reasons'])}")
        
        return sorted_props