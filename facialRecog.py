"""
Laser Turret - Face Tracking Application

Uses OpenCV for face detection and controls Arduino servos
to track detected faces.

Author: Si6gma
License: MIT
"""

import cv2
import logging
import math
import serial
import time
import os
from typing import Tuple, Optional

# =============================================================================
# LOGGING CONFIGURATION
# =============================================================================

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# =============================================================================
# CONFIGURATION
# =============================================================================

# Import local configuration if available
try:
    from config_local import (
        SERIAL_PORT, 
        SERIAL_BAUD, 
        CAMERA_INDEX, 
        DEFAULT_PITCH,
        SMOOTHING_FACTOR
    )
except ImportError:
    # Default configuration - update these for your system
    SERIAL_PORT = "/dev/cu.usbmodemDC5475C3BB642"  # Change to your Arduino port
    SERIAL_BAUD = 9600
    CAMERA_INDEX = 1  # 0 for default camera, 1 for external webcam
    DEFAULT_PITCH = 40
    SMOOTHING_FACTOR = 0.3  # Higher = smoother but more lag

# =============================================================================
# CONSTANTS
# =============================================================================

# Haar cascade file for face detection
FACE_CASCADE_PATH = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"

# Servo limits (degrees)
YAW_MIN = 0
YAW_MAX = 180
PITCH_MIN = 0
PITCH_MAX = 180

# Frame processing
FRAME_DELAY_MS = 1  # Delay between frames (ms)
QUIT_KEY = ord('q')

# =============================================================================
# FUNCTIONS
# =============================================================================

def calculate_angle(horizontal: float, vertical: float) -> int:
    """
    Calculate angle from horizontal and vertical distances.
    
    Args:
        horizontal: Horizontal distance from center
        vertical: Vertical distance from center
        
    Returns:
        Angle in degrees (0-180)
    """
    if horizontal == 0:
        return 90  # Center position
    angle = math.atan(vertical / horizontal) * (180 / math.pi)
    return int(max(YAW_MIN, min(YAW_MAX, angle + 90)))


def smooth_angle(current: int, target: int, factor: float = SMOOTHING_FACTOR) -> int:
    """
    Smooth angle transitions to reduce servo jitter.
    
    Args:
        current: Current angle
        target: Target angle
        factor: Smoothing factor (0-1)
        
    Returns:
        Smoothed angle
    """
    return int(current + (target - current) * factor)


def find_available_cameras(max_index: int = 5) -> list[int]:
    """
    Scan for available camera indices.
    
    Returns:
        List of available camera indices
    """
    available = []
    for i in range(max_index):
        cap = cv2.VideoCapture(i)
        if cap.isOpened():
            available.append(i)
            cap.release()
    return available


# =============================================================================
# MAIN APPLICATION
# =============================================================================

