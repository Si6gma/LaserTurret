"""
Local Configuration for Laser Turret

Copy this file to config_local.py and update values for your system.
Do not commit config_local.py to version control (it's in .gitignore).
"""

# =============================================================================
# SERIAL CONFIGURATION
# =============================================================================

# Serial port - find yours with:
#   macOS: ls /dev/tty.* /dev/cu.*
#   Linux: ls /dev/ttyACM* /dev/ttyUSB*
#   Windows: Check Device Manager → Ports (COM & LPT)
#   Arduino IDE: Tools → Port
SERIAL_PORT = "/dev/cu.usbmodemDC5475C3BB642"  # Example for macOS
# SERIAL_PORT = "/dev/ttyACM0"  # Example for Linux
# SERIAL_PORT = "COM3"  # Example for Windows

# Serial baud rate (must match Arduino sketch)
SERIAL_BAUD = 9600

# =============================================================================
# CAMERA CONFIGURATION
# =============================================================================

# Camera index - try different values if camera not found
#   0 = Default / built-in camera
#   1 = External USB webcam
#   2, 3, etc. = Additional cameras
CAMERA_INDEX = 0

# =============================================================================
# TRACKING CONFIGURATION
# =============================================================================

# Default pitch angle (vertical tilt)
# Range: 0-180 degrees
DEFAULT_PITCH = 40

# Smoothing factor for servo movement (0.0 - 1.0)
# Higher = more responsive but jerky
# Lower = smoother but more lag
SMOOTHING_FACTOR = 0.3

# Minimum face size for detection (pixels)
# Increase to ignore small/false detections
MIN_FACE_SIZE = 100

# =============================================================================
# DISPLAY CONFIGURATION
# =============================================================================

# Window name
WINDOW_NAME = "Laser Turret - Face Tracking"

# Show debug info on frame
SHOW_DEBUG_INFO = True

# Frame delay (ms) - lower = smoother but more CPU
FRAME_DELAY_MS = 1

# =============================================================================
# SAFETY CONFIGURATION
# =============================================================================

# Safety check - ensure this is False before using real hardware
# When True, prevents motor movement for testing
SAFETY_TEST_MODE = False

# Maximum servo speed (degrees per update)
# Lower for safer operation
MAX_SERVO_SPEED = 5
