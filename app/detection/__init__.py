from ultralytics import YOLO
import os

CRIME_RELEVANT_LABELS = {
    'knife', 'gun', 'person', 'cell phone', 'handbag',
    'backpack', 'bottle', 'scissors', 'car', 'truck'
}

class CrimeSceneDetector:
    _instance = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self, model_path='yolov8n.pt'):
        print(f'Loading YOLO model from {model_path}...')
        self.model = YOLO(model_path)
        print('Model loaded!')

    def detect(self, image_path, confidence_threshold=0.40):
        if not os.path.exists(image_path):
            raise FileNotFoundError(f'Image not found: {image_path}')

        results = self.model(image_path, conf=confidence_threshold, verbose=False)
        detections = []

        for result in results:
            img_h, img_w = result.orig_shape

            for box in result.boxes:
                label = result.names[int(box.cls)]
                confidence = float(box.conf)
                x1, y1, x2, y2 = box.xyxy[0].tolist()

                detections.append({
                    'label': label,
                    'confidence': round(confidence, 4),
                    'x': round(x1 / img_w, 4),
                    'y': round(y1 / img_h, 4),
                    'width': round((x2 - x1) / img_w, 4),
                    'height': round((y2 - y1) / img_h, 4),
                    'x1_px': int(x1), 'y1_px': int(y1),
                    'x2_px': int(x2), 'y2_px': int(y2),
                })

        return detections