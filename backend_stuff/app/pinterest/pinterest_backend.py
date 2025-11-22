# pinterest_analyzer.py - Add more feature detection and better matching

class PinterestPropertyAnalyzer:
    def __init__(self, hf_api_key: str = None):
        self.hf_api_key = hf_api_key
        self.headers = {"Authorization": f"Bearer {hf_api_key}"} if hf_api_key else {}
        
        # EXPANDED keywords with more property features
        self.feature_keywords = {
            # Property types
            'Apartment': [
                'apartment', 'flat', 'condo', 'loft', 'studio', 'wohnung',
                'city living', 'urban', 'downtown', 'high rise', 'apartment balcony',
                'tiny balcony', 'small balcony', 'apt', 'rental', 'renter',
                'cozy balcony', 'balcony decor', 'patio decorating'
            ],
            'House': [
                'house exterior', 'villa', 'cottage', 'standalone', 'detached',
                'single family', 'driveway', 'front yard', 'backyard with fence',
                'haus', 'einfamilienhaus', 'reihenhaus'
            ],
            
            # Outdoor spaces
            'Balcony': [
                'balcony', 'balkon', 'terrace', 'patio', 'small balcony',
                'tiny balcony', 'apartment balcony', 'city balcony', 'urban balcony',
                'balcony decor', 'balcony garden', 'balcony furniture', 'balcony setup',
                'cozy balcony', 'balcony with plants', 'balcony view', 'terrasse'
            ],
            'Garden': [
                'backyard', 'garden', 'yard', 'lawn', 'outdoor space',
                'garden path', 'landscaping', 'garten', 'large garden'
            ],
            
            # Styles
            'Modern': ['modern', 'contemporary', 'minimalist', 'sleek', 'clean', 'industrial', 'scandinavian', 'neu', 'neubau'],
            'Rustic': ['rustic', 'farmhouse', 'country', 'wood', 'barn', 'cozy', 'cabin', 'vintage wood', 'landhausstil', 'gemütlich'],
            'Vintage': ['vintage', 'antique', 'retro', 'classic', 'traditional', 'victorian', 'historic', 'old fashioned', 'altbau'],
            
            # NEW: Additional features
            'Garage': ['garage', 'parking', 'carport', 'stellplatz', 'tiefgarage', 'parkplatz'],
            'Elevator': ['elevator', 'lift', 'aufzug', 'accessible'],
            'Cellar': ['cellar', 'basement', 'storage', 'keller', 'storage room'],
            'NewBuild': ['new build', 'newly built', 'neubau', 'new construction', 'brand new'],
            'Renovated': ['renovated', 'refurbished', 'modernized', 'saniert', 'renoviert', 'updated'],
        }
        
        self.city_to_region = {
            'münchen': 'Bayern', 'munich': 'Bayern', 'berlin': 'Berlin',
            'hamburg': 'Hamburg', 'köln': 'Nordrhein-Westfalen',
            'frankfurt': 'Hessen', 'stuttgart': 'Baden-Württemberg',
        }
    
    # ... (keep existing methods: process_pinterest_board, _parse_rss_feed, etc.)
    
    def _filter_properties(self, properties: List[Dict], 
                          detected_features: Dict[str, bool],
                          style_prefs: List[Dict]) -> List[Dict]:
        """Enhanced post-filter with more property features"""
        scored_properties = []
        
        for prop in properties:
            match_score = 0
            reasons = []
            
            # ===== PRIMARY FEATURES (from API) =====
            
            # Balcony (direct from API)
            has_balcony = prop.get('balcony', False)
            if detected_features.get('balcony') and has_balcony:
                match_score += 5
                reasons.append('✓ Has balcony')
            
            # Garden (direct from API)
            has_garden = prop.get('garden', False)
            if detected_features.get('garden') and has_garden:
                match_score += 5
                reasons.append('✓ Has garden')
            
            # Elevator/Lift
            has_lift = prop.get('lift', False)
            if detected_features.get('elevator') and has_lift:
                match_score += 2
                reasons.append('✓ Has elevator')
            elif has_lift:
                match_score += 0.5  # Small bonus even if not explicitly wanted
            
            # Cellar
            has_cellar = prop.get('cellar', False)
            if detected_features.get('cellar') and has_cellar:
                match_score += 2
                reasons.append('✓ Has cellar')
            elif has_cellar:
                match_score += 0.5
            
            # ===== INFERRED FEATURES =====
            
            # Garage (infer from plot area or building type)
            plot_area = prop.get('plotArea', 0)
            building_type = (prop.get('buildingType') or '').lower()
            
            # Likely has parking if house with land
            if detected_features.get('garage'):
                if plot_area > 100 or 'garage' in building_type:
                    match_score += 3
                    reasons.append('✓ Likely has parking')
            
            # Garden inference (for houses without explicit garden field)
            if not has_garden and plot_area > 50:
                if detected_features.get('garden'):
                    match_score += 3
                    reasons.append(f'✓ Has land ({plot_area}m²)')
            
            # ===== CONDITION & AGE =====
            
            construction_year = prop.get('constructionYear', 2020)
            condition = prop.get('condition', '')
            last_refurb = prop.get('lastRefurbishment')
            
            # New build preference
            if detected_features.get('newbuild'):
                if construction_year and construction_year >= 2020:
                    match_score += 4
                    reasons.append(f'✓ New build ({construction_year})')
            
            # Renovated preference
            if detected_features.get('renovated'):
                if last_refurb or condition in ['MODERNIZED', 'REFURBISHED', 'WELL_KEPT']:
                    match_score += 3
                    reasons.append('✓ Renovated/Modern condition')
            
            # ===== STYLE MATCHING =====
            
            title = (prop.get('title') or '').lower()
            
            style_keywords = {
                'rustic': ['charmant', 'gemütlich', 'traditionell', 'familientraum', 'klassisch', 'altbau'],
                'modern': ['modern', 'neu', 'neubau', 'exklusiv', 'stilvoll', 'urban', 'contemporary'],
                'vintage': ['altbau', 'klassisch', 'historisch', 'charm', 'traditional']
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
                        reasons.append(f'🎨 {feature.title()}: {", ".join(matches)}')
            
            # Construction year style matching
            if construction_year:
                for pref in style_prefs:
                    feature = pref['feature'].lower()
                    confidence = pref['confidence']
                    
                    # Rustic/Vintage = older buildings
                    if feature in ['rustic', 'vintage'] and construction_year < 2000:
                        age_bonus = min(2, (2000 - construction_year) / 50) * confidence
                        match_score += age_bonus
                        reasons.append(f'🏛️ Character building ({construction_year})')
                    
                    # Modern = newer buildings
                    elif feature == 'modern' and construction_year >= 2010:
                        match_score += confidence * 2
                        reasons.append(f'✨ Modern build ({construction_year})')
            
            # ===== PROPERTY TYPE MATCHING =====
            
            apartment_type = prop.get('apartmentType', '')
            
            if detected_features.get('house_preference'):
                if 'house' in building_type or 'haus' in building_type.lower():
                    match_score += 2
                    reasons.append('🏡 House type match')
            
            # ===== LOCATION QUALITY (bonus) =====
            
            location_factor = prop.get('locationFactor', {})
            location_score = location_factor.get('score', 0)
            
            if location_score > 80:
                match_score += 1
                reasons.append(f'📍 Prime location (score: {location_score})')
            
            # ===== PRICE INDICATORS (bonus for good deals) =====
            
            price_reduced = prop.get('priceReduced', False)
            if price_reduced:
                match_score += 0.5
                reasons.append('💰 Price reduced')
            
            # Store results
            prop['match_score'] = round(match_score, 2)
            prop['match_reasons'] = reasons
            scored_properties.append(prop)
        
        # Sort by match score
        sorted_props = sorted(scored_properties, key=lambda x: x.get('match_score', 0), reverse=True)
        
        # Debug: Print top matches
        print(f"\n📊 Top 5 property matches:")
        for i, prop in enumerate(sorted_props[:5], 1):
            score = prop.get('match_score', 0)
            title = prop.get('title', '')[:70]
            print(f"\n  {i}. Score: {score:.2f}")
            print(f"     {title}")
            if prop.get('match_reasons'):
                for reason in prop['match_reasons'][:5]:  # Show top 5 reasons
                    print(f"       • {reason}")
        
        return sorted_props
    
    def _build_thinkimmo_payload(self, feature_scores: Dict, location: Dict) -> Dict:
        """Build request payload with expanded feature detection"""
        sorted_features = sorted(
            feature_scores.items(), 
            key=lambda x: x[1]['confidence'], 
            reverse=True
        )
        
        print(f"\n🎯 All detected features (sorted by confidence):")
        for feature, scores in sorted_features[:10]:  # Show top 10
            print(f"  {feature}: {scores['confidence']:.3f}")
        
        # Take features with confidence > 0.10
        confident_features = [
            (feature, scores) for feature, scores in sorted_features 
            if scores['confidence'] > 0.10
        ]
        
        if not confident_features:
            confident_features = sorted_features[:3]
        
        print(f"\n✅ Using {len(confident_features)} features for search")
        
        # Property type determination
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
            house_score = next((s['confidence'] for f, s in sorted_features if f == 'House'), 0)
            apartment_score = next((s['confidence'] for f, s in sorted_features if f == 'Apartment'), 0)
            
            if house_score > apartment_score:
                immo_type = "HOUSEBUY"
                house_preference = True
                print(f"  → Property type: HOUSE (by score)")
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
        
        # Expanded feature detection
        detected_features = {
            'garden': any(f == 'Garden' and s['confidence'] > 0.15 for f, s in confident_features),
            'balcony': any(f == 'Balcony' and s['confidence'] > 0.15 for f, s in confident_features),
            'garage': any(f == 'Garage' and s['confidence'] > 0.15 for f, s in confident_features),
            'elevator': any(f == 'Elevator' and s['confidence'] > 0.15 for f, s in confident_features),
            'cellar': any(f == 'Cellar' and s['confidence'] > 0.15 for f, s in confident_features),
            'newbuild': any(f == 'NewBuild' and s['confidence'] > 0.15 for f, s in confident_features),
            'renovated': any(f == 'Renovated' and s['confidence'] > 0.15 for f, s in confident_features),
            'house_preference': house_preference
        }
        
        style_prefs = [
            {'feature': f, **s} for f, s in confident_features 
            if f in ['Modern', 'Rustic', 'Vintage'] and s['confidence'] > 0.10
        ]
        
        print(f"\n🎨 Style preferences: {[p['feature'] for p in style_prefs]}")
        print(f"🌳 Features wanted:")
        for feature, wanted in detected_features.items():
            if wanted and feature != 'house_preference':
                print(f"   • {feature.title()}")
        
        payload['_metadata'] = {
            'detected_features': detected_features,
            'style_preferences': style_prefs
        }
        
        return payload