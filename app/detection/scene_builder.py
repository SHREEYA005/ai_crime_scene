import json
import os
from app.detection.opencv_processor import SceneProcessor


def build_scene_json(case, output_path):
    processor = SceneProcessor()
    all_objects = []
    object_id = 1

    for evidence in case.evidence:
        if evidence.file_type not in ['jpg', 'jpeg', 'png']:
            continue
        if not evidence.annotations:
            continue

        ann_dicts = [{
            'id': a.id, 'label': a.label,
            'x': a.x, 'y': a.y, 'width': a.width, 'height': a.height,
            'confidence': a.confidence, 'source': a.source
        } for a in evidence.annotations]

        try:
            result = processor.process(evidence.file_path, ann_dicts)
            for obj in result['objects']:
                obj['id'] = object_id
                obj['evidence_id'] = evidence.id
                all_objects.append(obj)
                object_id += 1
        except Exception as e:
            print(f'Warning: could not process evidence {evidence.id}: {e}')

    scene_json = {
        'case_id': case.case_number,
        'case_title': case.title,
        'room_dimensions': {'width': 6.0, 'height': 3.0, 'depth': 8.0},
        'objects': all_objects,
        'total_objects': len(all_objects)
    }

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(scene_json, f, indent=2)

    return scene_json
