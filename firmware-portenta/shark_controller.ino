/*
 * Shark Robot Controller - Portenta H7 Firmware
 * 
 * Receives commands via WiFi HTTP and controls motors
 * Designed to interface with the robot's motor drivers
 * 
 * Hardware connections (adjust based on your wiring):
 * - Left wheel motor:  PWM on D5, DIR on D6
 * - Right wheel motor: PWM on D7, DIR on D8  
 * - Vacuum motor:      PWM on D9
 * - Main brush:        PWM on D10
 * - Side brush:        PWM on D11
 */

#include <WiFi.h>
#include <WebServer.h>
#include <ArduinoJson.h>

// WiFi credentials - UPDATE THESE
const char* ssid = "Evolving Software";
const char* password = "YOUR_WIFI_PASSWORD";  // Update this!

// Motor pin definitions - UPDATE BASED ON YOUR WIRING
#define LEFT_MOTOR_PWM    5
#define LEFT_MOTOR_DIR    6
#define RIGHT_MOTOR_PWM   7
#define RIGHT_MOTOR_DIR   8
#define VACUUM_PWM        9
#define MAIN_BRUSH_PWM    10
#define SIDE_BRUSH_PWM    11

// Sensor pins (if connected)
#define BUMPER_LEFT       A0
#define BUMPER_RIGHT      A1
#define CLIFF_LEFT        A2
#define CLIFF_RIGHT       A3
#define CLIFF_FRONT       A4

// Motor state
int leftSpeed = 0;
int rightSpeed = 0;
int vacuumPower = 0;
int brushSpeed = 0;
unsigned long driveEndTime = 0;

WebServer server(8080);

void setup() {
  Serial.begin(115200);
  delay(1000);
  
  Serial.println("Shark Robot Controller - Portenta H7");
  Serial.println("=====================================");
  
  // Initialize motor pins
  pinMode(LEFT_MOTOR_PWM, OUTPUT);
  pinMode(LEFT_MOTOR_DIR, OUTPUT);
  pinMode(RIGHT_MOTOR_PWM, OUTPUT);
  pinMode(RIGHT_MOTOR_DIR, OUTPUT);
  pinMode(VACUUM_PWM, OUTPUT);
  pinMode(MAIN_BRUSH_PWM, OUTPUT);
  pinMode(SIDE_BRUSH_PWM, OUTPUT);
  
  // Initialize sensor pins
  pinMode(BUMPER_LEFT, INPUT_PULLUP);
  pinMode(BUMPER_RIGHT, INPUT_PULLUP);
  pinMode(CLIFF_LEFT, INPUT);
  pinMode(CLIFF_RIGHT, INPUT);
  pinMode(CLIFF_FRONT, INPUT);
  
  // Stop all motors initially
  stopAllMotors();
  
  // Connect to WiFi
  connectWiFi();
  
  // Setup HTTP endpoints
  setupServer();
  
  Serial.println("Ready for commands!");
}

void connectWiFi() {
  Serial.print("Connecting to WiFi: ");
  Serial.println(ssid);
  
  WiFi.begin(ssid, password);
  
  int attempts = 0;
  while (WiFi.status() != WL_CONNECTED && attempts < 30) {
    delay(500);
    Serial.print(".");
    attempts++;
  }
  
  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("\nWiFi connected!");
    Serial.print("IP address: ");
    Serial.println(WiFi.localIP());
  } else {
    Serial.println("\nWiFi connection failed! Starting AP mode...");
    
    // Start AP mode as fallback
    WiFi.softAP("SharkRobot", "shark1234");
    Serial.print("AP IP address: ");
    Serial.println(WiFi.softAPIP());
  }
}

void setupServer() {
  // Status endpoint
  server.on("/status", HTTP_GET, handleStatus);
  
  // Sensor endpoint
  server.on("/sensors", HTTP_GET, handleSensors);
  
  // Drive endpoint
  server.on("/drive", HTTP_POST, handleDrive);
  server.on("/drive", HTTP_GET, handleDrive);
  
  // Stop endpoint
  server.on("/stop", HTTP_GET, handleStop);
  server.on("/stop", HTTP_POST, handleStop);
  
  // Vacuum control
  server.on("/vacuum", HTTP_POST, handleVacuum);
  server.on("/vacuum", HTTP_GET, handleVacuum);
  
  // Brush control
  server.on("/brush", HTTP_POST, handleBrush);
  server.on("/brush", HTTP_GET, handleBrush);
  
  // Root endpoint
  server.on("/", HTTP_GET, []() {
    server.send(200, "application/json", "{\"status\":\"ok\",\"device\":\"shark-robot-portenta\"}");
  });
  
  server.begin();
  Serial.println("HTTP server started on port 8080");
}

void handleStatus() {
  StaticJsonDocument<512> doc;
  
  doc["status"] = "online";
  doc["wifi_rssi"] = WiFi.RSSI();
  doc["ip"] = WiFi.localIP().toString();
  
  JsonObject motors = doc.createNestedObject("motors");
  motors["left_speed"] = leftSpeed;
  motors["right_speed"] = rightSpeed;
  motors["vacuum_power"] = vacuumPower;
  motors["brush_speed"] = brushSpeed;
  
  doc["uptime_ms"] = millis();
  
  String response;
  serializeJson(doc, response);
  server.send(200, "application/json", response);
}

