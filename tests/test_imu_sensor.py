"""
Tests for the IMU Sensor module - data reading and filtering.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import pytest
import numpy as np
from imu_sensor import IMUSensor, IMUData, MPU6050_ADDR


class TestIMUData:
    """Test IMU data container."""
    
    def test_imu_data_defaults(self):
        """Test IMU data initializes with correct defaults."""
        data = IMUData()
        
        assert np.allclose(data.accel, np.zeros(3))
        assert np.allclose(data.gyro, np.zeros(3))
        assert data.mag is None
        assert data.temperature == 0.0
        assert data.timestamp == 0.0
        assert data.valid is False
    
    def test_imu_data_custom_values(self):
        """Test IMU data accepts custom values."""
        data = IMUData(
            accel=np.array([0.0, 0.0, 1.0]),
            gyro=np.array([0.1, 0.2, 0.3]),
            temperature=25.0,
            timestamp=1234.5,
            valid=True
        )
        
        assert np.allclose(data.accel, [0.0, 0.0, 1.0])
        assert np.allclose(data.gyro, [0.1, 0.2, 0.3])
        assert data.temperature == 25.0
        assert data.timestamp == 1234.5
        assert data.valid is True


class TestIMUSensor:
    """Test IMU sensor in simulation mode."""
    
    def test_imu_initialization(self):
        """Test IMU sensor initializes correctly."""
        imu = IMUSensor()
        
        assert imu.i2c_address == MPU6050_ADDR
        assert imu.sample_rate == 100
        assert imu.sample_period == 0.01
        assert imu._running is False
    
    def test_imu_custom_params(self):
        """Test IMU accepts custom parameters."""
        imu = IMUSensor(
            i2c_address=0x69,
            sample_rate=200
        )
        
        assert imu.i2c_address == 0x69
        assert imu.sample_rate == 200
        assert imu.sample_period == 0.005
    
    def test_get_reading_returns_data(self):
        """Test get_reading returns IMUData."""
        imu = IMUSensor()
        
        data = imu.get_reading()
        
        assert isinstance(data, IMUData)
    
    def test_get_angles_invalid_data(self):
        """Test get_angles handles invalid data."""
        imu = IMUSensor()
        
        # Default reading is invalid
        roll, pitch, yaw = imu.get_angles()
        
        assert roll == 0.0
        assert pitch == 0.0
        assert yaw == 0.0
    
    def test_get_angles_valid_data(self):
        """Test angle calculation from valid accelerometer data."""
        imu = IMUSensor()
        
        # Simulate level orientation
        imu._latest_data = IMUData(
            accel=np.array([0.0, 0.0, 1.0]),  # 1g straight down
            gyro=np.zeros(3),
            valid=True
        )
        
        roll, pitch, yaw = imu.get_angles()
        
        # Level should give near-zero roll and pitch
        assert roll == pytest.approx(0.0, abs=0.01)
        assert pitch == pytest.approx(0.0, abs=0.01)
    
    def test_get_angles_tilted(self):
        """Test angle calculation from tilted orientation."""
        imu = IMUSensor()
        
        # Simulate 45 degree pitch (accelerometer reading)
        # When pitched, x axis sees some gravity
        imu._latest_data = IMUData(
            accel=np.array([0.707, 0.0, 0.707]),  # 45 degrees
            gyro=np.zeros(3),
            valid=True
        )
        
        roll, pitch, yaw = imu.get_angles()
        
        # Should detect the pitch
        assert pitch == pytest.approx(-45.0, abs=1.0)
    
    def test_start_stop(self):
        """Test starting and stopping the IMU."""
        imu = IMUSensor()
        
        imu.start()
        assert imu._running is True
        assert imu._thread is not None
        
        imu.stop()
        assert imu._running is False


class TestIMUMotionSimulation:
    """Test motion simulation features."""
    
    def test_simulate_motion(self):
        """Test motion simulation sets correct data."""
        imu = IMUSensor()
        
        imu.simulate_motion(pitch_rate=1.0, yaw_rate=0.5)
        
        data = imu.get_reading()
        assert data.valid is True
        assert np.allclose(data.accel, [0.0, 0.0, 1.0])
        assert data.gyro[1] == 1.0  # pitch rate
        assert data.gyro[2] == 0.5  # yaw rate
    
    def test_simulate_motion_no_hardware(self):
        """Test simulation only works in simulation mode."""
        # This test assumes we're in simulation mode (no hardware)
        # The simulate_motion should work without hardware
        imu = IMUSensor()
        
        # Should not raise exception
        imu.simulate_motion(pitch_rate=0.0, yaw_rate=0.0)
        
        data = imu.get_reading()
        assert data.valid is True


class TestIMUFiltering:
    """Test IMU filtering functionality."""
    
    def test_filter_alpha_values(self):
        """Test filter coefficients are in valid range."""
        imu = IMUSensor()
        
        # Filter alpha should be between 0 and 1
        assert 0.0 <= imu._accel_filter_alpha <= 1.0
        assert 0.0 <= imu._gyro_filter_alpha <= 1.0
    
    def test_calibration_offsets_initial(self):
        """Test calibration offsets initialize to zero."""
        imu = IMUSensor()
        
        assert np.allclose(imu._gyro_offset, np.zeros(3))
        assert np.allclose(imu._accel_offset, np.zeros(3))


class TestIMUThreadSafety:
    """Test thread safety features."""
    
    def test_lock_exists(self):
        """Test IMU has a lock for thread safety."""
        imu = IMUSensor()
        
        assert imu._lock is not None
    
    def test_concurrent_reading(self):
        """Test concurrent reading doesn't crash."""
        import threading
        import time
        
        imu = IMUSensor()
        imu.start()
        time.sleep(0.01)  # Let it start
        
        results = []
        
        def reader():
            for _ in range(10):
                data = imu.get_reading()
                results.append(data)
                time.sleep(0.001)
        
        threads = [threading.Thread(target=reader) for _ in range(3)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        imu.stop()
        
        # All reads should have succeeded
        assert len(results) == 30