def main():
    """Main application entry point."""
    
    logger.info("=" * 60)
    logger.info("Laser Turret - Face Tracking System")
    logger.info("=" * 60)
    
    # Safety reminder
    logger.warning("⚠️  SAFETY REMINDER:")
    logger.warning("   Ensure laser is removed or replaced with LED before use!")
    logger.warning("   Never aim at people's eyes.")
    
    # Load face detection model
    logger.info("Loading face detection model...")
    face_cascade = cv2.CascadeClassifier(FACE_CASCADE_PATH)
    if face_cascade.empty():
        logger.error("❌ Error: Could not load face cascade classifier")
        return
    logger.info("✓ Face detection model loaded")
    
    # Connect to Arduino
    logger.info(f"Connecting to Arduino on {SERIAL_PORT}...")
    try:
        ser = serial.Serial(SERIAL_PORT, SERIAL_BAUD, timeout=1)
        time.sleep(2)  # Wait for Arduino reset
        logger.info("✓ Connected to Arduino")
    except serial.SerialException as e:
        logger.error(f"❌ Error: Could not connect to Arduino: {e}")
        logger.info(f"Available ports:")
        # Try to list available ports
        import serial.tools.list_ports
        ports = list(serial.tools.list_ports.comports())
        for p in ports:
            logger.info(f"  - {p.device}")
        return
    
    # Open webcam
    logger.info(f"Opening camera (index {CAMERA_INDEX})...")
    cap = cv2.VideoCapture(CAMERA_INDEX)
    if not cap.isOpened():
        logger.error(f"❌ Error: Could not open camera {CAMERA_INDEX}")
        logger.info(f"Available cameras: {find_available_cameras()}")
        ser.close()
        return
    logger.info("✓ Camera opened")
    
    # Get camera properties
    frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    logger.info(f"✓ Resolution: {frame_width}x{frame_height} @ {fps:.1f} FPS")
    
    # Initialize tracking variables
    current_yaw = 90  # Center position
    target_yaw = 90
    current_pitch = DEFAULT_PITCH  # Center position
    target_pitch = DEFAULT_PITCH
    
    logger.info("=" * 60)
    logger.info("Tracking started! Press 'q' to quit")
    logger.info("=" * 60)
    
    # Main loop
    try:
        while True:
            # Read frame
            ret, frame = cap.read()
            if not ret:
                logger.warning("Warning: Failed to capture frame")
                continue
            
            # Flip horizontally for mirror effect
            frame = cv2.flip(frame, 1)
            
            # Convert to grayscale for face detection
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            # Detect faces
            faces = face_cascade.detectMultiScale(
                gray,
                scaleFactor=1.1,
                minNeighbors=4,
                minSize=(100, 100)  # Ignore small detections
            )
            
            # Process detected faces
            for x, y, w, h in faces:
                # Calculate face center
                center_x = x + w // 2
                center_y = y + h // 2
                
                # Draw rectangle around face
                cv2.rectangle(
                    frame, 
                    (x, y), 
                    (x + w, y + h), 
                    (0, 0, 255),  # Red
                    2
                )
                
                # Draw center point
                cv2.circle(
                    frame, 
                    (center_x, center_y), 
                    radius=4, 
                    color=(0, 0, 255),  # Red
                    thickness=-1
                )
                
                # Calculate angles
                # Note: frame_height - center_y flips Y axis
                target_yaw = calculate_angle(center_x, frame_height - center_y)
                target_pitch = calculate_angle(center_y, frame_width - center_x)
                
                # Smooth the angle transition
                current_yaw = smooth_angle(current_yaw, target_yaw)
                current_pitch = smooth_angle(current_pitch, target_pitch)
                
                # Send to Arduino (2-axis control: pitch,yaw)
                data = f"{current_pitch},{current_yaw}\n".encode()
                ser.write(data)
                
                # Display angle on frame
                cv2.putText(
                    frame,
                    f"Pitch: {current_pitch}° Yaw: {current_yaw}°",
                    (x, y - 10),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    (0, 255, 0),
                    2
                )
            
            # Draw center reference point
            cv2.circle(
                frame,
                (frame_width // 2, frame_height // 2),
                radius=4,
                color=(0, 255, 0),  # Green
                thickness=-1
            )
            
            # Draw crosshair
            cv2.line(
                frame,
                (frame_width // 2, 0),
                (frame_width // 2, frame_height),
                (0, 255, 0),
                1
            )
            cv2.line(
                frame,
                (0, frame_height // 2),
                (frame_width, frame_height // 2),
                (0, 255, 0),
                1
            )
            
            # Display status
            status_text = f"Faces: {len(faces)} | Press 'q' to quit"
            cv2.putText(
                frame,
                status_text,
                (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (255, 255, 255),
                2
            )
            
            # Show frame
            cv2.imshow("Laser Turret - Face Tracking", frame)
            
            # Check for quit key
            if cv2.waitKey(FRAME_DELAY_MS) & 0xFF == QUIT_KEY:
                logger.info("Quit requested by user")
                break
                
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
    finally:
        # Cleanup
        logger.info("Cleaning up...")
        cap.release()
        cv2.destroyAllWindows()
        ser.close()
        logger.info("✓ Shutdown complete")


if __name__ == "__main__":
    main()
