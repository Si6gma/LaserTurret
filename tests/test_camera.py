"""
Tests for camera detection functionality.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from unittest.mock import Mock, patch, MagicMock
from facialRecog import find_available_cameras


class TestFindAvailableCameras:
    """Tests for find_available_cameras function."""
    
    @patch('facialRecog.cv2.VideoCapture')
    def test_no_cameras_available(self, mock_videocapture):
        """Test when no cameras are available."""
        # Mock closed capture
        mock_cap = MagicMock()
        mock_cap.isOpened.return_value = False
        mock_videocapture.return_value = mock_cap
        
        result = find_available_cameras(max_index=3)
        assert result == []
    
    @patch('facialRecog.cv2.VideoCapture')
    def test_single_camera_available(self, mock_videocapture):
        """Test when one camera is available."""
        def mock_capture(index):
            mock_cap = MagicMock()
            mock_cap.isOpened.return_value = (index == 0)
            return mock_cap
        
        mock_videocapture.side_effect = mock_capture
        
        result = find_available_cameras(max_index=3)
        assert result == [0]
    
    @patch('facialRecog.cv2.VideoCapture')
    def test_multiple_cameras_available(self, mock_videocapture):
        """Test when multiple cameras are available."""
        available_indices = [0, 2]
        
        def mock_capture(index):
            mock_cap = MagicMock()
            mock_cap.isOpened.return_value = (index in available_indices)
            return mock_cap
        
        mock_videocapture.side_effect = mock_capture
        
        result = find_available_cameras(max_index=4)
        assert result == [0, 2]
    
    @patch('facialRecog.cv2.VideoCapture')
    def test_camera_release_called(self, mock_videocapture):
        """Test that camera is released after checking."""
        mock_cap = MagicMock()
        mock_cap.isOpened.return_value = True
        mock_videocapture.return_value = mock_cap
        
        find_available_cameras(max_index=2)
        
        # Each camera should be released
        assert mock_cap.release.call_count == 2


class TestCameraConfiguration:
    """Tests for camera configuration constants."""
    
    def test_camera_index_is_integer(self):
        """Test that CAMERA_INDEX is an integer."""
        from facialRecog import CAMERA_INDEX
        assert isinstance(CAMERA_INDEX, int)
    
    def test_camera_index_non_negative(self):
        """Test that CAMERA_INDEX is non-negative."""
        from facialRecog import CAMERA_INDEX
        assert CAMERA_INDEX >= 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
