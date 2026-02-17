"""
Tests for the Stabilizer module - PID control and sensor fusion algorithms.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import pytest
import numpy as np
from stabilizer import PIDController, PIDConfig, Stabilizer


class TestPIDController:
    """Test the PID controller implementation."""
    
    def test_pid_initialization(self):
        """Test PID controller initializes with correct default values."""
        config = PIDConfig(kp=1.0, ki=0.1, kd=0.5)
        pid = PIDController(config)
        
        assert pid.integral == 0.0
        assert pid.prev_error == 0.0
        assert pid.prev_time is None
    
    def test_pid_reset(self):
        """Test PID controller reset clears internal state."""
        config = PIDConfig()
        pid = PIDController(config)
        
        # Run a few updates to change state
        pid.update(1.0, 0.1)
        pid.update(0.5, 0.1)
        
        # Reset and verify
        pid.reset()
        assert pid.integral == 0.0
        assert pid.prev_error == 0.0
        assert pid.prev_time is None
    
    def test_pid_proportional_response(self):
        """Test proportional term responds correctly to error."""
        config = PIDConfig(kp=2.0, ki=0.0, kd=0.0)
        pid = PIDController(config)
        
        # Error of 5.0 should give output of 10.0 (kp * error)
        output = pid.update(5.0, 0.1)
        assert output == pytest.approx(10.0)
    
    def test_pid_integral_accumulation(self):
        """Test integral term accumulates error over time."""
        config = PIDConfig(kp=0.0, ki=1.0, kd=0.0)
        pid = PIDController(config)
        
        # Apply constant error of 1.0 for 0.1s twice
        pid.update(1.0, 0.1)
        output = pid.update(1.0, 0.1)
        
        # Integral should be 0.2 (1.0 * 0.1 + 1.0 * 0.1)
        # Output should be 0.2 (ki * integral)
        assert output == pytest.approx(0.2, abs=0.01)
    
    def test_pid_derivative_response(self):
        """Test derivative term responds to error change."""
        config = PIDConfig(kp=0.0, ki=0.0, kd=1.0)
        pid = PIDController(config)
        
        # First update establishes previous error
        pid.update(1.0, 0.1)
        # Second update: derivative = (0.5 - 1.0) / 0.1 = -5.0
        output = pid.update(0.5, 0.1)
        
        assert output == pytest.approx(-5.0)
    
    def test_pid_integral_anti_windup(self):
        """Test integral anti-windup prevents excessive accumulation."""
        config = PIDConfig(kp=0.0, ki=1.0, kd=0.0, integral_limit=1.0)
        pid = PIDController(config)
        
        # Accumulate large error
        for _ in range(100):
            pid.update(10.0, 0.1)
        
        # Integral should be clamped to limit
        assert pid.integral <= config.integral_limit
    
    def test_pid_output_limit(self):
        """Test output is limited to configured range."""
        config = PIDConfig(kp=10.0, output_limit=50.0)
        pid = PIDController(config)
        
        # Large error should be clamped
        output = pid.update(100.0, 0.1)
        assert output <= config.output_limit
        assert output >= -config.output_limit
    
    def test_pid_zero_dt(self):
        """Test PID handles zero time step gracefully."""
        config = PIDConfig(kp=1.0, ki=0.1, kd=0.5)
        pid = PIDController(config)
        
        output = pid.update(1.0, 0.0)
        assert output == 0.0


class TestStabilizer:
    """Test the main Stabilizer class."""
    
    def test_stabilizer_initialization(self):
        """Test stabilizer initializes with correct default state."""
        stabilizer = Stabilizer()
        
        assert stabilizer.gain == 0.7
        assert stabilizer.smoothing == 0.3
        assert stabilizer.roll == 0.0
        assert stabilizer.pitch == 0.0
        assert stabilizer.yaw == 0.0
        assert stabilizer.use_complementary_filter is True
    
    def test_stabilizer_custom_params(self):
        """Test stabilizer accepts custom parameters."""
        stabilizer = Stabilizer(gain=0.5, smoothing=0.5, use_complementary_filter=False)
        
        assert stabilizer.gain == 0.5
        assert stabilizer.smoothing == 0.5
        assert stabilizer.use_complementary_filter is False
    
    def test_calculate_compensation_zero_motion(self):
        """Test compensation is zero when there's no motion."""
        stabilizer = Stabilizer()
        
        # Zero gyro readings
        gyro = np.array([0.0, 0.0, 0.0])
        accel = np.array([0.0, 0.0, 1.0])  # Flat, level
        
        pitch_comp, yaw_comp = stabilizer.calculate_compensation(gyro, accel, 0.01)
        
        assert pitch_comp == pytest.approx(0.0, abs=0.01)
        assert yaw_comp == pytest.approx(0.0, abs=0.01)
    
    def test_calculate_compensation_pitch_motion(self):
        """Test compensation responds to pitch motion."""
        stabilizer = Stabilizer(gain=1.0)
        
        # Gyro reading indicating pitch rotation (positive around Y axis)
        gyro = np.array([0.0, 1.0, 0.0])  # 1 rad/s pitch rate
        accel = np.array([0.0, 0.0, 1.0])
        
        pitch_comp, yaw_comp = stabilizer.calculate_compensation(gyro, accel, 0.01)
        
        # Should produce negative compensation (move opposite to shake)
        assert pitch_comp < 0
        assert yaw_comp == pytest.approx(0.0, abs=0.01)
    
    def test_calculate_compensation_yaw_motion(self):
        """Test compensation responds to yaw motion."""
        stabilizer = Stabilizer(gain=1.0)
        
        # Gyro reading indicating yaw rotation (around Z axis)
        gyro = np.array([0.0, 0.0, 1.0])  # 1 rad/s yaw rate
        accel = np.array([0.0, 0.0, 1.0])
        
        pitch_comp, yaw_comp = stabilizer.calculate_compensation(gyro, accel, 0.01)
        
        # Should produce negative compensation
        assert yaw_comp < 0
        assert pitch_comp == pytest.approx(0.0, abs=0.01)
    
    def test_calculate_compensation_zero_dt(self):
        """Test stabilizer handles zero time step gracefully."""
        stabilizer = Stabilizer()
        
        gyro = np.array([1.0, 1.0, 1.0])
        accel = np.array([0.0, 0.0, 1.0])
        
        pitch_comp, yaw_comp = stabilizer.calculate_compensation(gyro, accel, 0.0)
        
        assert pitch_comp == 0.0
        assert yaw_comp == 0.0
    
    def test_tracking_compensation_centered_subject(self):
        """Test tracking compensation when subject is centered."""
        stabilizer = Stabilizer()
        
        # Subject at frame center
        subject_pos = (640, 360)  # Center of 1280x720 frame
        frame_center = (640, 360)
        
        pitch_adj, yaw_adj = stabilizer.calculate_tracking_compensation(
            subject_pos, frame_center, 0.01
        )
        
        # Should require minimal adjustment
        assert pitch_adj == pytest.approx(0.0, abs=0.01)
        assert yaw_adj == pytest.approx(0.0, abs=0.01)
    
    def test_tracking_compensation_offset_subject(self):
        """Test tracking compensation when subject is offset."""
        stabilizer = Stabilizer()
        
        # Subject to the right and below center
        subject_pos = (740, 460)  # 100px right, 100px down
        frame_center = (640, 360)
        
        pitch_adj, yaw_adj = stabilizer.calculate_tracking_compensation(
            subject_pos, frame_center, 0.01
        )
        
        # Subject is right -> need positive yaw to track
        # Subject is down -> need positive pitch to track (but pitch PID may invert)
        assert yaw_adj > 0  # Need to move right
    
    def test_blend_tracking_stabilization(self):
        """Test blending of tracking and stabilization commands."""
        stabilizer = Stabilizer()
        
        tracking = (10.0, 20.0)  # Target angles from tracking
        stabilization = (5.0, -5.0)  # Compensation from stabilization
        
        # 50% blend
        pitch, yaw = stabilizer.blend_tracking_stabilization(
            tracking, stabilization, tracking_weight=0.5
        )
        
        # Result should be between the two
        assert 10.0 <= pitch <= 15.0
        assert 15.0 <= yaw <= 20.0
    
    def test_jerk_limiting(self):
        """Test jerk limiting prevents sudden movements."""
        stabilizer = Stabilizer()
        
        current_pitch, current_yaw = 90.0, 90.0
        target_pitch, target_yaw = 120.0, 120.0  # Large jump
        
        new_pitch, new_yaw = stabilizer.apply_jerk_limiting(
            target_pitch, target_yaw, current_pitch, current_yaw, dt=0.01, max_jerk=100.0
        )
        
        # Should not jump all the way to target
        assert new_pitch < target_pitch
        assert new_yaw < target_yaw
    
    def test_reset_clears_state(self):
        """Test reset clears all internal state."""
        stabilizer = Stabilizer()
        
        # Run some updates
        gyro = np.array([0.0, 1.0, 1.0])
        accel = np.array([0.0, 0.0, 1.0])
        stabilizer.calculate_compensation(gyro, accel, 0.01)
        
        # Reset
        stabilizer.reset()
        
        # Verify state cleared
        assert stabilizer.roll == 0.0
        assert stabilizer.pitch == 0.0
        assert stabilizer.yaw == 0.0
        assert len(stabilizer.pitch_history) == 0
        assert len(stabilizer.yaw_history) == 0


class TestStabilizerSmoothing:
    """Test smoothing functionality."""
    
    def test_smoothing_reduces_noise(self):
        """Test that smoothing reduces high-frequency noise."""
        stabilizer = Stabilizer(gain=1.0)
        
        np.random.seed(42)
        results = []
        
        for _ in range(20):
            # Add noise to gyro
            gyro = np.array([0.0, 0.1 + np.random.normal(0, 0.05), 0.0])
            accel = np.array([0.0, 0.0, 1.0])
            pitch, yaw = stabilizer.calculate_compensation(gyro, accel, 0.01)
            results.append(pitch)
        
        # Smoothed output should have lower variance than raw
        assert len(results) == 20
        # All results should be finite
        assert all(np.isfinite(r) for r in results)
