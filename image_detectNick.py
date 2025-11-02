from ultralytics import YOLO
import cv2
import random
import requests
import time
import threading
import pyautogui

import yaml

# ----- CONFIG -----
MODEL_NAME = "yolov8n.pt"
MAX_OBJECTS_PER_FRAME = 10
STATE_UPDATE_INTERVAL = 2  # seconds between state updates

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
        self.previous_objects = {}  # store last detected counts
        self.text_mapping = {}

    def update(self, results, model):
        """
        Update the state with YOLO results by merging counts
        instead of overwriting.
        """
        #new_detections = self._extract_objects(results, model)
        #self._merge_detections(new_detections)
        confidence_threshold = 0.5
        new_detections = self._extract_objects_conf(results, model, confidence_threshold)
        self._merge_detections_conf(new_detections)

    def new_frame(self, frame):
        self.latest_frame = frame

    def _extract_objects_conf(self, results, model, confidence_threshold):
        """
        Extract detected objects as {object_name: [confidences]} from YOLO results.
        """
        detected_objects = {}
        for r in results:
            for cls_idx, conf in zip(r.boxes.cls, r.boxes.conf):
                name = model.names[int(cls_idx)]
                conf_value = round (float(conf.item()), 2)  # convert tensor to float
                if conf_value > confidence_threshold:
                    detected_objects[name] = conf_value  # keep only latest
                #detected_objects.setdefault(name, []).append(conf_value) #append to a running list
        return detected_objects
        
    def _merge_detections_conf(self, new_detections):
        """
        Merge new detections into the current state.
        Replaces old confidence values with the latest ones.
        """
        for name, conf_value in new_detections.items():
            self.detected_objects[name] = conf_value

    def _merge_detections_conf_runninglist(self, new_detections):
        """
        Merge a new detection dictionary into the current state,
        appending confidence scores for existing objects.
        """
        for name, conf_list in new_detections.items():
            if name in self.detected_objects:
                self.detected_objects[name].extend(conf_list)
            else:
                self.detected_objects[name] = conf_list

    def _extract_objects_count(self, results, model):
        """
        Helper: extract detected objects as a dictionary from YOLO results.
        """
        detected_objects = {}
        for r in results:
            for cls_idx in r.boxes.cls:
                name = model.names[int(cls_idx)]
                detected_objects[name] = detected_objects.get(name, 0) + 1
        return detected_objects

    def _merge_detections_count(self, new_detections):
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


state = DetectionState()

# ------ Getters -------
def get_current_objects():
    return state.detected_objects

def get_text_mapping():
    return state.text_mapping

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
    state.detected_objects = {}
    state.previous_objects = {}
    state.new_frame(None)
    

# ----- Setup Functions -----
def open_webcam(cam_index=0):
    """
    Open webcam and return capture object.
    """
    cap = cv2.VideoCapture(cam_index)
    if not cap.isOpened():
        raise RuntimeError("Error: Could not open webcam.")
    return cap

def compute_change_ratio(old, new):
    """Compute the ratio of change between two detection dicts."""
    all_keys = set(old.keys()) | set(new.keys())
    total_diff = sum(abs(new.get(k, 0) - old.get(k, 0)) for k in all_keys)
    total_old = sum(old.values()) or 1
    return total_diff / total_old


def get_object_counts(results, model):
    """Return a dictionary of detected object counts from YOLO results."""
    counts = {}
    for r in results:
        for cls_idx in r.boxes.cls:
            name = model.names[int(cls_idx)]
            counts[name] = counts.get(name, 0) + 1
    return counts


def display_frame(window_name, results):
    """Display the annotated YOLO frame."""
    annotated = results[0].plot()
    cv2.imshow(window_name, annotated)
    return annotated


# ----- Object to text -----
def load_objects_to_text():

    with open("objects.yaml", "r") as f:
        object_key_map_total = yaml.safe_load(f)

    # Merge all categories into a single dictionary
    object_key_map = {}
    for category in object_key_map_total.values():  # letters, numbers, punctuation, keywords
        object_key_map.update(category)
    state.text_mapping = object_key_map

def send_keypress_for_objects(objects):
    for obj_name in objects:
        if obj_name in state.text_mapping:
            key = state.text_mapping[obj_name]
            print(f"Detected {obj_name} → typing '{key}'")
            pyautogui.typewrite(key)
        else:
            print(f"Detected {obj_name} → no mapped key")




# ----- Main Loop -----

def run_webcam_detection():
    """
    Capture webcam frames, detect objects with YOLO, update state periodically,
    and show annotated video until stop_event is set.
    """
    latest_frame = None
    stop_event.clear()

    load_objects_to_text()
    cap = open_webcam()
    print("Press 'q' to quit...")

    STATE_UPDATE_INTERVAL = 5  # seconds
    last_update_time = 0

    while not stop_event.is_set():
        ret, frame = cap.read()
        if not ret:
            print("Error: Failed to capture frame.")
            break

        # Run YOLO detection
        results = model(frame, verbose=True)
        current_objects = get_object_counts(results, model)

        # Compute change ratio vs previous detections
        ratio = compute_change_ratio(state.previous_objects, current_objects)
        current_time = time.time()

        # Update only if significant change or interval elapsed
        if ratio > 0.2 or (current_time - last_update_time >= STATE_UPDATE_INTERVAL):
            state.update(results, model)
            last_update_time = current_time
            state.previous_objects = current_objects
            print(f"Updated state ({ratio*100:.1f}% change):", state.get_state())

        # Display annotated frame
        latest_frame = display_frame("YOLO Webcam Detection", results)
        state.new_frame(latest_frame)

        # Handle window updates
        cv2.waitKey(1)

    cap.release()
    cv2.destroyAllWindows()
