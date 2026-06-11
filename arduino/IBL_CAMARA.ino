const int triggerPin = 13;
float FPS = 60.0;
unsigned long interval_us;
unsigned long lastTriggerTime = 0;
bool running = false;              // arranca detenido

void setup() {
  Serial.begin(9600);
  pinMode(triggerPin, OUTPUT);
  digitalWrite(triggerPin, LOW);
  interval_us = 1000000.0 / FPS;
  lastTriggerTime = micros();
}

void loop() {
  // Escucha comandos por Serial
  if (Serial.available() > 0) {
    char cmd = Serial.read();
    if (cmd == 's') {              // 's' = start
      interval_us = 1000000.0 / FPS;
      lastTriggerTime = micros(); // reinicia el contador limpio
      running = true;
    } else if (cmd == 'p') {      // 'p' = pause/stop
      running = false;
      digitalWrite(triggerPin, LOW); // garantiza que queda en LOW
    }
  }

  // Solo manda pulsos si está corriendo
  if (running) {
    unsigned long now = micros();
    if (now - lastTriggerTime >= interval_us) {
      lastTriggerTime += interval_us;
      digitalWrite(triggerPin, HIGH);
      delayMicroseconds(500);
      digitalWrite(triggerPin, LOW);
    }
  }
}