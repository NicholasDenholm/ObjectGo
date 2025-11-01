from ultralytics import YOLO
import cv2
import random
import requests

# ----- CONFIG -----
MODEL_NAME = "yolov8n.pt"
MAX_OBJECTS_PER_FRAME = 3
API_ENDPOINT = "https://example.com/api/objects"  # Replace with your API

# ----- Load YOLO model ----
model = YOLO(MODEL_NAME)

# ----- Functions -----
def get_detected_objects_dict(results, model):
    """
    Extract detected objects from YOLO results and return a dictionary
    with object names as keys and their counts as values.
    """
    detected_objects = {}
    for r in results:
        for cls_idx in r.boxes.cls:
            name = model.names[int(cls_idx)]
            detected_objects[name] = detected_objects.get(name, 0) + 1
    return detected_objects

def pick_random_objects(detected_dict, max_objects):
    """
    Pick up to max_objects random keys from the detected objects dict.
    """
    if not detected_dict:
        return []
    all_objects = list(detected_dict.keys())
    return random.sample(all_objects, min(max_objects, len(all_objects)))

def send_to_api(objects_list):
    """
    Send selected objects to API endpoint as JSON payload.
    """
    if not objects_list:
        return
    payload = {"objects": objects_list}
    try:
        response = requests.post(API_ENDPOINT, json=payload)
        if response.ok:
            print("API response:", response.json())
        else:
            print("API call failed with status code:", response.status_code)
    except Exception as e:
        print("Error sending API request:", e)

def open_webcam(cam_index=0):
    """
    Open webcam and return capture object.
    """
    cap = cv2.VideoCapture(cam_index)
    if not cap.isOpened():
        raise RuntimeError("Error: Could not open webcam.")
    return cap

def run_webcam_detection():
    """
    Main loop: capture frames, detect objects, pick random objects,
    send to API, and display annotated frame.
    """
    cap = open_webcam()
    print("Press 'q' to quit...")

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Error: Failed to capture frame.")
            break

        # Run YOLO detection
        results = model(frame, verbose=True)

        # Extract objects as dictionary
        detected_objects_dict = get_detected_objects_dict(results, model)
        if detected_objects_dict:
            print("Detected objects:", detected_objects_dict)

            # Pick random objects
            random_objects = pick_random_objects(detected_objects_dict, MAX_OBJECTS_PER_FRAME)
            print("Random objects selected:", random_objects)

            # Send to API
            #send_to_api(random_objects)

        # Draw detections
        annotated_frame = results[0].plot()
        cv2.imshow("YOLO Webcam Detection", annotated_frame)

        # Quit on 'q'
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

# ----- Entry point -----
if __name__ == "__main__":
    run_webcam_detection()
