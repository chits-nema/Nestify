# test_analyzer.py
from pinterest_backend import PinterestPropertyAnalyzer
import json
import os

def test_analysis():
    analyzer = PinterestPropertyAnalyzer(os.environ.get('GOOGLE_VISION_API_KEY'))
    
    # Test with a sample RSS URL
    rss_url = "https://www.pinterest.com/chitsidzonemazuwa/inthehousebored.rss"
    location = {
        'city': 'München',  # Using German spelling as in the example
    }
    
    print("="*70)
    print("PINTEREST BOARD PROPERTY ANALYZER TEST")
    print("="*70)
    print(f"RSS URL: {rss_url}")
    print(f"Location: {location['city']}")
    print()
    
    print("Starting analysis...")
    result = analyzer.process_pinterest_board(rss_url, location)
    
    print("\n" + "="*70)
    print("FEATURE SCORES")
    print("="*70)
    for feature, scores in sorted(result['feature_scores'].items(), 
                                   key=lambda x: x[1]['confidence'], 
                                   reverse=True):
        print(f"{feature:15} | confidence: {scores['confidence']:.2f} | "
              f"frequency: {scores['frequency']:.2f} | count: {scores['count']}")
    
    print("\n" + "="*70)
    print("THINKIMMO SEARCH PAYLOAD")
    print("="*70)
    # Remove metadata for display
    display_payload = {k: v for k, v in result['search_payload'].items() 
                      if k != '_metadata'}
    print(json.dumps(display_payload, indent=2, ensure_ascii=False))
    
    print("\n" + "="*70)
    print(f"FOUND {len(result['properties'])} PROPERTIES")
    print("="*70)
    
    # Print top 5 properties
    for i, prop in enumerate(result['properties'][:5], 1):
        print(f"\n{i}. {prop.get('title', 'No title')}")
        print(f"   Price: €{prop.get('buyingPrice', 0):,}")
        print(f"   Size: {prop.get('squareMeter', 0)} m²")
        print(f"   Rooms: {prop.get('rooms', 'N/A')}")
        print(f"   Location: {prop.get('zip', '')} {prop.get('address', {}).get('city', '')}")
        print(f"   Match Score: {prop.get('match_score', 0):.2f}")
        print(f"   Features: Balcony={prop.get('balcony', False)}, Garden={prop.get('garden', False)}")
 
if __name__ == '__main__':
    test_analysis()