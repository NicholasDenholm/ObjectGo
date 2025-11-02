from flask import Flask, render_template, Response, jsonify, request
import image_detect_api, image_detectNick 
import threading
import cv2
import time
import pyautogui
# Create Flask app
app = Flask(__name__)

# flag / handle for the background thread
detection_thread = None
detection_running = False


# ----- Routes -----

@app.route('/')
def home():
    return render_template("homepage.html")
'''
@app.route('/objtotext1')
def objToText():
    return render_template('Obj_to_text.html')
'''
@app.route('/objtotext2')
def objToText():
    return render_template('object_to_text.html')

# ----- Buttons ------

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

# ----- Typing ------

# Make sure your text mapping is loaded at startup
image_detectNick.load_objects_to_text()

@app.route("/type_objects", methods=["POST"])
def type_objects():
    text_mapping = image_detectNick.get_text_mapping()
    data = request.json
    detected_objects = data.get("objects", [])
    typed_keys = []

    for obj_name in detected_objects:
        key = text_mapping.get(obj_name)
        if key:
            typed_keys.append(key)
            print(f"Detected {obj_name} → typing '{key}'")
            # pyautogui.typewrite(key)  # optional
        else:
            print(f"Detected {obj_name} → no mapped key")
            typed_keys.append("")

    return jsonify({"typed_keys": typed_keys})

@app.route("/type_object/<obj_name>", methods=["POST"])
def type_object(obj_name):
    mapping = image_detectNick.get_text_mapping()
    
    # COMPREHENSIVE DEBUG LOGGING
    print("\n" + "="*50)
    print(f"🔍 DEBUGGING /type_object/<obj_name>")
    print("="*50)
    print(f"📥 Received object name: '{obj_name}'")
    print(f"📥 Object name type: {type(obj_name)}")
    print(f"📥 Object name length: {len(obj_name)}")
    print(f"📥 Object name repr: {repr(obj_name)}")
    print(f"\n📚 Full mapping dictionary:")
    for key, value in mapping.items():
        print(f"   '{key}' -> '{value}'")
    print(f"\n🔑 All mapping keys: {list(mapping.keys())}")
    print(f"🔑 Number of mappings: {len(mapping)}")
    
    # Try to find the key
    typed_key = mapping.get(obj_name, "")
    
    print(f"\n🎯 Looking up '{obj_name}' in mapping...")
    print(f"✅ Found: {obj_name in mapping}")
    print(f"📝 Typed key result: '{typed_key}'")
    print("="*50 + "\n")
    
    if typed_key:
        print(f"✓ SUCCESS: Detected {obj_name} → typing '{typed_key}'")
        # pyautogui.typewrite(typed_key)  # optional while debugging
    else:
        print(f"✗ FAILED: No mapping found for '{obj_name}'")
        # Try case-insensitive match
        for key in mapping.keys():
            if key.lower() == obj_name.lower():
                print(f"⚠️  HINT: Found case mismatch! '{key}' exists but you sent '{obj_name}'")

    return jsonify({"typed_key": typed_key, "object_received": obj_name})

'''
@app.route("/type_objects", methods=["POST"])
def type_objects():
    text_mapping = image_detectNick.get_text_mapping()
    data = request.json
    detected_objects = data.get("objects", [])
    typed_keys = []

    for obj_name in detected_objects:
        if obj_name in text_mapping:
            key = text_mapping[obj_name]
            typed_keys.append(key)
            pyautogui.typewrite(key)
        else:
            typed_keys.append("")  # or skip unmapped objects

    return jsonify({"typed_keys": typed_keys})

@app.route('/type_object/<obj_name>', methods=['POST'])
def type_object(obj_name):
    mapping = image_detectNick.get_text_mapping()
    typed_key = mapping.get(obj_name, "")
    if typed_key:
        # Optional: also trigger pyautogui typing if you want real keyboard input
        pyautogui.typewrite(typed_key)
        print(f"Detected {obj_name} → typing '{typed_key}'")
    return jsonify({"typed_key": typed_key})
'''

# ----- Object Info ------

@app.route('/api/get_objects', methods=['GET'])
def get_objects():
    """
    Return current detected objects from your YOLO pipeline
    """
    current_objects = image_detectNick.get_current_objects()  # e.g., ['person', 'cup']
    return jsonify({"objects": current_objects}), 200


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
 