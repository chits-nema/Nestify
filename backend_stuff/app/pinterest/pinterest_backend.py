# pinterest_analyzer.py - Updated to use API key
import feedparser
import requests
from typing import List, Dict
import re
from collections import defaultdict
import json
import base64

class PinterestPropertyAnalyzer:
    def __init__(self, vision_api_key: str):
        self.vision_api_key = vision_api_key
        self.vision_api_url = "https://vision.googleapis.com/v1/images:annotate"
        
        self.feature_keywords = {
            'Apartment': ['apartment', 'wohnung', 'flat', 'condo', 'loft', 'studio'],
            'House': ['house', 'haus', 'villa', 'home', 'cottage', 'bungalow', 'townhouse'],
            'Garden': ['garden', 'garten', 'yard', 'outdoor space', 'backyard', 'lawn', 'greenery'],
            'Balcony': ['balcony', 'balkon', 'terrace', 'terrasse', 'patio', 'deck'],
            'Modern': ['modern', 'contemporary', 'minimalist', 'sleek', 'clean', 'industrial'],
            'Rustic': ['rustic', 'farmhouse', 'country', 'wood', 'barn', 'cozy', 'cabin'],
            'Vintage': ['vintage', 'antique', 'retro', 'classic', 'traditional', 'victorian', 'historic']
        }
        
        # City to region mapping (full names)
        self.city_to_region = {
            'münchen': 'Bayern',
            'munich': 'Bayern',
            'berlin': 'Berlin',
            'hamburg': 'Hamburg',
            'köln': 'Nordrhein-Westfalen',
            'cologne': 'Nordrhein-Westfalen',
            'frankfurt': 'Hessen',
            'stuttgart': 'Baden-Württemberg',
            'düsseldorf': 'Nordrhein-Westfalen',
            'dortmund': 'Nordrhein-Westfalen',
            'essen': 'Nordrhein-Westfalen',
            'leipzig': 'Sachsen',
            'bremen': 'Bremen',
            'dresden': 'Sachsen',
            'hannover': 'Niedersachsen',
            'nürnberg': 'Bayern',
            'nuremberg': 'Bayern',
        }
    
    def process_pinterest_board(self, rss_url: str, location: Dict) -> Dict:
        """Main processing pipeline"""
        # 1. Parse RSS feed
        pins = self._parse_rss_feed(rss_url)
        print(f"Found {len(pins)} pins")
        
        # 2. Analyze all pins (text + image in parallel)
        analyzed_pins = self._analyze_all_pins(pins)
        
        # 3. Calculate aggregate feature scores
        feature_scores = self._calculate_feature_scores(analyzed_pins)
        print(f"Feature scores: {feature_scores}")
        
        # 4. Build ThinkImmo query
        search_payload = self._build_thinkimmo_payload(feature_scores, location)
        print(f"Search payload: {json.dumps(search_payload, indent=2)}")
        
        # 5. Query ThinkImmo API
        properties = self._query_thinkimmo(search_payload)
        
        return {
            'analyzed_pins': analyzed_pins,
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
            # Extract image URL from description
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
    
    def _analyze_all_pins(self, pins: List[Dict]) -> List[Dict]:
        """Analyze all pins with both text and image analysis"""
        analyzed = []
        
        for i, pin in enumerate(pins):
            print(f"Analyzing pin {i+1}/{len(pins)}: {pin['title'][:50]}...")
            
            # Text analysis
            text_features = self._analyze_text(pin['title'], pin['description'])
            
            # Image analysis with API key
            image_features = self._analyze_image(pin['image_url'])
            
            # Merge features
            combined_features = self._merge_features(text_features, image_features)
            
            analyzed.append({
                'pin': pin,
                'text_features': text_features,
                'image_features': image_features,
                'combined_features': combined_features
            })
        
        return analyzed
    
    def _analyze_text(self, title: str, description: str) -> Dict[str, float]:
        """Analyze text for property features"""
        text = f"{title} {description}".lower()
        detected = {}
        
        for feature, keywords in self.feature_keywords.items():
            match_count = sum(1 for keyword in keywords if keyword in text)
            if match_count > 0:
                # Confidence based on how many keywords matched
                detected[feature] = match_count / len(keywords)
        
        return detected
    
    def _analyze_image(self, image_url: str) -> Dict[str, float]:
        """Analyze image using Google Cloud Vision API with API key"""
        try:
            # Build the request payload
            request_payload = {
                "requests": [
                    {
                        "image": {
                            "source": {
                                "imageUri": image_url
                            }
                        },
                        "features": [
                            {
                                "type": "LABEL_DETECTION",
                                "maxResults": 20
                            },
                            {
                                "type": "IMAGE_PROPERTIES"
                            },
                            {
                                "type": "OBJECT_LOCALIZATION",
                                "maxResults": 10
                            }
                        ]
                    }
                ]
            }
            
            # Make request to Vision API
            response = requests.post(
                f"{self.vision_api_url}?key={self.vision_api_key}",
                json=request_payload,
                timeout=10
            )
            
            response.raise_for_status()
            data = response.json()
            
            if 'responses' not in data or len(data['responses']) == 0:
                print(f"No response from Vision API for {image_url}")
                return {}
            
            result = data['responses'][0]
            
            # Check for errors
            if 'error' in result:
                print(f"Vision API error: {result['error']}")
                return {}
            
            # Extract features
            labels = result.get('labelAnnotations', [])
            image_props = result.get('imagePropertiesAnnotation', {})
            colors = image_props.get('dominantColors', {}).get('colors', [])
            objects = result.get('localizedObjectAnnotations', [])
            
            return self._classify_vision_features(labels, objects, colors)
            
        except Exception as e:
            print(f"Error analyzing image {image_url}: {e}")
            return {}
    
    def _classify_vision_features(self, labels, objects, colors) -> Dict[str, float]:
        """Classify Vision API results into our feature categories"""
        detected = {}
        
        # Convert labels to list of (description, score) tuples
        label_list = [(label['description'].lower(), label['score']) for label in labels]
        
        # Property Type Detection
        apartment_indicators = ['apartment', 'condominium', 'loft', 'penthouse', 'flat']
        house_indicators = ['house', 'home', 'cottage', 'villa', 'building exterior', 'residential area']
        
        for desc, score in label_list:
            if any(ind in desc for ind in apartment_indicators):
                detected['Apartment'] = max(detected.get('Apartment', 0), score)
            if any(ind in desc for ind in house_indicators):
                detected['House'] = max(detected.get('House', 0), score)
        
        # Feature Detection
        garden_indicators = ['garden', 'lawn', 'grass', 'plant', 'tree', 'vegetation', 'flower', 'backyard']
        balcony_indicators = ['balcony', 'terrace', 'patio', 'deck', 'railing']
        
        for desc, score in label_list:
            if any(ind in desc for ind in garden_indicators):
                detected['Garden'] = max(detected.get('Garden', 0), score)
            if any(ind in desc for ind in balcony_indicators):
                detected['Balcony'] = max(detected.get('Balcony', 0), score)
        
        # Style Detection
        modern_indicators = ['modern', 'contemporary', 'minimalist', 'architecture', 'glass', 'steel', 'minimal']
        rustic_indicators = ['wood', 'wooden', 'rustic', 'natural', 'timber', 'brick', 'stone']
        vintage_indicators = ['vintage', 'antique', 'classic', 'ornament', 'decorative', 'traditional']
        
        for desc, score in label_list:
            if any(ind in desc for ind in modern_indicators):
                detected['Modern'] = max(detected.get('Modern', 0), score)
            if any(ind in desc for ind in rustic_indicators):
                detected['Rustic'] = max(detected.get('Rustic', 0), score)
            if any(ind in desc for ind in vintage_indicators):
                detected['Vintage'] = max(detected.get('Vintage', 0), score)
        
        # Color-based style hints
        if colors:
            dominant_color = colors[0]
            color_info = dominant_color.get('color', {})
            r = color_info.get('red', 0)
            g = color_info.get('green', 0)
            b = color_info.get('blue', 0)
            
            # Modern: clean whites, grays, blacks
            if r > 200 and g > 200 and b > 200:
                detected['Modern'] = max(detected.get('Modern', 0), 0.6)
            
            # Rustic: earth tones (browns)
            if 100 < r < 180 and 70 < g < 140 and b < 100:
                detected['Rustic'] = max(detected.get('Rustic', 0), 0.5)
        
        return detected
    
    def _merge_features(self, text_features: Dict[str, float], 
                       image_features: Dict[str, float]) -> Dict[str, float]:
        """Merge text and image features with weighted average"""
        all_features = set(list(text_features.keys()) + list(image_features.keys()))
        merged = {}
        
        for feature in all_features:
            text_score = text_features.get(feature, 0)
            image_score = image_features.get(feature, 0)
            
            # Weighted average: Text 40%, Image 60%
            merged[feature] = (text_score * 0.4) + (image_score * 0.6)
        
        return merged
    
    def _calculate_feature_scores(self, analyzed_pins: List[Dict]) -> Dict[str, Dict]:
        """Calculate aggregate scores across all pins"""
        aggregate_scores = defaultdict(list)
        
        for analyzed in analyzed_pins:
            for feature, score in analyzed['combined_features'].items():
                aggregate_scores[feature].append(score)
        
        # Calculate statistics for each feature
        final_scores = {}
        total_pins = len(analyzed_pins)
        
        for feature, scores in aggregate_scores.items():
            avg_score = sum(scores) / len(scores)
            frequency = len(scores) / total_pins
            
            # Confidence: combines average score and frequency
            confidence = min(1.0, avg_score * frequency * 1.5)
            
            final_scores[feature] = {
                'avg_score': round(avg_score, 3),
                'frequency': round(frequency, 3),
                'confidence': round(confidence, 3),
                'count': len(scores)
            }
        
        return final_scores
    
    def _build_thinkimmo_payload(self, feature_scores: Dict, location: Dict) -> Dict:
        """Build request payload for ThinkImmo API - following example format"""
        # Sort by confidence
        sorted_features = sorted(
            feature_scores.items(), 
            key=lambda x: x[1]['confidence'], 
            reverse=True
        )
        
        # Filter confident features
        confident_features = [
            (feature, scores) for feature, scores in sorted_features 
            if scores['confidence'] > 0.3
        ]
        
        # Determine property type (highest scoring between Apartment/House)
        property_types = [(f, s) for f, s in confident_features if f in ['Apartment', 'House']]
        
        # Default to APARTMENTBUY
        immo_type = "APARTMENTBUY"
        if property_types:
            top_type = property_types[0][0]
            immo_type = "APARTMENTBUY" if top_type == 'Apartment' else "HOUSEBUY"
        
        # Get city and region
        city = location.get('city', 'München')
        city_lower = city.lower()
        region = self.city_to_region.get(city_lower, 'Bayern')  # Default to Bayern
        
        # Build the payload following the example format
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
        
        # Store detected features and style preferences for post-filtering
        detected_features = {
            'garden': any(f == 'Garden' and s['confidence'] > 0.4 for f, s in confident_features),
            'balcony': any(f == 'Balcony' and s['confidence'] > 0.4 for f, s in confident_features)
        }
        
        style_prefs = [
            {'feature': f, **s} for f, s in confident_features 
            if f in ['Modern', 'Rustic', 'Vintage']
        ]
        
        payload['_metadata'] = {
            'detected_features': detected_features,
            'style_preferences': style_prefs
        }
        
        return payload
    
    def _query_thinkimmo(self, payload: Dict) -> List[Dict]:
        """Query ThinkImmo API with POST request"""
        # Extract metadata (not sent to API)
        metadata = payload.pop('_metadata', {})
        detected_features = metadata.get('detected_features', {})
        style_prefs = metadata.get('style_preferences', [])
        
        try:
            print(f"\nQuerying ThinkImmo API...")
            
            response = requests.post(
                'https://thinkimmo-api.mgraetz.de/thinkimmo',
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            
            print(f"Response status: {response.status_code}")
            
            response.raise_for_status()
            data = response.json()
            
            properties = data.get('results', [])
            total = data.get('total', 0)
            
            print(f"ThinkImmo API returned {len(properties)} properties (total available: {total})")
            
            # Post-filter by features and style
            filtered_properties = self._filter_properties(
                properties, 
                detected_features, 
                style_prefs
            )
            
            return filtered_properties
            
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 429:
                print("⚠️  Rate limit exceeded (429). Please implement caching and backoff.")
            print(f"HTTP Error querying ThinkImmo API: {e}")
            if hasattr(e, 'response'):
                print(f"Response text: {e.response.text[:500]}")
            return []
        except Exception as e:
            print(f"Error querying ThinkImmo API: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def _filter_properties(self, properties: List[Dict], 
                          detected_features: Dict[str, bool],
                          style_prefs: List[Dict]) -> List[Dict]:
        """Post-filter and score properties based on detected features and style"""
        scored_properties = []
        
        for prop in properties:
            match_score = 0
            
            # Feature matching (balcony, garden from API response)
            if detected_features.get('garden') and prop.get('garden'):
                match_score += 2
            if detected_features.get('balcony') and prop.get('balcony'):
                match_score += 2
            
            # Style matching (from title)
            title = prop.get('title', '').lower()
            
            for pref in style_prefs:
                feature = pref['feature'].lower()
                confidence = pref['confidence']
                
                if feature in title:
                    match_score += confidence * 3
            
            prop['match_score'] = round(match_score, 2)
            scored_properties.append(prop)
        
        # Sort by match score (highest first)
        return sorted(scored_properties, key=lambda x: x.get('match_score', 0), reverse=True)