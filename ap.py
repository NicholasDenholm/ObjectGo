from flask import Flask, jsonify, request
from image_detect_api import  run_webcam_detection
# Create Flask app
app = Flask(__name__)

# ----- Routes -----

@app.route('/')
def home():
    return "Hello, Flask is running!"

@app.route('/api/objects', methods=['POST'])
def receive_objects():
    """
    Example API endpoint to receive detected objects.
    Expects JSON payload like: {"objects": ["person", "bicycle"]}
    """
    run_webcam_detection()
    data = request.get_json()
    if not data or "objects" not in data:
        return jsonify({"error": "No objects provided"}), 400

    objects = data["objects"]
    # Example: just echo back the received objects
    return jsonify({"received_objects": objects}), 200

# ----- Run server -----
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
 