from flask import Flask, render_template, Response, jsonify, request
import image_detect_api 
import threading
import cv2
import time
# Create Flask app
app = Flask(__name__)

# flag / handle for the background thread
detection_thread = None
detection_running = False


# ----- Routes -----

@app.route('/')
def home():
    return render_template("templates.html")
    return "Hello, Flask is running!"

@app.route("/api/start_model")
def start_model():
    global detection_thread, detection_running

    # already running → just tell frontend
    if detection_running:
        return jsonify({"message": "Model already running."})

    # start background thread
   
    def run_detector():
        global detection_running
        try:
            # this is your loop
            image_detect_api.run_webcam_detection()
        finally:
            # if the loop exits, mark as stopped
            detection_running = False

    detection_thread = threading.Thread(target=run_detector, daemon=True)
    detection_thread.start()

    return jsonify({"message": "Model started successfully!"})

@app.route("/api/stop_model")
def stop_model():
    # we will signal the loop via image_detect_api.stop_event
    image_detect_api.stop_detection()
    return jsonify({"message": "Stop signal sent."})


@app.route("/api/request")
def make_request():
    """
    This is like “give me what the model currently sees”.
    We just read the shared state from image_detect_api.
    """
    current_objects = image_detect_api.get_current_objects()  # returns dict: {"person": 1, "dog": 2}
    return jsonify({
        "message": "Request sent successfully!",
        "objects": current_objects
    })



@app.route('/api/objects', methods=['POST'])
def receive_objects():
    
    """
    Example API endpoint to receive detected objects.
    Expects JSON payload like: {"objects": ["person", "bicycle"]}
    """

    data = request.get_json()
    if not data or "objects" not in data:
        return jsonify({"error": "No objects provided"}), 400

    objects = data["objects"]
    # Example: just echo back the received objects
    return jsonify({"received_objects": objects}), 200

@app.route("/video_feed")
def video_feed():
    def gen_frames():
        while True:
            frame = image_detect_api.get_latest_frame()

            if frame is None:
                # no frame yet → don’t hammer the browser
                time.sleep(0.05)
                continue

            ok, buffer = cv2.imencode(".jpg", frame)
            if not ok:
                time.sleep(0.05)
                continue

            jpg_bytes = buffer.tobytes()
            # send proper multipart chunk
            yield (
                b"--frame\r\n"
                b"Content-Type: image/jpeg\r\n"
                b"Content-Length: " + f"{len(jpg_bytes)}".encode() + b"\r\n\r\n" +
                jpg_bytes + b"\r\n"
            )
            # small cooldown so the browser doesn’t freak out
            time.sleep(0.03)

    return Response(gen_frames(), mimetype="multipart/x-mixed-replace; boundary=frame")


# ----- Run server -----
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
 