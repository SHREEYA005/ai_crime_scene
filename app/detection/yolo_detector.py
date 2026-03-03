from ultralytics import YOLO
import os


class CrimeSceneDetector:
    _instance = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self, model_path='yolov8n.pt'):
        print(f'Loading YOLO model...')
        self.model = YOLO(model_path)
        print('Model ready.')

    def detect(self, image_path, confidence_threshold=0.40):
        if not os.path.exists(image_path):
            raise FileNotFoundError(f'Image not found: {image_path}')

        results = self.model(image_path, conf=confidence_threshold, verbose=False)
        detections = []

        for result in results:
            img_h, img_w = result.orig_shape
            for box in result.boxes:
                x1, y1, x2, y2 = box.xyxy[0].tolist()
                detections.append({
                    'label': result.names[int(box.cls)],
                    'confidence': round(float(box.conf), 4),
                    'x': round(x1 / img_w, 4),
                    'y': round(y1 / img_h, 4),
                    'width': round((x2 - x1) / img_w, 4),
                    'height': round((y2 - y1) / img_h, 4),
                })

        return detections
