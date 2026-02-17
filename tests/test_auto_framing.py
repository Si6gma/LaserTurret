"""
Tests for the Auto-Framing module - subject detection and composition.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import pytest
import numpy as np
from auto_framing import AutoFramer, Subject, FramingData


class TestSubject:
    """Test Subject dataclass."""
    
    def test_subject_creation(self):
        """Test creating a Subject."""
        subject = Subject(
            bbox=(100, 100, 50, 50),
            center=(125, 125),
            confidence=0.95,
            subject_type="face"
        )
        
        assert subject.bbox == (100, 100, 50, 50)
        assert subject.center == (125, 125)
        assert subject.confidence == 0.95
        assert subject.subject_type == "face"
    
    def test_subject_area(self):
        """Test area calculation."""
        subject = Subject(
            bbox=(100, 100, 50, 60),
            center=(125, 130),
            confidence=0.9,
            subject_type="body"
        )
        
        assert subject.area == 3000  # 50 * 60


class TestFramingData:
    """Test FramingData dataclass."""
    
    def test_framing_data_defaults(self):
        """Test FramingData default values."""
        data = FramingData(
            detected=True,
            bbox=(100, 100, 50, 50),
            center=(125, 125),
            confidence=0.9
        )
        
        assert data.detected is True
        assert data.optimal_pitch == 90.0  # Default
        assert data.optimal_yaw == 90.0     # Default


class TestAutoFramerInitialization:
    """Test AutoFramer initialization."""
    
    def test_default_initialization(self):
        """Test AutoFramer with default parameters."""
        framer = AutoFramer()
        
        assert framer.smoothing == 0.15
        assert framer.model_type == "yolo"
        assert framer.composition == "center"
        assert framer.headroom_ratio == 0.15
    
    def test_custom_initialization(self):
        """Test AutoFramer with custom parameters."""
        framer = AutoFramer(
            smoothing=0.3,
            model_type="haar",
            composition="rule_of_thirds",
            headroom_ratio=0.2
        )
        
        assert framer.smoothing == 0.3
        assert framer.model_type == "haar"
        assert framer.composition == "rule_of_thirds"
        assert framer.headroom_ratio == 0.2


class TestAutoFramerDetection:
    """Test subject detection functionality."""
    
    def test_detect_faces_haar_empty_frame(self):
        """Test face detection on empty frame returns empty list."""
        framer = AutoFramer(model_type="haar")
        
        # Create blank frame
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        
        subjects = framer._detect_faces_haar(frame)
        
        assert isinstance(subjects, list)
        assert len(subjects) == 0
    
    def test_detect_bodies_hog_empty_frame(self):
        """Test body detection on empty frame returns empty list."""
        framer = AutoFramer(model_type="yolo")
        
        # Create blank frame
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        
        subjects = framer._detect_bodies_hog(frame)
        
        assert isinstance(subjects, list)
        assert len(subjects) == 0
    
    def test_process_frame_no_detection(self):
        """Test processing frame with no subjects."""
        framer = AutoFramer()
        
        # Create blank frame
        frame = np.zeros((720, 1280, 3), dtype=np.uint8)
        
        result = framer.process_frame(frame)
        
        assert isinstance(result, FramingData)
        assert result.detected is False
        assert result.confidence == 0.0
        assert result.center == (640, 360)  # Frame center


class TestAutoFramerComposition:
    """Test composition calculations."""
    
    def test_calculate_framing_centered(self):
        """Test framing calculation for centered composition."""
        framer = AutoFramer(composition="center")
        
        # Subject already centered in 1280x720 frame
        bbox = (590, 310, 100, 100)  # Centered box
        frame_size = (1280, 720)
        
        pitch, yaw = framer.calculate_framing(bbox, frame_size)
        
        # Should be near center (90, 90)
        assert pitch == pytest.approx(90.0, abs=5.0)
        assert yaw == pytest.approx(90.0, abs=5.0)
    
    def test_calculate_framing_subject_right(self):
        """Test framing when subject is to the right."""
        framer = AutoFramer(composition="center")
        
        # Subject to the right of center
        bbox = (900, 310, 100, 100)
        frame_size = (1280, 720)
        
        pitch, yaw = framer.calculate_framing(bbox, frame_size)
        
        # Should adjust yaw to the right (>90)
        assert yaw > 90.0
    
    def test_calculate_framing_subject_left(self):
        """Test framing when subject is to the left."""
        framer = AutoFramer(composition="center")
        
        # Subject to the left of center
        bbox = (280, 310, 100, 100)
        frame_size = (1280, 720)
        
        pitch, yaw = framer.calculate_framing(bbox, frame_size)
        
        # Should adjust yaw to the left (<90)
        assert yaw < 90.0
    
    def test_calculate_framing_subject_above(self):
        """Test framing when subject is above center."""
        framer = AutoFramer(composition="center")
        
        # Subject above center (remember y increases downward in images)
        bbox = (590, 110, 100, 100)
        frame_size = (1280, 720)
        
        pitch, yaw = framer.calculate_framing(bbox, frame_size)
        
        # Subject is above center -> need to tilt up -> pitch increases (inverted logic in source)
        assert pitch > 90.0
    
    def test_calculate_framing_subject_below(self):
        """Test framing when subject is below center."""
        framer = AutoFramer(composition="center")
        
        # Subject below center
        bbox = (590, 510, 100, 100)
        frame_size = (1280, 720)
        
        pitch, yaw = framer.calculate_framing(bbox, frame_size)
        
        # Subject is below center -> need to tilt down -> pitch decreases (inverted logic in source)
        assert pitch < 90.0
    
    def test_calculate_framing_clamped(self):
        """Test framing angles are clamped to valid range."""
        framer = AutoFramer()
        
        # Extreme subject position
        bbox = (-500, -500, 100, 100)
        frame_size = (1280, 720)
        
        pitch, yaw = framer.calculate_framing(bbox, frame_size)
        
        # Should be clamped to [0, 180]
        assert 0.0 <= pitch <= 180.0
        assert 0.0 <= yaw <= 180.0


class TestMultiSubjectFraming:
    """Test multi-subject framing."""
    
    def test_empty_subjects(self):
        """Test multi-subject framing with no subjects."""
        framer = AutoFramer()
        
        pitch, yaw = framer.calculate_multi_subject_framing([], (1280, 720))
        
        assert pitch == 90.0
        assert yaw == 90.0
    
    def test_single_subject(self):
        """Test multi-subject framing with one subject."""
        framer = AutoFramer()
        
        subjects = [
            Subject(bbox=(640, 360, 100, 100), center=(690, 410), confidence=0.9, subject_type="face")
        ]
        
        pitch, yaw = framer.calculate_multi_subject_framing(subjects, (1280, 720))
        
        # Should frame to that subject
        assert 0.0 <= pitch <= 180.0
        assert 0.0 <= yaw <= 180.0
    
    def test_multiple_subjects(self):
        """Test multi-subject framing with multiple subjects."""
        framer = AutoFramer()
        
        subjects = [
            Subject(bbox=(200, 300, 100, 100), center=(250, 350), confidence=0.9, subject_type="face"),
            Subject(bbox=(1000, 400, 100, 100), center=(1050, 450), confidence=0.85, subject_type="face")
        ]
        
        pitch, yaw = framer.calculate_multi_subject_framing(subjects, (1280, 720))
        
        # Should frame to include both (center between them)
        assert 0.0 <= pitch <= 180.0
        assert 0.0 <= yaw <= 180.0
        # Yaw should be between the two subjects (roughly center)
        assert 80.0 <= yaw <= 100.0


class TestDetectionMerging:
    """Test merging face and body detections."""
    
    def test_merge_empty(self):
        """Test merging empty lists."""
        framer = AutoFramer()
        
        merged = framer._merge_detections([], [])
        
        assert merged == []
    
    def test_merge_no_overlap(self):
        """Test merging non-overlapping detections."""
        framer = AutoFramer()
        
        faces = [
            Subject(bbox=(100, 100, 50, 50), center=(125, 125), confidence=0.9, subject_type="face")
        ]
        bodies = [
            Subject(bbox=(500, 500, 100, 200), center=(550, 600), confidence=0.8, subject_type="body")
        ]
        
        merged = framer._merge_detections(faces, bodies)
        
        assert len(merged) == 2
    
    def test_merge_with_overlap(self):
        """Test merging overlapping detections."""
        framer = AutoFramer()
        
        # Face inside body
        faces = [
            Subject(bbox=(150, 150, 50, 50), center=(175, 175), confidence=0.95, subject_type="face")
        ]
        bodies = [
            Subject(bbox=(100, 100, 200, 300), center=(200, 250), confidence=0.8, subject_type="body")
        ]
        
        merged = framer._merge_detections(faces, bodies)
        
        # Should only keep the face (inside the body)
        assert len(merged) == 1
        assert merged[0].subject_type == "face"


class TestTrackingState:
    """Test tracking state management."""
    
    def test_lost_frames_tracking(self):
        """Test lost frames counter increments."""
        framer = AutoFramer()
        
        initial_lost = framer._lost_frames
        
        # Process empty frames
        frame = np.zeros((720, 1280, 3), dtype=np.uint8)
        framer.process_frame(frame)
        framer.process_frame(frame)
        
        assert framer._lost_frames > initial_lost
    
    def test_center_buffer_smoothing(self):
        """Test center buffer for smoothing."""
        framer = AutoFramer()
        
        # Add some centers to buffer
        framer._center_buffer.append((100, 100))
        framer._center_buffer.append((200, 200))
        
        assert len(framer._center_buffer) == 2
