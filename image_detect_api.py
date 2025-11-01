from ultralytics import YOLO
import cv2
import random
import requests
import time
import threading

# ----- CONFIG -----
MODEL_NAME = "yolov8n.pt"
MAX_OBJECTS_PER_FRAME = 10
STATE_UPDATE_INTERVAL = 2  # seconds between state updates
API_ENDPOINT = "http://10.121.54.137:8000/"  # Replace with your API

# ----- Load YOLO model ----
model = YOLO(MODEL_NAME)

# this will store the latest frame for the web
latest_frame = None

# event to stop the loop from Flask
stop_event = threading.Event()

class DetectionState:
    """
    Simple class to hold the latest detected objects.
    """
    def __init__(self):
        self.detected_objects = {}  # dictionary: object name -> count
        self.latest_frame = None

    def update(self, results, model):
        """
        Update the state with YOLO results by merging counts
        instead of overwriting.
        """
        new_detections = self._extract_objects(results, model)
        self._merge_detections(new_detections)

    def new_frame(self, frame):
        self.latest_frame = frame

    def _extract_objects(self, results, model):
        """
        Helper: extract detected objects as a dictionary from YOLO results.
        """
        detected_objects = {}
        for r in results:
            for cls_idx in r.boxes.cls:
                name = model.names[int(cls_idx)]
                detected_objects[name] = detected_objects.get(name, 0) + 1
        return detected_objects

    def _merge_detections(self, new_detections):
        """
        Merge a new detection dictionary into the current state.
        """
        for name, count in new_detections.items():
            self.detected_objects[name] = self.detected_objects.get(name, 0) + count


    def pick_random_objects(self, max_objects):
        """
        Pick up to max_objects random keys from the detected objects dict.
        """
        if not self.detected_objects:
            return []
        all_objects = list(self.detected_objects.keys())
        return random.sample(all_objects, min(max_objects, len(all_objects)))

    def get_state(self):
        return self.detected_objects

state = DetectionState()

# ------ Getters -------
def get_current_objects():
    return state.get_state()

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

def get_latest_frame():
    return state.latest_frame

def stop_detection():
    stop_event.set()
    state.new_frame(None)
    

# ----- Functions -----
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
    latest_frame = None
    # clear stop signal when starting
    stop_event.clear()

    cap = open_webcam()
    print("Press 'q' to quit...")
    
    STATE_UPDATE_INTERVAL = 2  # seconds
    last_update_time = 0  # track last update


    while True:
        ret, frame = cap.read()
        if not ret:
            print("Error: Failed to capture frame.")
            break

        # Run YOLO detection
        results = model(frame, verbose=True)

        # --- Only update state every 2 seconds ---
        current_time = time.time()
        if current_time - last_update_time >= STATE_UPDATE_INTERVAL:
            state.update(results, model)  # update detection state
            last_update_time = current_time
            print("Updated state:", state.get_state())

        # Display annotated frame
        annotated_frame = results[0].plot()
        cv2.imshow("YOLO Detection", annotated_frame)            

        # Draw detections
        annotated_frame = results[0].plot()
        latest_frame = annotated_frame
        state.new_frame(latest_frame)
        #state.latest_frame = latest_frame
        cv2.imshow("YOLO Webcam Detection", annotated_frame)
        cv2.waitKey(1)

        # Quit on 'q'
        #if cv2.waitKey(1) & 0xFF == ord('q'):
            #break

    
    cap.release()
    cv2.destroyAllWindows()

# ----- Entry point -----
#if __name__ == "__main__":
    #run_webcam_detection()
