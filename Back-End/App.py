# app.py
import os
import osmnx as ox
from flask import Flask, request, jsonify
from flask_cors import CORS
from ev_solver import solve
from google.cloud import storage
import tempfile
app = Flask(__name__)
# Configure CORS to allow requests from frontend
CORS(app)

def is_local():
    """Detect if running locally or in the cloud."""
    # Option 1: Explicit env variable (most reliable)
    env = os.getenv("APP_ENV", "local")  # default to local if not set
    return env == "local"

# --- Graph Loading Logic ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
GRAPH_PATH = os.path.join(BASE_DIR, "Data", "algeria_roads.graphml")

def load_graph():
    return ox.load_graphml(GRAPH_PATH)

def download_graph():
    client = storage.Client()
    bucket = client.bucket('ev-planner-data')
    blob = bucket.blob('algeria_roads.graphml')
    
    tmp_path = '/tmp/tunisia_major.graphml'
    blob.download_to_filename(tmp_path)
    return ox.load_graphml(tmp_path)
print("Loading graph data... Please wait.")
try:
    if is_local():
        print("Local environment detected → loading from disk.")
        G = load_graph()
    else:
        print("Cloud environment detected → downloading from GCS.")
        G = download_graph()
    print("Graph loaded successfully!")
except Exception as e:
    print(f"Error loading graph: {e}")
    G = None
# ---------------------------


@app.route('/api/route', methods=['POST', 'OPTIONS'])
def get_route():
    """
    Route planning endpoint.
    """
    print("=== Request received ===")  
    print("Method:", request.method)
    print("Headers:", dict(request.headers))
    if request.method =='OPTIONS':
        return jsonify({}), 200
    
    try:
        data = request.get_json()
        print("Raw body:", data)  # see exactly what's coming in

        # Validate required fields
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400

        start_address = data.get('start')
        end_address = data.get('end')
        battery_level = data.get('battery_level')
        search_strategy = data.get('search_strategy')

        # Validation
        if not all([start_address, end_address, battery_level, search_strategy]):
            return jsonify({
                'error': 'Missing required fields: start, end, battery_level, search_strategy'
            }), 400

        # Validate search strategy
        valid_strategies = ['Greedy', 'BFS', 'A*']
        if search_strategy not in valid_strategies:
            return jsonify({
                'error': f'Invalid search strategy. Must be one of: {", ".join(valid_strategies)}'
            }), 400

        # Validate battery level
        try:
            battery_pct = float(battery_level)
            if not (0 <= battery_pct <= 100):
                return jsonify({'error': 'Battery level must be between 0 and 100'}), 400
        except ValueError:
            return jsonify({'error': 'Battery level must be a number'}), 400
        print("================================================================")
        print(f'Route request: {start_address} -> {end_address}, Strategy: {search_strategy}, Battery: {battery_pct}%')



        result = solve(start_address,end_address,search_strategy,float(battery_level),G,0.16125)
        if result is None:
            return jsonify({'error': 'No path found'}), 404

        return jsonify(result), 200

    except ValueError as e:
        # Address resolution error
        error_msg = str(e)
        print(f'Address Error: {error_msg}')
        return jsonify({'error': error_msg}), 400
    except Exception as e:
        print(f'Error in /api/route: {str(e)}')
        return jsonify({'error': str(e)}), 500


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({'status': 'healthy'}), 200


if __name__ == '__main__':
    app.run(debug=True, host='localhost', port=5000)
