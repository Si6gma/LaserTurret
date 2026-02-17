"""
Tests for the Servo Driver module - PWM control and position management.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import pytest
from servo_driver import ServoDriver


class TestServoDriver:
    """Test the servo driver in simulation mode."""
    
    def test_servo_initialization(self):
        """Test servo driver initializes with correct defaults."""
        driver = ServoDriver()
        
        assert driver.pitch_range == (0, 180)
        assert driver.yaw_range == (0, 180)
        assert driver.current_pitch == 90.0
        assert driver.current_yaw == 90.0
    
    def test_servo_custom_ranges(self):
        """Test servo driver accepts custom angle ranges."""
        driver = ServoDriver(
            pitch_range=(30, 150),
            yaw_range=(45, 135)
        )
        
        assert driver.pitch_range == (30, 150)
        assert driver.yaw_range == (45, 135)
    
    def test_set_position_basic(self):
        """Test setting servo position."""
        driver = ServoDriver()
        
        driver.set_position(45.0, 135.0)
        
        assert driver.current_pitch == 45.0
        assert driver.current_yaw == 135.0
    
    def test_set_position_clamping_pitch(self):
        """Test pitch is clamped to valid range."""
        driver = ServoDriver(pitch_range=(0, 180))
        
        # Try to set below minimum
        driver.set_position(-10.0, 90.0)
        assert driver.current_pitch == 0.0
        
        # Try to set above maximum
        driver.set_position(200.0, 90.0)
        assert driver.current_pitch == 180.0
    
    def test_set_position_clamping_yaw(self):
        """Test yaw is clamped to valid range."""
        driver = ServoDriver(yaw_range=(0, 180))
        
        # Try to set below minimum
        driver.set_position(90.0, -10.0)
        assert driver.current_yaw == 0.0
        
        # Try to set above maximum
        driver.set_position(90.0, 200.0)
        assert driver.current_yaw == 180.0
    
    def test_set_position_custom_range_clamping(self):
        """Test clamping with custom angle ranges."""
        driver = ServoDriver(
            pitch_range=(45, 135),
            yaw_range=(60, 120)
        )
        
        driver.set_position(0.0, 180.0)
        
        assert driver.current_pitch == 45.0  # Clamped to min
        assert driver.current_yaw == 120.0   # Clamped to max
    
    def test_get_position(self):
        """Test getting current position."""
        driver = ServoDriver()
        driver.set_position(60.0, 120.0)
        
        pitch, yaw = driver.get_position()
        
        assert pitch == 60.0
        assert yaw == 120.0
    
    def test_center(self):
        """Test centering servos."""
        driver = ServoDriver()
        driver.set_position(0.0, 180.0)
        
        driver.center()
        
        # Center should move to (90, 90)
        assert driver.current_pitch == 90.0
        assert driver.current_yaw == 90.0


class TestServoSmoothMotion:
    """Test smooth motion functionality."""
    
    def test_smooth_motion_reaches_target(self):
        """Test smooth motion eventually reaches target."""
        driver = ServoDriver()
        driver.set_position(0.0, 0.0)
        
        # Quick duration for testing
        driver.set_position_smooth(90.0, 90.0, duration=0.05)
        
        # Should end at target
        assert driver.current_pitch == 90.0
        assert driver.current_yaw == 90.0
    
    def test_smooth_motion_interpolates(self):
        """Test smooth motion interpolates between positions."""
        driver = ServoDriver()
        driver.set_position(0.0, 0.0)
        
        # This test verifies the method runs without error
        # In real hardware, we'd check intermediate positions
        driver.set_position_smooth(50.0, 50.0, duration=0.05)  # Need enough time for steps
        
        # Should end at target
        assert driver.current_pitch == 50.0
        assert driver.current_yaw == 50.0


class TestServoEdgeCases:
    """Test edge cases and error conditions."""
    
    def test_float_positions(self):
        """Test servo accepts floating point positions."""
        driver = ServoDriver()
        
        driver.set_position(45.5, 90.3)
        
        assert driver.current_pitch == 45.5
        assert driver.current_yaw == 90.3
    
    def test_boundary_values(self):
        """Test exact boundary values."""
        driver = ServoDriver()
        
        # Test exact min and max
        driver.set_position(0.0, 0.0)
        assert driver.current_pitch == 0.0
        assert driver.current_yaw == 0.0
        
        driver.set_position(180.0, 180.0)
        assert driver.current_pitch == 180.0
        assert driver.current_yaw == 180.0
    
    def test_very_small_movement(self):
        """Test very small position changes."""
        driver = ServoDriver()
        driver.set_position(90.0, 90.0)
        
        driver.set_position(90.01, 90.01)
        
        assert driver.current_pitch == 90.01
        assert driver.current_yaw == 90.01
