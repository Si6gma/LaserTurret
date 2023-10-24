#include <Servo.h>
// #include <iostream>
// #include <thread>

String data;     // String to hold incoming serial data
int pitch, yaw;  // Variables to hold the pitch and yaw values

Servo servoPitch;  // Servo to control pitch
Servo servo;    // Servo to control yaw
int currentPosition = servo.read();

void setup() {
  Serial.begin(9600);  // Start serial communication at 115200 baud rate

  servoPitch.attach(9);  // Attach the pitch servo to pin 9
  servo.attach(10);   // Attach the yaw servo to pin 10

  // std::thread t(readSerial);
  // t.join();
}

// void loop() {
//   int target = data.toInt();
//   Serial.print("Initial Target: ");
//   Serial.println(target);
//   int currentPosition = servo.read(); // Get the current position of the servo
//   if (target > currentPosition) {
//     for (int pos = currentPosition; pos <= target; pos++) {
//       servo.write(pos);
//       delay(15); // Wait 15ms for the servo to reach the position
//         Serial.print("Yaw Position: ");
//         Serial.println(pos);
//         Serial.print("Target: ");
//         Serial.println(target);
//     }
//   } else {
//     for (int pos = currentPosition; pos >= target; pos--) {
//       servo.write(pos);
//       delay(15); // Wait 15ms for the servo to reach the position
//         Serial.print("Yaw Position: ");
//         Serial.println(pos);
//         Serial.print("Target: ");
//         Serial.println(target);
//     }
//   }
// }

void loop() {
  // int currentPosition = servo.read();
  int target = 0;
  if (Serial.available()) {
  data = Serial.readStringUntil('\n');
    target = data.toInt();
    // target = data;
    Serial.print("Target: ");
    Serial.println(data);

    if (target > currentPosition) {
      servo.write(currentPosition++);
    } else {
      servo.write(currentPosition--);
    }
    delay(15);  // Wait 15ms for the servo to reach the position
    // Serial.print("Position: ");
    // Serial.println(currentPosition);
  }
  delay(100);
}

// void readSerial() {

//   if (Serial.available()) { // Check if data is available to read

//     data = Serial.readStringUntil('\0'); // Read the incoming data until newline character

//     // Find the comma in the string
//     // int commaIndex = data.indexOf(',');

//     // // Split the string into two parts using the comma's index
//     // String pitchString = data.substring(0, commaIndex);
//     // String yawString = data.substring(commaIndex + 1);

//     // // Convert the split strings into integers
//     // pitch = pitchString.toInt();
//     // yaw = yawString.toInt();

//     yaw = data.toInt();
//     // Control the servos using the received pitch and yaw values
//     Serial.print("Yaw: ");
//     Serial.println(yaw);
//     // smoothMove(servoPitch, pitch);

//     // delay(500); // Wait for half a second before reading new positions
//   }
// }
