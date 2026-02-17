<!-- 
Suggested GitHub Topics: computer-vision, opencv, arduino, servo-control, face-tracking, python, robotics, educational
-->

# LaserTurret

> **⚠️ SAFETY NOTICE: This is an educational computer vision prototype only. Read the Safety section before use.**

A computer vision experiment using OpenCV face detection to control a 2-axis servo mount via Arduino serial communication.

## What It Is

This project demonstrates real-time face tracking using OpenCV, with servo motors controlled by an Arduino to physically orient a mounted object (originally designed for a pointer device) toward detected faces.

## Why It Exists

Built as a learning exercise to explore:
- Real-time computer vision with OpenCV
- Coordinate transformation from 2D image space to angular servo control
- Python-Arduino serial communication
- Hardware-software integration

## ⚠️ Safety Notice (Critical)

**THIS PROJECT IS AN EDUCATIONAL PROTOTYPE ONLY.**

### Laser Safety
- **DO NOT use an actual laser module with this project when targeting faces**
- Even low-power lasers can cause permanent eye damage
- If demonstrating face-tracking, use an **LED** or other non-coherent light source instead
- Never aim any light-emitting device at people's eyes

### Safe Demo Options
1. **LED Mode** (Recommended): Replace the laser with a standard LED for safe visual indication
2. **No-Light Mode**: Use the servo movement alone to demonstrate tracking
3. **Target Cardboard**: Point at inanimate objects only (cardboard cutouts, walls)

### Recommended Hardware Modification
Remove the laser module entirely and use:
- A bright LED (5mm or 10mm)
- A small cardboard pointer
- A toy flag or indicator

## Tech Stack

- **Python 3** - Main application logic
- **OpenCV** - Face detection using Haar cascades
- **PySerial** - Arduino communication
- **Arduino C++** - Servo control firmware
- **Hardware**: Arduino UNO/Nano, 2x SG90 servos, webcam

## How It Works

1. Python captures webcam video using OpenCV
2. Face detection identifies face bounding boxes
3. Face center coordinates are transformed to angular coordinates using `arctan`
4. Angles are sent via serial to Arduino
5. Arduino moves servos to orient the mount toward the face

### Coordinate System

```
        Webcam Frame
    ┌─────────────────┐
    │    (c_x, c_y)   │ ← Face center
    │        ●        │
    │       /│        │
    │      / θ        │ ← yaw angle
    │     /____________│
    └─────────────────┘
           ↓
    Transformed to servo angles
```

- Pitch (x-axis): Vertical angle
- Yaw (y-axis): Horizontal angle
- `c_x`, `c_y`: Face center coordinates in pixel space
- Z-distance: Estimated/fixed distance for angle calculation

## Project Structure

```
LaserTurret/
├── facialRecog.py          # Main face detection & angle calculation
├── serialPy.py             # Serial test script (random angles)
├── motorControls/
│   └── motorControls.ino   # Arduino servo firmware
├── requirements.txt        # Python dependencies
├── assets/                 # Documentation images
└── README.md
```

## How to Run

### Prerequisites
- Python 3.8+
- Arduino IDE
- Webcam
- Arduino UNO/Nano
- 2x SG90 servos
- Breadboard and jumper wires

### 1. Install Python Dependencies

```bash
pip install -r requirements.txt
```

### 2. Upload Arduino Firmware

1. Open `motorControls/motorControls.ino` in Arduino IDE
2. Connect your Arduino via USB
3. Select correct board and port
4. Upload the sketch

### 3. Configure Serial Port

Edit `facialRecog.py` and update the serial port:

```python
# macOS example
ser = serial.Serial("/dev/cu.usbmodemXXXXXXX", 9600)

# Linux example
ser = serial.Serial("/dev/ttyACM0", 9600)

# Windows example
ser = serial.Serial("COM3", 9600)
```

Find your port in Arduino IDE under Tools > Port.

### 4. Run the Application

```bash
python facialRecog.py
```

- Press `q` to quit
- Ensure adequate lighting for face detection
- Stand 1-2 meters from the webcam

### Hardware Wiring

```
Arduino Pin 9  → Pitch Servo Signal
Arduino Pin 10 → Yaw Servo Signal
5V             → Servo VCC (both)
GND            → Servo GND (both)
USB            → Computer
```

## Key Learnings

- **Coordinate Transformation**: Converting pixel coordinates to angular servo positions requires careful calibration and understanding of the physical setup
- **Serial Communication**: Reliable Python-Arduino communication requires proper baud rate matching and delay allowances for connection establishment
- **Real-time Processing**: Face detection frame rate impacts servo smoothness; balancing detection accuracy vs. performance is important
- **Hardware Constraints**: Servo speed and range limitations affect tracking responsiveness

## Known Limitations

- Single-axis control currently implemented (yaw only)
- Fixed distance assumption for angle calculation
- Haar cascade detection can be sensitive to lighting
- Hardcoded serial port path
- No distance measurement (Z-coordinate is estimated)

## Future Improvements

- [ ] Add LED mode toggle in software
- [ ] Implement two-axis (pitch + yaw) control
- [ ] Add distance estimation using face size
- [ ] Configuration file for serial port and camera selection
- [ ] Smoother servo movement with easing functions

## Safety Checklist

Before running this project:
- [ ] Laser module removed or replaced with LED
- [ ] All participants aware of moving servos
- [ ] Servos mounted securely
- [ ] Power supply adequate for servos
- [ ] Demo environment clear of obstacles

## License

MIT License - See [LICENSE](LICENSE) file

## Disclaimer

This software is provided for educational purposes only. The authors assume no liability for any damage or injury resulting from the use of this software or associated hardware. Users are solely responsible for ensuring safe operation and compliance with local regulations.
