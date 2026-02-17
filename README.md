# Laser Turret

> Computer vision-powered face tracking with Arduino-controlled servos

⚠️ **SAFETY FIRST**: This project involves moving servos. Read the [Safety Section](#safety) before use.

---

## ✨ Features

- 🎯 **Real-time face tracking** using OpenCV Haar cascades
- 🔄 **2-axis servo control** (pitch + yaw) via Arduino
- 🔌 **Serial communication** between Python and Arduino
- 🖥️ **Live video preview** with face detection overlay
- ⚡ **Responsive tracking** with coordinate transformation

---

## 📋 Requirements

### Hardware
| Component | Specification |
|-----------|--------------|
| Arduino | UNO, Nano, or Mega |
| Servos | 2x SG90 micro servos |
| Camera | USB webcam or built-in |
| Cables | USB cable, jumper wires |
| Power | 5V 1A (USB powered) |

### Software
- Python 3.8+
- Arduino IDE 1.8+ or Arduino CLI
- OpenCV Python bindings

---

## 🚀 Installation

### Step 1: Clone the Repository
```bash
git clone https://github.com/Si6gma/LaserTurret.git
cd LaserTurret
```

### Step 2: Install Python Dependencies
```bash
pip install -r requirements.txt
```

Requirements:
- `opencv-python>=4.5.0`
- `pyserial>=3.5`
- `numpy>=1.20.0`

### Step 3: Configure Serial Port
Copy the example config and edit:
```bash
cp config_local_example.py config_local.py
```

Edit `config_local.py`:
```python
SERIAL_PORT = "/dev/cu.usbmodemXXXXXXX"  # macOS
# SERIAL_PORT = "/dev/ttyACM0"           # Linux
# SERIAL_PORT = "COM3"                   # Windows
SERIAL_BAUD = 9600
CAMERA_INDEX = 0  # 0=default, 1=external webcam
```

Find your port:
- **macOS/Linux**: `ls /dev/tty.*` or `ls /dev/cu.*`
- **Windows**: Check Device Manager → Ports (COM & LPT)
- **Arduino IDE**: Tools → Port

### Step 4: Upload Arduino Firmware
1. Open `motorControls/motorControls.ino` in Arduino IDE
2. Select your board: Tools → Board → Arduino UNO (or your board)
3. Select port: Tools → Port → [your port]
4. Click Upload (→)

### Step 5: Wire the Hardware
```
Arduino Pin 9  → Pitch Servo Signal (orange/yellow)
Arduino Pin 10 → Yaw Servo Signal   (orange/yellow)
5V             → Servo VCC (red)    (both servos)
GND            → Servo GND (brown)  (both servos)
USB            → Computer
```

---

## 💻 Usage

### Start the Tracking
```bash
python facialRecog.py
```

### Controls
| Key | Action |
|-----|--------|
| `q` | Quit application |

### Expected Output
```
Connecting to Arduino on /dev/cu.usbmodemDC5475C3BB642...
⚠️  SAFETY REMINDER: Ensure laser is removed or replaced with LED before use!
Press 'q' to quit

Video resolution: 640x480
b'45'
b'46'
b'44'
...
```

### Window Preview
You should see:
- Live webcam feed with a **red rectangle** around detected faces
- **Red dot** at the center of detected face
- **Green dot** at the center of the frame
- Servos moving to track your face

---

## 🔧 Calibration

### Servo Range Adjustment
Edit `motorControls/motorControls.ino`:
```cpp
const int PITCH_MIN = 0;    // Minimum pitch angle
const int PITCH_MAX = 180;  // Maximum pitch angle
const int YAW_MIN = 0;      // Minimum yaw angle
const int YAW_MAX = 180;    // Maximum yaw angle
```

### Camera Selection
If you have multiple cameras:
```python
# Try different indices
CAMERA_INDEX = 0  # Default camera
CAMERA_INDEX = 1  # External USB camera
```

### Tracking Smoothness
Adjust in `facialRecog.py`:
```python
# Higher = more smoothing but more lag
SMOOTHING_FACTOR = 0.3
```

---

## 🏗️ Project Structure

```
LaserTurret/
├── facialRecog.py              # Main application
├── config_local_example.py     # Example configuration
├── requirements.txt            # Python dependencies
├── motorControls/
│   └── motorControls.ino       # Arduino firmware
├── assets/                     # Documentation images
└── README.md
```

---

## ⚠️ Safety

### Critical Warnings
1. **NEVER aim at eyes** - Even low-power lasers can cause permanent damage
2. **Secure servos** - Ensure mechanical assembly is stable
3. **Power limits** - Don't exceed servo voltage ratings

### Safe Demo Options
| Mode | Description |
|------|-------------|
| **LED Mode** (Recommended) | Replace laser with LED |
| **Pointer Mode** | Use a cardboard pointer |
| **No-Light Mode** | Servo movement only |

### Pre-Flight Checklist
- [ ] Laser removed or replaced with LED
- [ ] Servos mounted securely
- [ ] All wires connected correctly
- [ ] Power supply adequate
- [ ] Demo area clear

---

## 🐛 Troubleshooting

### "Cannot connect to Arduino"
```bash
# Check available ports
ls /dev/tty.* /dev/cu.*  # macOS/Linux
# or check Device Manager on Windows

# Update config_local.py with correct port
```

### "No camera detected"
```python
# Try different camera indices in config_local.py
CAMERA_INDEX = 0  # Try 0, 1, 2...
```

### "Servos not moving"
- Check wiring (signal, power, ground)
- Verify Arduino sketch uploaded successfully
- Check serial port isn't open in another program

### "Jerky servo movement"
- Increase `delay()` in Arduino code
- Reduce frame rate in OpenCV
- Check power supply (add external 5V if needed)

---

## 🗺️ Roadmap

- [ ] Add LED mode toggle in software
- [ ] Implement full 2-axis (pitch + yaw) control
- [ ] Add distance estimation using face size
- [ ] Configuration file for all settings
- [ ] Smoother servo movement with easing
- [ ] Add calibration wizard

---

## 📚 How It Works

### Coordinate Transformation
```
Webcam Frame (pixels)    →    Angles (degrees)
┌─────────────────┐           ┌─────────────┐
│    (c_x, c_y)   │           │ pitch, yaw  │
│        ●        │  arctan   │      ●      │
│       /│        │  ───────→ │     /       │
│      / θ        │           │    /        │
│     /____________│           │   /_________│
└─────────────────┘           └─────────────┘
```

1. OpenCV detects face → bounding box
2. Calculate center point (c_x, c_y)
3. Transform to angles using `arctan()`
4. Send angles via serial to Arduino
5. Arduino moves servos to position

---

## 📝 License

MIT License - See [LICENSE](LICENSE) file

---

*Built for learning computer vision and hardware integration.*
