/**
 * Laser Turret - Arduino Servo Controller
 * 
 * Receives angle commands via serial and controls two servos
 * for pitch and yaw movement.
 * 
 * Hardware:
 *   - Arduino UNO/Nano/Mega
 *   - 2x SG90 micro servos
 * 
 * Wiring:
 *   Pin 9  -> Pitch servo signal
 *   Pin 10 -> Yaw servo signal
 *   5V     -> Servo VCC (both)
 *   GND    -> Servo GND (both)
 */

#include <Servo.h>

// =============================================================================
// CONFIGURATION
// =============================================================================

// Pin assignments
const int PITCH_SERVO_PIN = 9;
const int YAW_SERVO_PIN = 10;
const int LED_PIN = LED_BUILTIN;  // For status indication

// Servo limits (degrees)
const int PITCH_MIN = 0;
const int PITCH_MAX = 180;
const int YAW_MIN = 0;
const int YAW_MAX = 180;

// Movement parameters
const int MOVEMENT_DELAY_MS = 15;      // Delay between servo steps (ms)
const int SERIAL_BAUD = 9600;          // Serial communication speed
const int UPDATE_INTERVAL_MS = 20;     // Main loop delay (ms)

// Smoothing
const float SMOOTHING_FACTOR = 0.2;    // Lower = smoother, higher = more responsive

// =============================================================================
// GLOBALS
// =============================================================================

Servo servoPitch;  // Vertical movement
Servo servoYaw;    // Horizontal movement

// Current positions
int currentPitch = 90;  // Start centered
int currentYaw = 90;    // Start centered

// Target positions
int targetPitch = 90;
int targetYaw = 90;

// Communication
String inputBuffer;
bool newData = false;

// =============================================================================
// SETUP
// =============================================================================

void setup() {
    // Initialize serial communication
    Serial.begin(SERIAL_BAUD);
    while (!Serial) {
        ; // Wait for serial port to connect (native USB boards)
    }
    
    // Initialize LED
    pinMode(LED_PIN, OUTPUT);
    digitalWrite(LED_PIN, LOW);
    
    // Attach servos
    servoPitch.attach(PITCH_SERVO_PIN);
    servoYaw.attach(YAW_SERVO_PIN);
    
    // Move to starting position
    moveToPosition(90, 90);
    
    // Signal ready
    digitalWrite(LED_PIN, HIGH);
    delay(100);
    digitalWrite(LED_PIN, LOW);
    
    Serial.println("# Laser Turret Controller Ready");
    Serial.println("# Format: PITCH,YAW (e.g., '90,90')");
    Serial.println("# Ready for commands...");
}

// =============================================================================
// MAIN LOOP
// =============================================================================

void loop() {
    // Read serial data
    readSerialData();
    
    // Process new command
    if (newData) {
        processCommand(inputBuffer);
        newData = false;
        inputBuffer = "";
    }
    
    // Smooth movement to target
    updateServos();
    
    // Small delay for stability
    delay(UPDATE_INTERVAL_MS);
}

// =============================================================================
// FUNCTIONS
// =============================================================================

/**
 * Read data from serial until newline
 */
void readSerialData() {
    while (Serial.available() > 0) {
        char received = Serial.read();
        
        // Check for end of command
        if (received == '\n' || received == '\r') {
            if (inputBuffer.length() > 0) {
                newData = true;
            }
            return;
        }
        
        // Add to buffer
        inputBuffer += received;
        
        // Prevent buffer overflow
        if (inputBuffer.length() > 20) {
            inputBuffer = "";
            Serial.println("# Error: Command too long");
        }
    }
}

/**
 * Process incoming command
 * Format: "PITCH" or "PITCH,YAW"
 * Example: "90" or "45,120"
 */
void processCommand(String& command) {
    // Trim whitespace
    command.trim();
    
    if (command.length() == 0) {
        return;
    }
    
    Serial.print("# Received: ");
    Serial.println(command);
    
    // Find comma separator
    int commaIndex = command.indexOf(',');
    
    if (commaIndex == -1) {
        // Single value - assume yaw only for backward compatibility
        int yaw = command.toInt();
        targetYaw = constrain(yaw, YAW_MIN, YAW_MAX);
        
        Serial.print("# Setting yaw to: ");
        Serial.println(targetYaw);
    } else {
        // Two values - pitch and yaw
        int pitch = command.substring(0, commaIndex).toInt();
        int yaw = command.substring(commaIndex + 1).toInt();
        
        targetPitch = constrain(pitch, PITCH_MIN, PITCH_MAX);
        targetYaw = constrain(yaw, YAW_MIN, YAW_MAX);
        
        Serial.print("# Setting pitch to: ");
        Serial.print(targetPitch);
        Serial.print(", yaw to: ");
        Serial.println(targetYaw);
    }
}

/**
 * Update servo positions with smoothing
 */
void updateServos() {
    // Calculate smoothed positions
    int newPitch = currentPitch + (targetPitch - currentPitch) * SMOOTHING_FACTOR;
    int newYaw = currentYaw + (targetYaw - currentYaw) * SMOOTHING_FACTOR;
    
    // Apply minimum movement threshold to reduce jitter
    if (abs(newPitch - currentPitch) > 1) {
        currentPitch = newPitch;
        servoPitch.write(currentPitch);
    }
    
    if (abs(newYaw - currentYaw) > 1) {
        currentYaw = newYaw;
        servoYaw.write(currentYaw);
    }
}

/**
 * Move servos to specific position (blocking)
 * Used for initialization
 */
void moveToPosition(int pitch, int yaw) {
    pitch = constrain(pitch, PITCH_MIN, PITCH_MAX);
    yaw = constrain(yaw, YAW_MIN, YAW_MAX);
    
    servoPitch.write(pitch);
    servoYaw.write(yaw);
    
    currentPitch = pitch;
    currentYaw = yaw;
    targetPitch = pitch;
    targetYaw = yaw;
    
    delay(500);  // Wait for servos to reach position
}

/**
 * Smooth movement from current to target (legacy - not used in main loop)
 * Kept for potential future use
 */
void smoothMove(Servo& servo, int target) {
    int current = servo.read();
    target = constrain(target, YAW_MIN, YAW_MAX);
    
    if (target > current) {
        for (int pos = current; pos <= target; pos++) {
            servo.write(pos);
            delay(MOVEMENT_DELAY_MS);
        }
    } else {
        for (int pos = current; pos >= target; pos--) {
            servo.write(pos);
            delay(MOVEMENT_DELAY_MS);
        }
    }
}
