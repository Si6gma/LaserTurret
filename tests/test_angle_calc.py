"""
Tests for angle calculation and smoothing functions.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
import math
from facialRecog import calculate_angle, smooth_angle, YAW_MIN, YAW_MAX


class TestCalculateAngle:
    """Tests for calculate_angle function."""
    
    def test_center_position(self):
        """Test that center position returns 90 degrees."""
        # When horizontal is 0, should return center (90)
        assert calculate_angle(0, 100) == 90
    
    def test_horizontal_positive(self):
        """Test angle calculation with positive horizontal."""
        # atan(1) * 180/pi = 45 degrees, + 90 = 135
        result = calculate_angle(100, 100)
        assert result == 135
    
    def test_horizontal_negative(self):
        """Test angle calculation with negative vertical."""
        # atan(-1) * 180/pi = -45 degrees, + 90 = 45
        result = calculate_angle(100, -100)
        assert result == 45
    
    def test_angle_clamping_min(self):
        """Test that angle is clamped to minimum."""
        # Very negative angle should be clamped to YAW_MIN
        result = calculate_angle(1, -1000)
        assert result == YAW_MIN
    
    def test_angle_clamping_max(self):
        """Test that angle is clamped to maximum."""
        # Very positive angle should be clamped to YAW_MAX
        result = calculate_angle(1, 1000)
        assert result == YAW_MAX


class TestSmoothAngle:
    """Tests for smooth_angle function."""
    
    def test_no_change_when_equal(self):
        """Test that no smoothing occurs when current equals target."""
        result = smooth_angle(90, 90)
        assert result == 90
    
    def test_smooth_towards_target(self):
        """Test that angle moves towards target."""
        # With default factor of 0.3, from 90 to 120
        # 90 + (120 - 90) * 0.3 = 90 + 9 = 99
        result = smooth_angle(90, 120, factor=0.3)
        assert result == 99
    
    def test_smooth_decreasing(self):
        """Test smoothing when decreasing angle."""
        # From 120 to 90 with factor 0.3
        # 120 + (90 - 120) * 0.3 = 120 - 9 = 111
        result = smooth_angle(120, 90, factor=0.3)
        assert result == 111
    
    def test_full_smoothing_factor(self):
        """Test with smoothing factor of 1.0 (no smoothing)."""
        result = smooth_angle(90, 120, factor=1.0)
        assert result == 120
    
    def test_zero_smoothing_factor(self):
        """Test with smoothing factor of 0.0 (no movement)."""
        result = smooth_angle(90, 120, factor=0.0)
        assert result == 90


class TestAngleIntegration:
    """Integration tests for angle calculation and smoothing."""
    
    def test_calculate_and_smooth(self):
        """Test calculating angle then smoothing it."""
        target = calculate_angle(100, 100)  # Should be 135
        smoothed = smooth_angle(90, target, factor=0.5)
        # 90 + (135 - 90) * 0.5 = 90 + 22.5 = 112.5 -> 112
        assert smoothed == 112
    
    def test_multiple_smoothing_steps(self):
        """Test multiple smoothing steps converge to target."""
        current = 90
        target = calculate_angle(100, 100)  # 135
        
        # Apply smoothing multiple times
        for _ in range(10):
            current = smooth_angle(current, target, factor=0.3)
        
        # Should be closer to target after multiple steps
        assert current > 90
        assert current <= target


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
