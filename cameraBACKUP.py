import cv2
import numpy as np
from keras.models import load_model
from ultralytics import YOLO

# Load YOLOv8 model
yolo_model = YOLO('yolov8n.pt')

# Load pre-trained emotion recognition model
emotion_model = load_model('model_file_custom_5.h5')

# Labels for emotion recognition
labels_dict = {0: 'Angry', 1: 'Disgust', 2: 'Fear', 3: 'Happy', 4: 'Sad', 5: 'Surprise'}

class Video(object):
    def __init__(self):
        self.video = cv2.VideoCapture(0)

    def __del__(self):
        self.video.release()

    def get_frame(self):
        ret, frame = self.video.read()
        obj_info = []

        if not ret:
            print("Failed to read frame from the video capture")
            return None

        # Detect objects using YOLOv8
        results = yolo_model.track(frame, save=False, classes=[0], conf=0.5, persist=True)

        # Process the detected objects
        if len(results) > 0:
            for result in results:
                if result.boxes.id is not None and len(result.boxes.id) > 0:
                    for obj_id in result.boxes.id:
                        # Get the bounding box coordinates
                        boxes = result.boxes.xyxy
                        bbox = boxes[result.boxes.id == obj_id][0]
                        x1, y1, x2, y2 = int(bbox[0]), int(bbox[1]), int(bbox[2]), int(bbox[3])

                        # Extract the object region
                        object_img = frame[y1:y2, x1:x2]

                        # Preprocess the object image for emotion recognition
                        gray = cv2.cvtColor(object_img, cv2.COLOR_BGR2GRAY)
                        resized = cv2.resize(gray, (48, 48))
                        normalized = resized / 255.0
                        reshaped = np.reshape(normalized, (1, 48, 48, 1))

                        # Predict the emotion
                        emotion_result = emotion_model.predict(reshaped)
                        emotion_label = np.argmax(emotion_result, axis=1)[0]
                        emotion_text = labels_dict[emotion_label]

                        # Append ID and emotion to obj_info list
                        obj_info.append(f"ID: {obj_id}, Emotion: {emotion_text}")

                        # Draw bounding box and emotion label
                        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                        cv2.putText(frame, f"ID: {obj_id}, Emotion: {emotion_text}", (x1, y1 - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (36, 255, 12), 2)

        ret, jpg = cv2.imencode('.jpg', frame)
        return jpg.tobytes(), obj_info
