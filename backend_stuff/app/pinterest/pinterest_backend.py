# pinterest_analyzer.py - FIXED with better contextual understanding

import feedparser
import requests
from typing import List, Dict
import re
from collections import defaultdict
import json

class PinterestPropertyAnalyzer:
    def __init__(self, hf_api_key: str = None):
        self.hf_api_key = hf_api_key
        self.headers = {"Authorization": f"Bearer {hf_api_key}"} if hf_api_key else {}
        
        # MORE SPECIFIC keywords
        self.feature_keywords = {
            # APARTMENTS - very specific urban living keywords
            'Apartment': [
                'apartment', 'flat', 'condo', 'loft', 'studio', 'wohnung',
                'city living', 'urban', 'downtown', 'high rise', 'apartment balcony',
                'tiny balcony', 'small balcony', 'apt', 'rental', 'renter',
                'cozy balcony', 'balcony decor', 'patio decorating'  # These are apartment-specific!
            ],
            
            # HOUSES - only use when clearly standalone
            'House': [
                'house exterior', 'villa', 'cottage', 'standalone', 'detached',
                'single family', 'driveway', 'front yard', 'backyard with fence'
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
                'backyard', 'garden with lawn', 'large garden', 'landscaping',
                'yard', 'outdoor space with grass', 'garden path'
            ],
            
            'Modern': ['modern', 'contemporary', 'minimalist', 'sleek', 'clean', 'industrial', 'scandinavian'],
            'Rustic': ['rustic', 'farmhouse', 'country', 'wood', 'barn', 'cozy', 'cabin', 'vintage wood'],
            'Vintage': ['vintage', 'antique', 'retro', 'classic', 'traditional', 'victorian', 'historic', 'old fashioned']
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
        
        search_payload = self._build_thinkimmo_payload(feature_scores, location)
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
            image_url = self._extract_image_url(entry.get('description', ''))
            
            if image_url:
                pins.append({
                    'title': entry.get('title', ''),
                    'description': entry.get('description', ''),
                    'image_url': image_url,
                    'link': entry.get('link', '')
                })
        
        return pins
    
    def _extract_image_url(self, description: str) -> str:
        """Extract image URL from RSS description"""
        match = re.search(r'src="([^"]+)"', description)
        return match.group(1) if match else None
    
    # pinterest_analyzer.py - Update _analyze_board_context

    def _analyze_board_context(self, analyzed_pins: List[Dict]) -> Dict:
        """Analyze the OVERALL board context to understand the vibe"""
        all_text = ' '.join([
            f"{pin['pin']['title']} {pin['pin']['description']}" 
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
            
            text_features = self._analyze_text(pin['title'], pin['description'])
            # For now, skip image analysis (not working well enough)
            image_features = {}
            combined_features = text_features  # Just use text for now
            
            analyzed.append({
                'pin': pin,
                'text_features': text_features,
                'image_features': image_features,
                'combined_features': combined_features
            })
        
        return analyzed
    
    def _analyze_text(self, title: str, description: str) -> Dict[str, float]:
        """Analyze text for property features with better context understanding"""
        text = f"{title} {description}".lower()
        detected = {}
        
        for feature, keywords in self.feature_keywords.items():
            match_count = sum(1 for keyword in keywords if keyword in text)
            if match_count > 0:
                detected[feature] = min(1.0, match_count / len(keywords) * 3)  # Boost score
        
        # SPECIAL RULE: If "balcony" appears, strongly favor Apartment over House
        if 'balcony' in text or 'balkon' in text:
            detected['Apartment'] = max(detected.get('Apartment', 0), 0.8)
            # Reduce house score
            if 'House' in detected:
                detected['House'] = detected['House'] * 0.3
        
        # SPECIAL RULE: "apartment" or "flat" keywords should boost Apartment
        if any(word in text for word in ['apartment', 'flat', 'loft', 'studio', 'condo']):
            detected['Apartment'] = max(detected.get('Apartment', 0), 0.9)
        
        return detected
    
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
            confidence = min(1.0, avg_score * frequency * 1.5)
            
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

    def _build_thinkimmo_payload(self, feature_scores: Dict, location: Dict) -> Dict:
        """Build request payload for ThinkImmo API"""
        sorted_features = sorted(
            feature_scores.items(), 
            key=lambda x: x[1]['confidence'], 
            reverse=True
        )
        
        print(f"\n🎯 All detected features (sorted by confidence):")
        for feature, scores in sorted_features:
            print(f"  {feature}: {scores['confidence']:.3f}")
        
        # LOWERED THRESHOLD: Use top features even if confidence is low
        # Take ANY feature with confidence > 0.10 OR top 3 features
        confident_features = [
            (feature, scores) for feature, scores in sorted_features 
            if scores['confidence'] > 0.10  # Lowered from 0.25
        ]
        
        # If still nothing, take top 3 regardless
        if not confident_features:
            confident_features = sorted_features[:3]
        
        print(f"\n✅ Using {len(confident_features)} features:")
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
            "size": 20,
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
        
        # Include ALL style preferences with confidence > 0.10
        style_prefs = [
            {'feature': f, **s} for f, s in confident_features 
            if f in ['Modern', 'Rustic', 'Vintage'] and s['confidence'] > 0.10  # Lowered from 0.25
        ]
        
        print(f"\n🎨 Style preferences: {[p['feature'] for p in style_prefs]}")
        print(f"🌳 Features wanted: garden={detected_features['garden']}, balcony={detected_features['balcony']}")
        
        payload['_metadata'] = {
            'detected_features': detected_features,
            'style_preferences': style_prefs
        }
        
        return payload

    
    def _query_thinkimmo(self, payload: Dict) -> List[Dict]:
        """Query ThinkImmo API"""
        metadata = payload.pop('_metadata', {})
        detected_features = metadata.get('detected_features', {})
        style_prefs = metadata.get('style_preferences', [])
        
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
            filtered_properties = self._filter_properties(properties, detected_features, style_prefs)
            
            return filtered_properties
            
        except Exception as e:
            print(f"Error querying ThinkImmo API: {e}")
            return []
    
    def _filter_properties(self, properties: List[Dict], 
                          detected_features: Dict[str, bool],
                          style_prefs: List[Dict]) -> List[Dict]:
        """Post-filter and score properties"""
        scored_properties = []
        
        for prop in properties:
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
            
            # Style matching
            title = (prop.get('title') or '').lower()
            
            style_keywords = {
                'rustic': ['charmant', 'gemütlich', 'traditionell', 'familientraum', 'klassisch'],
                'modern': ['modern', 'neu', 'neubau', 'exklusiv', 'stilvoll', 'urban'],
                'vintage': ['altbau', 'klassisch', 'historisch', 'charm']
            }
            
            for pref in style_prefs:
                feature = pref['feature'].lower()
                confidence = pref['confidence']
                
                if feature in style_keywords:
                    keywords = style_keywords[feature]
                    matches = [kw for kw in keywords if kw in title]
                    if matches:
                        score_boost = confidence * len(matches) * 2
                        match_score += score_boost
                        reasons.append(f'{feature.title()}: {", ".join(matches)}')
            
            # Construction year bonus for rustic
            construction_year = prop.get('constructionYear', 2020)
            if construction_year and construction_year < 2000:
                if any(p['feature'].lower() == 'rustic' for p in style_prefs):
                    age_bonus = min(2, (2000 - construction_year) / 50)
                    match_score += age_bonus
                    reasons.append(f'Built {construction_year}')
            
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