void handleSensors() {
  StaticJsonDocument<512> doc;
  
  doc["bumper_left"] = !digitalRead(BUMPER_LEFT);  // Active low
  doc["bumper_right"] = !digitalRead(BUMPER_RIGHT);
  doc["cliff_left"] = analogRead(CLIFF_LEFT);
  doc["cliff_right"] = analogRead(CLIFF_RIGHT);
  doc["cliff_front"] = analogRead(CLIFF_FRONT);
  
  String response;
  serializeJson(doc, response);
  server.send(200, "application/json", response);
}

void handleDrive() {
  StaticJsonDocument<256> doc;
  
  if (server.hasArg("plain")) {
    deserializeJson(doc, server.arg("plain"));
  } else {
    // Handle URL parameters
    if (server.hasArg("left")) doc["left"] = server.arg("left").toInt();
    if (server.hasArg("right")) doc["right"] = server.arg("right").toInt();
    if (server.hasArg("duration")) doc["duration"] = server.arg("duration").toInt();
  }
  
  leftSpeed = constrain(doc["left"] | 0, -100, 100);
  rightSpeed = constrain(doc["right"] | 0, -100, 100);
  int duration = doc["duration"] | 0;
  
  // Set drive end time if duration specified
  if (duration > 0) {
    driveEndTime = millis() + duration;
  } else {
    driveEndTime = 0;  // Continuous
  }
  
  // Apply motor speeds
  setMotorSpeed(LEFT_MOTOR_PWM, LEFT_MOTOR_DIR, leftSpeed);
  setMotorSpeed(RIGHT_MOTOR_PWM, RIGHT_MOTOR_DIR, rightSpeed);
  
  Serial.printf("Drive: L=%d R=%d duration=%dms\n", leftSpeed, rightSpeed, duration);
  
  StaticJsonDocument<128> response;
  response["status"] = "ok";
  response["left"] = leftSpeed;
  response["right"] = rightSpeed;
  response["duration"] = duration;
  
  String responseStr;
  serializeJson(response, responseStr);
  server.send(200, "application/json", responseStr);
}

void handleStop() {
  stopAllMotors();
  
  Serial.println("STOP command received");
  server.send(200, "application/json", "{\"status\":\"stopped\"}");
}

void handleVacuum() {
  StaticJsonDocument<128> doc;
  
  if (server.hasArg("plain")) {
    deserializeJson(doc, server.arg("plain"));
  } else if (server.hasArg("power")) {
    doc["power"] = server.arg("power").toInt();
  }
  
  vacuumPower = constrain(doc["power"] | 0, 0, 100);
  
  int pwmValue = map(vacuumPower, 0, 100, 0, 255);
  analogWrite(VACUUM_PWM, pwmValue);
  
  Serial.printf("Vacuum power: %d%%\n", vacuumPower);
  
  StaticJsonDocument<64> response;
  response["status"] = "ok";
  response["power"] = vacuumPower;
  
  String responseStr;
  serializeJson(response, responseStr);
  server.send(200, "application/json", responseStr);
}

void handleBrush() {
  StaticJsonDocument<128> doc;
  
  if (server.hasArg("plain")) {
    deserializeJson(doc, server.arg("plain"));
  } else if (server.hasArg("speed")) {
    doc["speed"] = server.arg("speed").toInt();
  }
  
  brushSpeed = constrain(doc["speed"] | 0, 0, 100);
  
  int pwmValue = map(brushSpeed, 0, 100, 0, 255);
  analogWrite(MAIN_BRUSH_PWM, pwmValue);
  analogWrite(SIDE_BRUSH_PWM, pwmValue);
  
  Serial.printf("Brush speed: %d%%\n", brushSpeed);
  
  StaticJsonDocument<64> response;
  response["status"] = "ok";
  response["speed"] = brushSpeed;
  
  String responseStr;
  serializeJson(response, responseStr);
  server.send(200, "application/json", responseStr);
}

void setMotorSpeed(int pwmPin, int dirPin, int speed) {
  // Speed: -100 to 100
  // Negative = reverse
  
  if (speed >= 0) {
    digitalWrite(dirPin, HIGH);  // Forward
  } else {
    digitalWrite(dirPin, LOW);   // Reverse
    speed = -speed;
  }
  
  int pwmValue = map(speed, 0, 100, 0, 255);
  analogWrite(pwmPin, pwmValue);
}

void stopAllMotors() {
  leftSpeed = 0;
  rightSpeed = 0;
  driveEndTime = 0;
  
  analogWrite(LEFT_MOTOR_PWM, 0);
  analogWrite(RIGHT_MOTOR_PWM, 0);
  
  Serial.println("All motors stopped");
}

void loop() {
  server.handleClient();
  
  // Check if timed drive should end
  if (driveEndTime > 0 && millis() >= driveEndTime) {
    stopAllMotors();
    Serial.println("Drive duration ended");
  }
  
  // Safety: Check cliff sensors and stop if detected
  int cliffThreshold = 100;  // Adjust based on sensor
  if (analogRead(CLIFF_LEFT) < cliffThreshold ||
      analogRead(CLIFF_RIGHT) < cliffThreshold ||
      analogRead(CLIFF_FRONT) < cliffThreshold) {
    if (leftSpeed != 0 || rightSpeed != 0) {
      Serial.println("CLIFF DETECTED - Emergency stop!");
      stopAllMotors();
    }
  }
  
  // Safety: Check bumpers and stop if hit
  if (!digitalRead(BUMPER_LEFT) || !digitalRead(BUMPER_RIGHT)) {
    if (leftSpeed > 0 || rightSpeed > 0) {  // Only if moving forward
      Serial.println("BUMPER HIT - Stopping");
      stopAllMotors();
    }
  }
  
  delay(10);  // Small delay for stability
}
