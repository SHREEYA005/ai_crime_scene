# Run with: pytest tests/
import pytest

def test_detector_import():
    """Test that the detector module imports correctly"""
    from app.detection.yolo_detector import CrimeSceneDetector
    assert CrimeSceneDetector is not None

def test_scene_processor_import():
    """Test that the scene processor imports correctly"""
    from app.detection.opencv_processor import SceneProcessor
    assert SceneProcessor is not None

def test_prefab_mapping():
    """Test that labels map to prefab names correctly"""
    from app.detection.opencv_processor import SceneProcessor
    processor = SceneProcessor()
    assert processor._get_prefab_name('knife') == 'Knife_01'
    assert processor._get_prefab_name('unknown_thing') == 'EvidenceMarker_Default'
