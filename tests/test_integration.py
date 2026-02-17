"""
Integration tests for GyroGimbal - testing component interactions.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import pytest
import numpy as np
from stabilizer import Stabilizer
from servo_driver import ServoDriver
from imu_sensor import IMUSensor, IMUData
from auto_framing import AutoFramer


class TestStabilizationLoop:
    """Test the stabilization control loop."""
    
    def test_imu_to_stabilizer_flow(self):
        """Test data flow from IMU to stabilizer."""
        imu = IMUSensor()
        stabilizer = Stabilizer(gain=1.0)
        
        # Simulate motion in IMU
        imu.simulate_motion(pitch_rate=0.5, yaw_rate=0.3)
        data = imu.get_reading()
        
        # Use data in stabilizer
        pitch_comp, yaw_comp = stabilizer.calculate_compensation(
            data.gyro, data.accel, dt=0.01
        )
        
        # Should produce non-zero compensation
        assert pitch_comp != 0.0 or yaw_comp != 0.0
        assert np.isfinite(pitch_comp)
        assert np.isfinite(yaw_comp)
    
    def test_stabilizer_to_servo_flow(self):
        """Test control flow from stabilizer to servo driver."""
        stabilizer = Stabilizer(gain=1.0)
        servo = ServoDriver()
        
        # Get compensation for some motion
        gyro = np.array([0.0, 1.0, 0.5])
        accel = np.array([0.0, 0.0, 1.0])
        pitch_comp, yaw_comp = stabilizer.calculate_compensation(gyro, accel, 0.01)
        
        # Apply to current position
        current_pitch, current_yaw = servo.get_position()
        new_pitch = current_pitch + pitch_comp * 0.01
        new_yaw = current_yaw + yaw_comp * 0.01
        
        servo.set_position(new_pitch, new_yaw)
        
        # Verify position was set
        assert servo.current_pitch == pytest.approx(new_pitch)
        assert servo.current_yaw == pytest.approx(new_yaw)


class TestTrackingLoop:
    """Test the subject tracking loop."""
    
    def test_framer_to_stabilizer_flow(self):
        """Test data flow from framer to stabilizer."""
        framer = AutoFramer()
        stabilizer = Stabilizer()
        
        # Simulate subject detection
        subject_bbox = (700, 400, 100, 100)  # Subject to right and below
        frame_size = (1280, 720)
        
        # Get framing angles
        target_pitch, target_yaw = framer.calculate_framing(subject_bbox, frame_size)
        
        # Use tracking compensation
        subject_pos = (750, 450)
        frame_center = (640, 360)
        pitch_adj, yaw_adj = stabilizer.calculate_tracking_compensation(
            subject_pos, frame_center, dt=0.01
        )
        
        # Both should produce valid angles
        assert 0 <= target_pitch <= 180
        assert 0 <= target_yaw <= 180
        assert np.isfinite(pitch_adj)
        assert np.isfinite(yaw_adj)
    
    def test_full_tracking_pipeline(self):
        """Test full tracking pipeline with simulated data."""
        framer = AutoFramer()
        stabilizer = Stabilizer()
        servo = ServoDriver()
        
        # Start centered
        servo.center()
        
        # Simulate subject to the right
        subject_bbox = (800, 360, 100, 100)
        frame_size = (1280, 720)
        
        # Calculate framing
        target_pitch, target_yaw = framer.calculate_framing(subject_bbox, frame_size)
        
        # Get tracking adjustment
        pitch_adj, yaw_adj = stabilizer.calculate_tracking_compensation(
            (850, 410), (640, 360), dt=0.01
        )
        
        # Blend with current position
        current_pitch, current_yaw = servo.get_position()
        blended_pitch, blended_yaw = stabilizer.blend_tracking_stabilization(
            (target_pitch, target_yaw),
            (pitch_adj, yaw_adj),
            tracking_weight=0.7
        )
        
        # Apply to servo
        servo.set_position(blended_pitch, blended_yaw)
        
        # Verify final position is reasonable
        final_pitch, final_yaw = servo.get_position()
        assert 0 <= final_pitch <= 180
        assert 0 <= final_yaw <= 180
        # Subject was to the right, so yaw should increase
        assert final_yaw >= 90


class TestStabilizationAndTracking:
    """Test combining stabilization with subject tracking."""
    
    def test_blend_modes(self):
        """Test different blend modes between tracking and stabilization."""
        stabilizer = Stabilizer()
        
        tracking = (100.0, 110.0)
        stabilization = (5.0, -5.0)
        
        # Full tracking
        p, y = stabilizer.blend_tracking_stabilization(tracking, stabilization, tracking_weight=1.0)
        assert p == tracking[0]  # Just tracking, no stab compensation
        
        # Full stabilization
        p, y = stabilizer.blend_tracking_stabilization(tracking, stabilization, tracking_weight=0.0)
        assert p == tracking[0] + stabilization[0]  # Just stabilization
        
        # 50/50 blend
        p, y = stabilizer.blend_tracking_stabilization(tracking, stabilization, tracking_weight=0.5)
        assert tracking[0] <= p <= tracking[0] + stabilization[0]


class TestSystemState:
    """Test overall system state management."""
    
    def test_multiple_components_running(self):
        """Test that multiple components can run together."""
        imu = IMUSensor()
        stabilizer = Stabilizer()
        servo = ServoDriver()
        framer = AutoFramer()
        
        # Start IMU
        imu.start()
        
        # Simulate a control loop iteration
        imu.simulate_motion(pitch_rate=0.1, yaw_rate=0.05)
        data = imu.get_reading()
        
        # Calculate stabilization
        pitch_comp, yaw_comp = stabilizer.calculate_compensation(
            data.gyro, data.accel, dt=0.01
        )
        
        # Apply to servo
        servo.set_position(90 + pitch_comp, 90 + yaw_comp)
        
        # Check tracking
        target_p, target_y = framer.calculate_framing((640, 360, 100, 100), (1280, 720))
        
        # Stop IMU
        imu.stop()
        
        # Verify everything is in valid state
        assert not imu._running
        assert 0 <= servo.current_pitch <= 180
        assert 0 <= servo.current_yaw <= 180
    
    def test_reset_all_components(self):
        """Test resetting all components to initial state."""
        imu = IMUSensor()
        stabilizer = Stabilizer()
        servo = ServoDriver()
        
        # Run some operations
        imu.start()
        imu.simulate_motion(1.0, 1.0)
        stabilizer.calculate_compensation(np.array([0.0, 1.0, 1.0]), np.array([0.0, 0.0, 1.0]), 0.01)
        servo.set_position(120.0, 130.0)
        imu.stop()
        
        # Reset
        stabilizer.reset()
        servo.center()
        
        # Verify reset state
        assert stabilizer.pitch == 0.0
        assert stabilizer.yaw == 0.0
        assert servo.current_pitch == 90.0
        assert servo.current_yaw == 90.0


class TestEdgeCases:
    """Test edge cases and boundary conditions."""
    
    def test_very_small_dt(self):
        """Test system handles very small time steps."""
        imu = IMUSensor()
        stabilizer = Stabilizer()
        
        imu.simulate_motion(1.0, 1.0)
        data = imu.get_reading()
        
        # Very small dt
        pitch, yaw = stabilizer.calculate_compensation(data.gyro, data.accel, dt=0.0001)
        
        assert np.isfinite(pitch)
        assert np.isfinite(yaw)
    
    def test_zero_motion(self):
        """Test system with zero motion input."""
        imu = IMUSensor()
        stabilizer = Stabilizer()
        servo = ServoDriver()
        
        # Zero motion
        imu._latest_data = IMUData(
            accel=np.array([0.0, 0.0, 1.0]),
            gyro=np.array([0.0, 0.0, 0.0]),
            valid=True
        )
        
        data = imu.get_reading()
        pitch, yaw = stabilizer.calculate_compensation(data.gyro, data.accel, 0.01)
        
        servo.center()
        
        # With zero motion, compensation should be near zero
        assert abs(pitch) < 1.0
        assert abs(yaw) < 1.0
        assert servo.current_pitch == 90.0
        assert servo.current_yaw == 90.0
    
    def test_extreme_angles(self):
        """Test system with extreme servo angles."""
        servo = ServoDriver()
        
        # Try to set extreme angles (should be clamped)
        servo.set_position(-1000.0, 1000.0)
        
        assert servo.current_pitch == 0.0  # Clamped to min
        assert servo.current_yaw == 180.0   # Clamped to max


class TestPerformance:
    """Test performance characteristics."""
    
    def test_stabilizer_performance(self):
        """Test stabilizer can run at high frequency."""
        import time
        
        stabilizer = Stabilizer()
        gyro = np.array([0.0, 0.5, 0.3])
        accel = np.array([0.0, 0.0, 1.0])
        
        start = time.time()
        iterations = 1000
        
        for _ in range(iterations):
            stabilizer.calculate_compensation(gyro, accel, 0.01)
        
        elapsed = time.time() - start
        
        # Should complete 1000 iterations quickly (< 1 second)
        assert elapsed < 1.0
        # Average iteration should be < 1ms
        assert elapsed / iterations < 0.001
