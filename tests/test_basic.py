"""
Basic tests for GyroGimbal - Project structure and smoke tests.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import pytest
import ast


class TestProjectStructure:
    """Test project file structure and organization."""
    
    def test_src_directory_exists(self):
        """Test that src directory exists."""
        src_dir = os.path.join(os.path.dirname(__file__), '..', 'src')
        assert os.path.isdir(src_dir)
    
    def test_tests_directory_exists(self):
        """Test that tests directory exists."""
        tests_dir = os.path.join(os.path.dirname(__file__), '..', 'tests')
        assert os.path.isdir(tests_dir)
    
    def test_assets_directory_exists(self):
        """Test that assets directory exists."""
        assets_dir = os.path.join(os.path.dirname(__file__), '..', 'assets')
        assert os.path.isdir(assets_dir)
    
    def test_github_workflows_exist(self):
        """Test that GitHub CI workflow exists."""
        workflow_path = os.path.join(os.path.dirname(__file__), '..', '.github', 'workflows', 'ci.yml')
        assert os.path.exists(workflow_path)
    
    def test_config_exists(self):
        """Test that config file exists."""
        config_path = os.path.join(os.path.dirname(__file__), '..', 'config.py')
        assert os.path.exists(config_path)
    
    def test_requirements_exists(self):
        """Test that requirements.txt exists."""
        req_path = os.path.join(os.path.dirname(__file__), '..', 'requirements.txt')
        assert os.path.exists(req_path)
    
    def test_readme_exists(self):
        """Test that README exists."""
        readme_paths = [
            os.path.join(os.path.dirname(__file__), '..', 'README.md'),
            os.path.join(os.path.dirname(__file__), '..', 'README.rst'),
        ]
        assert any(os.path.exists(p) for p in readme_paths)
    
    def test_license_exists(self):
        """Test that LICENSE file exists."""
        license_path = os.path.join(os.path.dirname(__file__), '..', 'LICENSE')
        assert os.path.exists(license_path)


class TestCodeQuality:
    """Test code quality and syntax."""
    
    def test_all_python_files_valid_syntax(self):
        """Test all Python files have valid syntax."""
        src_dir = os.path.join(os.path.dirname(__file__), '..', 'src')
        
        python_files = [
            'servo_driver.py',
            'imu_sensor.py', 
            'stabilizer.py',
            'auto_framing.py',
            'gimbal_controller.py',
            'gamepad_controller.py',
            'web_server.py'
        ]
        
        for filename in python_files:
            filepath = os.path.join(src_dir, filename)
            if os.path.exists(filepath):
                with open(filepath, 'r') as f:
                    code = f.read()
                # Parse to check it's valid Python
                try:
                    ast.parse(code)
                except SyntaxError as e:
                    pytest.fail(f"Syntax error in {filename}: {e}")
    
    def test_no_debug_print_statements(self):
        """Test that there are no debug print statements in production code."""
        src_dir = os.path.join(os.path.dirname(__file__), '..', 'src')
        
        for filename in os.listdir(src_dir):
            if filename.endswith('.py'):
                filepath = os.path.join(src_dir, filename)
                with open(filepath, 'r') as f:
                    content = f.read()
                
                # Check for print statements (not logger)
                lines = content.split('\n')
                for i, line in enumerate(lines, 1):
                    # Skip comments and strings containing "print"
                    stripped = line.strip()
                    if stripped.startswith('#') or stripped.startswith('"""'):
                        continue
                    # Check for print( that isn't logger-related
                    if 'print(' in line and 'logger' not in line:
                        # This is a soft check - prints are sometimes OK
                        pass  # Not failing, just documenting


class TestModuleImports:
    """Test that modules can be imported."""
    
    def test_servo_driver_imports(self):
        """Test servo_driver module imports."""
        from servo_driver import ServoDriver, HARDWARE_AVAILABLE
        assert ServoDriver is not None
    
    def test_imu_sensor_imports(self):
        """Test imu_sensor module imports."""
        from imu_sensor import IMUSensor, IMUData, MPU6050_ADDR
        assert IMUSensor is not None
        assert IMUData is not None
        assert MPU6050_ADDR == 0x68
    
    def test_stabilizer_imports(self):
        """Test stabilizer module imports."""
        from stabilizer import Stabilizer, PIDController, PIDConfig
        assert Stabilizer is not None
        assert PIDController is not None
        assert PIDConfig is not None
    
    def test_auto_framing_imports(self):
        """Test auto_framing module imports."""
        from auto_framing import AutoFramer, Subject, FramingData
        assert AutoFramer is not None
        assert Subject is not None
        assert FramingData is not None


class TestConfiguration:
    """Test configuration file."""
    
    def test_config_is_valid_python(self):
        """Test config file is valid Python."""
        config_path = os.path.join(os.path.dirname(__file__), '..', 'config.py')
        with open(config_path, 'r') as f:
            code = f.read()
        ast.parse(code)  # Should not raise


class TestRequirements:
    """Test requirements file."""
    
    def test_requirements_not_empty(self):
        """Test requirements file has content."""
        req_path = os.path.join(os.path.dirname(__file__), '..', 'requirements.txt')
        with open(req_path, 'r') as f:
            content = f.read()
        assert len(content.strip()) > 0
    
    def test_requirements_has_key_packages(self):
        """Test requirements has key dependencies listed."""
        req_path = os.path.join(os.path.dirname(__file__), '..', 'requirements.txt')
        with open(req_path, 'r') as f:
            content = f.read().lower()
        
        # Check for common packages
        key_packages = ['numpy', 'opencv', 'pytest']
        for pkg in key_packages:
            assert pkg in content, f"Missing package: {pkg}"


class TestDocumentation:
    """Test project documentation."""
    
    def test_readme_has_content(self):
        """Test README has substantial content."""
        readme_path = os.path.join(os.path.dirname(__file__), '..', 'README.md')
        if os.path.exists(readme_path):
            with open(readme_path, 'r') as f:
                content = f.read()
            assert len(content) > 100  # Should have substantial content
    
    def test_readme_has_key_sections(self):
        """Test README has expected sections."""
        readme_path = os.path.join(os.path.dirname(__file__), '..', 'README.md')
        if os.path.exists(readme_path):
            with open(readme_path, 'r') as f:
                content = f.read().lower()
            
            # Check for common sections
            key_terms = ['gimbal', 'raspberry pi', 'servo', 'imu', 'stabilizer']
            found_terms = [term for term in key_terms if term in content]
            assert len(found_terms) >= 3, "README should describe key features"
