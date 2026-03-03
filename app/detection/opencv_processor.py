import cv2
import numpy as np
import os


class SceneProcessor:

    def process(self, image_path, annotations, room_width=6.0, room_depth=8.0):
        if not os.path.exists(image_path):
            raise FileNotFoundError(f'Image not found: {image_path}')

        img = cv2.imread(image_path)
        img_h, img_w = img.shape[:2]
        floor_y = self._estimate_floor_line(img)

        scene_objects = []
        for ann in annotations:
            cx = ann['x'] + ann['width'] / 2
            cy = ann['y'] + ann['height'] / 2
            bottom_y = ann['y'] + ann['height']

            depth_ratio = min(bottom_y / max(floor_y, 0.01), 1.0)
            x_3d = (cx - 0.5) * room_width
            z_3d = depth_ratio * room_depth

            scene_objects.append({
                'label': ann['label'],
                'annotation_id': ann.get('id'),
                'confidence': ann.get('confidence'),
                'source': ann.get('source', 'manual'),
                'position': {'x': round(x_3d, 2), 'y': 0.0, 'z': round(z_3d, 2)},
                'rotation': {'x': 0, 'y': 0, 'z': 0},
                'prefab': self._get_prefab_name(ann['label'])
            })

        return {
            'room_dimensions': {'width': room_width, 'height': 3.0, 'depth': room_depth},
            'objects': scene_objects
        }

    def _estimate_floor_line(self, img):
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray, 50, 150)
        h = edges.shape[0]
        bottom = edges[int(h * 0.6):, :]
        row_sums = np.sum(bottom, axis=1)
        if row_sums.max() > 0:
            return (int(h * 0.6) + np.argmax(row_sums)) / h
        return 0.75

    def _get_prefab_name(self, label):
        mapping = {
            'knife': 'Knife_01', 'gun': 'Handgun_01', 'person': 'PersonOutline_01',
            'bloodstain': 'Bloodstain_01', 'footprint': 'Footprint_01',
            'shell_casing': 'ShellCasing_01', 'handgun': 'Handgun_01',
            'bottle': 'Bottle_01', 'cell phone': 'Phone_01',
        }
        return mapping.get(label.lower(), 'EvidenceMarker_Default')
