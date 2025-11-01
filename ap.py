from flask import Flask, render_template, jsonify, request
from image_detect_api import  run_webcam_detection
# Create Flask app
app = Flask(__name__)

# ----- Routes -----

@app.route('/')
def home():
    return render_template("templates.html")
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

@app.route("/api/start_model")
def start_model():
    # Replace this with your model startup logic
    return jsonify({"message": "Model started successfully!"})

@app.route("/api/request")
def make_request():
    # Replace this with whatever your model does
    return jsonify({"message": "Request sent successfully!"})

# ----- Run server -----
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
 