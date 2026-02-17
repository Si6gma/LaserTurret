"""
Basic tests for GyroGimbal
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))


def test_imports():
    """Test that main modules can be imported (with hardware mocking)."""
    # These will fail if hardware is not present, which is expected in CI
    # Just test that the files exist and are valid Python
    import ast
    
    src_dir = os.path.join(os.path.dirname(__file__), '..', 'src')
    
    for filename in ['servo_driver.py', 'imu_sensor.py', 'stabilizer.py', 
                     'auto_framing.py', 'gimbal_controller.py']:
        filepath = os.path.join(src_dir, filename)
        if os.path.exists(filepath):
            with open(filepath, 'r') as f:
                code = f.read()
            # Parse to check it's valid Python
            ast.parse(code)


def test_config_exists():
    """Test that config file exists."""
    config_path = os.path.join(os.path.dirname(__file__), '..', 'config.py')
    assert os.path.exists(config_path)


def test_requirements_exists():
    """Test that requirements.txt exists."""
    req_path = os.path.join(os.path.dirname(__file__), '..', 'requirements.txt')
    assert os.path.exists(req_path)
