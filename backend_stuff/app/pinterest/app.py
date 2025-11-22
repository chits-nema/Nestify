# app.py - Flask API for Pinterest Property Analyzer
from flask import Flask, request, jsonify
from flask_cors import CORS
from pinterest_backend import PinterestPropertyAnalyzer
import os

app = Flask(__name__)
CORS(app)

# Get FREE Hugging Face API key from environment (optional)
HF_API_KEY = os.environ.get('HF_API_KEY', '')

if not HF_API_KEY:
    print("⚠️  WARNING: HF_API_KEY not set (optional)")
    print("Get a FREE token from: https://huggingface.co/settings/tokens")
    print("Then run: export HF_API_KEY='your_token_here'")
else:
    print("✅ Hugging Face API key loaded!")

# Initialize analyzer
analyzer = PinterestPropertyAnalyzer(HF_API_KEY)

def convert_to_rss_url(url: str) -> str:
    """Convert Pinterest board URL to RSS URL"""
    url = url.rstrip('/')
    
    # Check if it's already an RSS URL
    if url.endswith('.rss'):
        return url
    
    # Convert regular Pinterest board URL to RSS
    if 'pinterest.com' in url and not url.endswith('.rss'):
        return f"{url}.rss"
    
    raise ValueError("Invalid Pinterest URL. Please provide a valid Pinterest board URL.")

@app.route('/api/analyze-board', methods=['POST'])
def analyze_board():
    """
    Endpoint to analyze Pinterest board and find matching properties
    
    Request body:
    {
        "board_url": "https://www.pinterest.com/username/board-name/",
        "city": "München"
    }
    
    Response:
    {
        "success": true,
        "data": {
            "board_context": {...},
            "feature_scores": {...},
            "properties": [...],
            "total_properties": 20
        }
    }
    """
    try:
        data = request.json
        
        # Validate input
        board_url = data.get('board_url')
        city = data.get('city')
        
        if not board_url:
            return jsonify({
                'success': False,
                'error': 'board_url is required'
            }), 400
        
        if not city:
            return jsonify({
                'success': False,
                'error': 'city is required'
            }), 400
        
        # Convert to RSS URL
        try:
            rss_url = convert_to_rss_url(board_url)
            print(f"📌 Converted {board_url} -> {rss_url}")
        except ValueError as e:
            return jsonify({
                'success': False,
                'error': str(e)
            }), 400
        
        # Build location object
        location = {'city': city}
        
        # Process the Pinterest board
        print(f"🔍 Analyzing board for {city}...")
        result = analyzer.process_pinterest_board(rss_url, location)
        
        # Return successful response
        return jsonify({
            'success': True,
            'data': {
                'board_context': result.get('board_context', {}),
                'feature_scores': result.get('feature_scores', {}),
                'properties': result.get('properties', []),
                'total_properties': result.get('total_properties', 0),
                'search_params': {
                    k: v for k, v in result.get('search_payload', {}).items() 
                    if k != '_metadata'
                }
            }
        })
        
    except Exception as e:
        # Log the full error for debugging
        import traceback
        traceback.print_exc()
        
        return jsonify({
            'success': False,
            'error': f'An error occurred: {str(e)}'
        }), 500

@app.route('/api/health', methods=['GET'])
def health():
    """
    Health check endpoint
    """
    return jsonify({
        'status': 'healthy',
        'service': 'Pinterest Property Analyzer',
        'hf_api_configured': bool(HF_API_KEY)
    })

@app.route('/api/test', methods=['GET'])
def test():
    """
    Simple test endpoint to verify API is running
    """
    return jsonify({
        'message': 'API is working!',
        'endpoints': {
            'analyze': '/api/analyze-board (POST)',
            'health': '/api/health (GET)',
            'test': '/api/test (GET)'
        }
    })

# Error handlers
@app.errorhandler(404)
def not_found(e):
    return jsonify({
        'success': False,
        'error': 'Endpoint not found'
    }), 404

@app.errorhandler(500)
def internal_error(e):
    return jsonify({
        'success': False,
        'error': 'Internal server error'
    }), 500

if __name__ == '__main__':
    print("="*70)
    print("🏠 FOREVER HOME FINDER - Pinterest Property Analyzer API")
    print("="*70)
    print(f"Starting server...")
    print(f"HF API Key configured: {bool(HF_API_KEY)}")
    print()
    print("Available endpoints:")
    print("  POST   http://localhost:5000/api/analyze-board")
    print("  GET    http://localhost:5000/api/health")
    print("  GET    http://localhost:5000/api/test")
    print()
    print("Example request:")
    print("""
    curl -X POST http://localhost:5000/api/analyze-board \\
      -H "Content-Type: application/json" \\
      -d '{
        "board_url": "https://www.pinterest.com/username/board/",
        "city": "München"
      }'
    """)
    print("="*70)
    
    # Run Flask app
    app.run(debug=True, host='0.0.0.0', port=5000)