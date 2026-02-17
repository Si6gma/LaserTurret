#!/usr/bin/env python3
"""
Web Control Interface for Pi Gimbal Stabilizer

Provides a web-based control panel accessible from any device on the network.
Features:
- Live MJPEG video stream
- Virtual joystick for manual pan/tilt
- Real-time status display
- Toggle stabilization and tracking
- Photo capture button
- Mobile-friendly responsive design

Usage:
    python web_server.py
    
Then open browser to: http://[pi-ip-address]:5000
"""

import logging
import threading
import time
import io
import base64
from flask import Flask, render_template, Response, jsonify, request
from flask_cors import CORS
import cv2
import numpy as np

# Import our gimbal modules
from gimbal_controller import GimbalController
from servo_driver import ServoDriver
from imu_sensor import IMUSensor
from stabilizer import Stabilizer
from auto_framing import AutoFramer

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

class WebGimbalController:
    """Gimbal controller with web interface capabilities."""
    
    def __init__(self):
        self.running = False
        self.frame = None
        self.frame_lock = threading.Lock()
        
        # Initialize gimbal components
        self.servo = ServoDriver()
        self.imu = IMUSensor()
        self.stabilizer = Stabilizer()
        self.framer = AutoFramer()
        
        # Camera
        self.cap = cv2.VideoCapture(0)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
        
        # Control state
        self.manual_mode = False
        self.manual_pitch = 90.0
        self.manual_yaw = 90.0
        self.stabilization_enabled = True
        self.tracking_enabled = True
        
        # Status
        self.status = {
            'pitch': 90.0,
            'yaw': 90.0,
            'stabilization': False,
            'tracking': False,
            'subject_detected': False,
            'fps': 0
        }
        
        # Start IMU
        self.imu.start()
        
        # Start control loop
        self.control_thread = threading.Thread(target=self._control_loop, daemon=True)
        self.control_thread.start()
        
        logger.info("Web Gimbal Controller initialized")
    
    def _control_loop(self):
        """Main control loop running in background."""
        last_time = time.time()
        frame_count = 0
        fps_time = time.time()
        
        while True:
            loop_start = time.time()
            dt = loop_start - last_time
            last_time = loop_start
            
            # Read frame
            ret, frame = self.cap.read()
            if not ret:
                continue
            
            frame = cv2.flip(frame, 1)
            
            # Get IMU data
            imu_data = self.imu.get_reading()
            
            # Detect subject
            subject_data = self.framer.process_frame(frame)
            
            # Calculate angles
            if self.manual_mode:
                # Manual control from web
                target_pitch = self.manual_pitch
                target_yaw = self.manual_yaw
            elif subject_data.detected and self.tracking_enabled:
                # Auto-framing
                target = self.framer.calculate_framing(
                    subject_data.bbox,
                    frame.shape[:2]
                )
                target_pitch, target_yaw = target
            else:
                # Return to center
                target_pitch, target_yaw = 90.0, 90.0
            
            # Apply stabilization
            if self.stabilization_enabled and imu_data.valid:
                comp = self.stabilizer.calculate_compensation(
                    imu_data.gyro, imu_data.accel, dt
                )
                target_pitch -= comp[0] * dt * 50
                target_yaw -= comp[1] * dt * 50
            
            # Clamp and set
            target_pitch = np.clip(target_pitch, 0, 180)
            target_yaw = np.clip(target_yaw, 0, 180)
            
            self.servo.set_position(target_pitch, target_yaw)
            
            # Draw overlays
            display = self._draw_overlays(frame, subject_data, target_pitch, target_yaw)
            
            # Update frame for streaming
            with self.frame_lock:
                self.frame = display.copy()
            
            # Update status
            self.status['pitch'] = round(target_pitch, 1)
            self.status['yaw'] = round(target_yaw, 1)
            self.status['stabilization'] = self.stabilization_enabled
            self.status['tracking'] = self.tracking_enabled
            self.status['subject_detected'] = subject_data.detected
            
            # Calculate FPS
            frame_count += 1
            if time.time() - fps_time >= 1.0:
                self.status['fps'] = frame_count
                frame_count = 0
                fps_time = time.time()
    
    def _draw_overlays(self, frame, subject_data, pitch, yaw):
        """Draw UI overlays on frame."""
        display = frame.copy()
        h, w = display.shape[:2]
        
        # Draw rule of thirds
        third_x = w // 3
        third_y = h // 3
        cv2.line(display, (third_x, 0), (third_x, h), (50, 50, 50), 1)
        cv2.line(display, (2*third_x, 0), (2*third_x, h), (50, 50, 50), 1)
        cv2.line(display, (0, third_y), (w, third_y), (50, 50, 50), 1)
        cv2.line(display, (0, 2*third_y), (w, 2*third_y), (50, 50, 50), 1)
        
        # Draw subject box
        if subject_data.detected:
            x, y, bw, bh = subject_data.bbox
            cv2.rectangle(display, (x, y), (x+bw, y+bh), (0, 255, 0), 2)
            cv2.circle(display, subject_data.center, 5, (0, 255, 0), -1)
        
        # Status overlay (top bar)
        bar_height = 40
        overlay = display.copy()
        cv2.rectangle(overlay, (0, 0), (w, bar_height), (0, 0, 0), -1)
        display = cv2.addWeighted(overlay, 0.7, display, 0.3, 0)
        
        # Status text
        status_text = f"P:{pitch:.0f}° Y:{yaw:.0f}° | STAB:{'ON' if self.stabilization_enabled else 'OFF'} | TRACK:{'ON' if self.tracking_enabled else 'OFF'} | {self.status['fps']} FPS"
        cv2.putText(display, status_text, (10, 28), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        
        # Mode indicator
        mode = "MANUAL" if self.manual_mode else ("TRACKING" if self.tracking_enabled else "CENTER")
        color = (0, 165, 255) if self.manual_mode else (0, 255, 0)
        cv2.putText(display, mode, (w - 120, 28), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
        
        return display
    
    def get_frame_jpeg(self):
        """Get current frame as JPEG bytes."""
        with self.frame_lock:
            if self.frame is None:
                return None
            ret, jpeg = cv2.imencode('.jpg', self.frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
            if ret:
                return jpeg.tobytes()
        return None
    
    def set_manual_position(self, pitch, yaw):
        """Set manual gimbal position."""
        self.manual_pitch = np.clip(pitch, 0, 180)
        self.manual_yaw = np.clip(yaw, 0, 180)
        self.manual_mode = True
    
    def disable_manual(self):
        """Return to automatic mode."""
        self.manual_mode = False
    
    def toggle_stabilization(self):
        """Toggle stabilization on/off."""
        self.stabilization_enabled = not self.stabilization_enabled
        return self.stabilization_enabled
    
    def toggle_tracking(self):
        """Toggle tracking on/off."""
        self.tracking_enabled = not self.tracking_enabled
        return self.tracking_enabled
    
    def capture_photo(self):
        """Capture a photo."""
        import os
        from datetime import datetime
        
        os.makedirs('./photos', exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"./photos/web_capture_{timestamp}.jpg"
        
        with self.frame_lock:
            if self.frame is not None:
                cv2.imwrite(filename, self.frame)
                logger.info(f"Photo captured: {filename}")
                return filename
        return None
    
    def center(self):
        """Center the gimbal."""
        self.manual_pitch = 90.0
        self.manual_yaw = 90.0
        self.servo.set_position(90, 90)


# Global controller instance
gimbal = WebGimbalController()


def generate_frames():
    """Generator for MJPEG stream."""
    while True:
        frame = gimbal.get_frame_jpeg()
        if frame:
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
        time.sleep(0.033)  # ~30 FPS


# HTML Template
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>Pi Gimbal Control</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: #0d1117;
            color: #c9d1d9;
            min-height: 100vh;
            display: flex;
            flex-direction: column;
        }
        
        .header {
            background: #161b22;
            padding: 15px 20px;
            border-bottom: 1px solid #30363d;
        }
        
        .header h1 {
            font-size: 1.5rem;
            color: #8A00FF;
        }
        
        .main {
            flex: 1;
            display: flex;
            flex-direction: column;
            padding: 20px;
            gap: 20px;
            max-width: 1200px;
            margin: 0 auto;
            width: 100%;
        }
        
        .video-container {
            position: relative;
            width: 100%;
            max-width: 800px;
            margin: 0 auto;
            border-radius: 12px;
            overflow: hidden;
            background: #000;
            box-shadow: 0 4px 20px rgba(0,0,0,0.5);
        }
        
        .video-container img {
            width: 100%;
            display: block;
        }
        
        .status-bar {
            display: flex;
            justify-content: center;
            gap: 20px;
            flex-wrap: wrap;
            padding: 15px;
            background: #161b22;
            border-radius: 10px;
            border: 1px solid #30363d;
        }
        
        .status-item {
            display: flex;
            align-items: center;
            gap: 8px;
            font-size: 0.9rem;
        }
        
        .status-item .dot {
            width: 10px;
            height: 10px;
            border-radius: 50%;
            background: #484f58;
        }
        
        .status-item.active .dot {
            background: #238636;
            box-shadow: 0 0 8px #238636;
        }
        
        .status-item.inactive .dot {
            background: #da3633;
        }
        
        .controls {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 20px;
        }
        
        .control-panel {
            background: #161b22;
            border: 1px solid #30363d;
            border-radius: 12px;
            padding: 20px;
        }
        
        .control-panel h3 {
            margin-bottom: 15px;
            color: #8A00FF;
            font-size: 1.1rem;
        }
        
        .btn {
            background: #21262d;
            border: 1px solid #30363d;
            color: #c9d1d9;
            padding: 12px 24px;
            border-radius: 8px;
            cursor: pointer;
            font-size: 1rem;
            transition: all 0.2s;
            margin: 5px;
            min-width: 120px;
        }
        
        .btn:hover {
            background: #30363d;
            border-color: #8A00FF;
        }
        
        .btn.active {
            background: #8A00FF;
            border-color: #8A00FF;
            color: white;
        }
        
        .btn.capture {
            background: #238636;
            border-color: #238636;
            color: white;
            font-weight: bold;
        }
        
        .btn.capture:hover {
            background: #2ea043;
        }
        
        .joystick-container {
            width: 200px;
            height: 200px;
            background: #0d1117;
            border: 2px solid #30363d;
            border-radius: 50%;
            position: relative;
            margin: 20px auto;
            touch-action: none;
        }
        
        .joystick {
            width: 60px;
            height: 60px;
            background: linear-gradient(135deg, #FF0048, #8A00FF);
            border-radius: 50%;
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            cursor: grab;
            box-shadow: 0 4px 15px rgba(138, 0, 255, 0.4);
            transition: transform 0.1s;
        }
        
        .joystick:active {
            cursor: grabbing;
        }
        
        .joystick-center {
            width: 6px;
            height: 6px;
            background: #484f58;
            border-radius: 50%;
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
        }
        
        .angle-display {
            text-align: center;
            margin-top: 10px;
            font-family: monospace;
            font-size: 0.9rem;
            color: #8b949e;
        }
        
        .button-group {
            display: flex;
            flex-wrap: wrap;
            justify-content: center;
            gap: 10px;
        }
        
        @media (max-width: 600px) {
            .header h1 {
                font-size: 1.2rem;
            }
            
            .joystick-container {
                width: 180px;
                height: 180px;
            }
            
            .btn {
                padding: 10px 18px;
                font-size: 0.9rem;
            }
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>Pi Gimbal Stabilizer</h1>
    </div>
    
    <div class="main">
        <div class="video-container">
            <img src="/video_feed" alt="Live Feed">
        </div>
        
        <div class="status-bar">
            <div class="status-item" id="status-stab">
                <span class="dot"></span>
                <span>Stabilization</span>
            </div>
            <div class="status-item" id="status-track">
                <span class="dot"></span>
                <span>Tracking</span>
            </div>
            <div class="status-item" id="status-subject">
                <span class="dot"></span>
                <span>Subject</span>
            </div>
            <div class="status-item">
                <span id="fps-display">0 FPS</span>
            </div>
        </div>
        
        <div class="controls">
            <div class="control-panel">
                <h3>Mode Control</h3>
                <div class="button-group">
                    <button class="btn" id="btn-stab" onclick="toggleStab()">Stabilization</button>
                    <button class="btn" id="btn-track" onclick="toggleTrack()">Tracking</button>
                    <button class="btn" onclick="centerGimbal()">Center</button>
                </div>
            </div>
            
            <div class="control-panel">
                <h3>Manual Control</h3>
                <div class="joystick-container" id="joystick-area">
                    <div class="joystick-center"></div>
                    <div class="joystick" id="joystick"></div>
                </div>
                <div class="angle-display">
                    Pitch: <span id="pitch-val">90</span>° | Yaw: <span id="yaw-val">90</span>°
                </div>
            </div>
            
            <div class="control-panel">
                <h3>Camera</h3>
                <div class="button-group">
                    <button class="btn capture" onclick="capturePhoto()">Capture Photo</button>
                </div>
            </div>
        </div>
    </div>
    
    <script>
        // Status polling
        setInterval(updateStatus, 500);
        
        async function updateStatus() {
            try {
                const resp = await fetch('/status');
                const data = await resp.json();
                
                // Update status indicators
                updateIndicator('status-stab', data.stabilization);
                updateIndicator('status-track', data.tracking);
                updateIndicator('status-subject', data.subject_detected);
                document.getElementById('fps-display').textContent = data.fps + ' FPS';
                
                // Update button states
                document.getElementById('btn-stab').classList.toggle('active', data.stabilization);
                document.getElementById('btn-track').classList.toggle('active', data.tracking);
                
                // Update angle display if not manually controlling
                if (!isDragging) {
                    document.getElementById('pitch-val').textContent = data.pitch;
                    document.getElementById('yaw-val').textContent = data.yaw;
                }
            } catch (e) {
                console.error('Status update failed:', e);
            }
        }
        
        function updateIndicator(id, active) {
            const el = document.getElementById(id);
            el.classList.remove('active', 'inactive');
            el.classList.add(active ? 'active' : 'inactive');
        }
        
        // Toggle functions
        async function toggleStab() {
            await fetch('/toggle/stabilization', {method: 'POST'});
            updateStatus();
        }
        
        async function toggleTrack() {
            await fetch('/toggle/tracking', {method: 'POST'});
            updateStatus();
        }
        
        async function centerGimbal() {
            await fetch('/center', {method: 'POST'});
        }
        
        async function capturePhoto() {
            const resp = await fetch('/capture', {method: 'POST'});
            const data = await resp.json();
            if (data.success) {
                alert('Photo captured: ' + data.filename);
            }
        }
        
        // Joystick control
        const joystickArea = document.getElementById('joystick-area');
        const joystick = document.getElementById('joystick');
        let isDragging = false;
        let manualTimeout;
        
        const centerX = 100; // Half of container width
        const centerY = 100;
        const maxDist = 70; // Maximum joystick movement
        
        joystickArea.addEventListener('mousedown', startDrag);
        joystickArea.addEventListener('touchstart', startDrag, {passive: false});
        
        document.addEventListener('mousemove', drag);
        document.addEventListener('touchmove', drag, {passive: false});
        
        document.addEventListener('mouseup', endDrag);
        document.addEventListener('touchend', endDrag);
        
        function startDrag(e) {
            isDragging = true;
            e.preventDefault();
            drag(e);
        }
        
        function drag(e) {
            if (!isDragging) return;
            e.preventDefault();
            
            const rect = joystickArea.getBoundingClientRect();
            const clientX = e.touches ? e.touches[0].clientX : e.clientX;
            const clientY = e.touches ? e.touches[0].clientY : e.clientY;
            
            let x = clientX - rect.left - centerX;
            let y = clientY - rect.top - centerY;
            
            // Clamp to circle
            const dist = Math.sqrt(x*x + y*y);
            if (dist > maxDist) {
                x = x / dist * maxDist;
                y = y / dist * maxDist;
            }
            
            joystick.style.transform = `translate(calc(-50% + ${x}px), calc(-50% + ${y}px))`;
            
            // Convert to angles (0-180)
            const yaw = 90 + (x / maxDist) * 45;  // +/- 45 degrees
            const pitch = 90 - (y / maxDist) * 45;  // Inverted
            
            document.getElementById('pitch-val').textContent = Math.round(pitch);
            document.getElementById('yaw-val').textContent = Math.round(yaw);
            
            // Send to server (throttled)
            clearTimeout(manualTimeout);
            manualTimeout = setTimeout(() => {
                fetch('/manual', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({pitch: pitch, yaw: yaw})
                });
            }, 50);
        }
        
        function endDrag() {
            if (!isDragging) return;
            isDragging = false;
            
            // Reset joystick
            joystick.style.transform = 'translate(-50%, -50%)';
            document.getElementById('pitch-val').textContent = '90';
            document.getElementById('yaw-val').textContent = '90';
            
            // Return to auto mode
            fetch('/manual/disable', {method: 'POST'});
        }
        
        // Initial status
        updateStatus();
    </script>
</body>
</html>
'''


@app.route('/')
def index():
    """Main page."""
    return HTML_TEMPLATE


@app.route('/video_feed')
def video_feed():
    """MJPEG video stream."""
    return Response(generate_frames(),
                   mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route('/status')
def status():
    """Get current status."""
    return jsonify(gimbal.status)


@app.route('/toggle/stabilization', methods=['POST'])
def toggle_stabilization():
    """Toggle stabilization."""
    state = gimbal.toggle_stabilization()
    return jsonify({'stabilization': state})


@app.route('/toggle/tracking', methods=['POST'])
def toggle_tracking():
    """Toggle tracking."""
    state = gimbal.toggle_tracking()
    return jsonify({'tracking': state})


@app.route('/manual', methods=['POST'])
def manual_control():
    """Set manual position."""
    data = request.json
    pitch = data.get('pitch', 90)
    yaw = data.get('yaw', 90)
    gimbal.set_manual_position(pitch, yaw)
    return jsonify({'success': True, 'pitch': pitch, 'yaw': yaw})


@app.route('/manual/disable', methods=['POST'])
def disable_manual():
    """Disable manual mode."""
    gimbal.disable_manual()
    return jsonify({'success': True})


@app.route('/center', methods=['POST'])
def center():
    """Center the gimbal."""
    gimbal.center()
    return jsonify({'success': True})


@app.route('/capture', methods=['POST'])
def capture():
    """Capture photo."""
    filename = gimbal.capture_photo()
    return jsonify({'success': filename is not None, 'filename': filename})


def main():
    """Run web server."""
    import socket
    
    # Get IP address
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('10.255.255.255', 1))
        ip = s.getsockname()[0]
    except:
        ip = '127.0.0.1'
    finally:
        s.close()
    
    print(f"\n{'='*50}")
    print(f"Pi Gimbal Web Control")
    print(f"{'='*50}")
    print(f"Open in browser: http://{ip}:5000")
    print(f"{'='*50}\n")
    
    app.run(host='0.0.0.0', port=5000, threaded=True, debug=False)


if __name__ == '__main__':
    main()
