# app.py
from flask import Flask, request, jsonify
from flask_cors import CORS
from pinterest_backend import PinterestPropertyAnalyzer
import os

app = Flask(__name__)
CORS(app)

# Get API key from environment variable
GOOGLE_VISION_API_KEY = os.environ.get('GOOGLE_VISION_API_KEY')

if not GOOGLE_VISION_API_KEY:
    print("⚠️  WARNING: GOOGLE_VISION_API_KEY not set!")
    print("Set it with: export GOOGLE_VISION_API_KEY='your-api-key'")

# Initialize analyzer with API key
analyzer = PinterestPropertyAnalyzer(GOOGLE_VISION_API_KEY)

def convert_to_rss_url(url: str) -> str:
    """Convert Pinterest board URL to RSS URL"""
    url = url.rstrip('/')
    
    if url.endswith('.rss'):
        return url
    
    if 'pinterest.com' in url and not url.endswith('.rss'):
        return f"{url}.rss"
    
    raise ValueError("Invalid Pinterest URL. Please provide a board URL.")

@app.route('/api/analyze-board', methods=['POST'])
def analyze_board():
    """
    Endpoint to analyze Pinterest board
    
    Request body:
    {
        "board_url": "https://www.pinterest.com/username/board-name/",
        "city": "München"
    }
    """
    try:
        data = request.json
        board_url = data.get('board_url')
        city = data.get('city')
        
        if not board_url:
            return jsonify({'error': 'board_url is required'}), 400
        
        if not city:
            return jsonify({'error': 'city is required'}), 400
        
        # Convert to RSS URL
        try:
            rss_url = convert_to_rss_url(board_url)
            print(f"Converted {board_url} -> {rss_url}")
        except ValueError as e:
            return jsonify({'error': str(e)}), 400
        
        location = {'city': city}
        
        # Process the board
        result = analyzer.process_pinterest_board(rss_url, location)
        
        return jsonify({
            'success': True,
            'data': {
                'feature_scores': result['feature_scores'],
                'properties': result['properties'],
                'total_properties': result['total_properties'],
                'search_payload': {k: v for k, v in result['search_payload'].items() 
                                 if k != '_metadata'}
            }
        })
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({
        'status': 'healthy',
        'vision_api_configured': bool(GOOGLE_VISION_API_KEY)
    })

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)