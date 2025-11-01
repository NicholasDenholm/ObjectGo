from ultralytics import YOLO
import cv2

# Load pretrained YOLOv8n model (trained on COCO)
model = YOLO("yolov8n.pt")

# Open default webcam (0)
cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print("Error: Could not open webcam.")
    exit()

print("Press 'q' to quit...")

while True:
    ret, frame = cap.read()
    if not ret:
        print("Error: Failed to capture frame.")
        break

    # Run YOLO detection on the frame
    results = model(frame)

    # Render results on the frame
    annotated_frame = results[0].plot()  # returns numpy array with boxes & labels

    # Display the frame
    cv2.imshow("YOLO Webcam Detection", annotated_frame)

    # Quit on 'q' key
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Release resources
cap.release()
cv2.destroyAllWindows()
