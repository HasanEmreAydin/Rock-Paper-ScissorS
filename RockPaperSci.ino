#include <Wire.h>
#include <Adafruit_PWMServoDriver.h>

Adafruit_PWMServoDriver pwm = Adafruit_PWMServoDriver();

#define THUMB 5
#define INDEX 7
#define MIDDLE 9
#define RING 11
#define PINKY 12

#define PINKY_MIN 400
#define PINKY_MAX 180
#define RING_MIN 410
#define RING_MAX 180
#define MIDDLE_MIN 485
#define MIDDLE_MAX 200
#define INDEX_MIN 380
#define INDEX_MAX 120
#define THUMB_MIN 410
#define THUMB_MAX 130

void setup() {
  Serial.begin(9600);
  pwm.begin();
  pwm.setPWMFreq(60);  // Servo motorlar için standart frekans
  openHand();          // Başlangıçta tüm parmaklar açık
}

void loop() {
  if (Serial.available()) {
    String command = Serial.readStringUntil('\n');
    command.trim();

    if (command == "rock") makeRock();
    else if (command == "sci") makeScissors();
    else if (command == "paper") makePaper();
  }
}

void makeRock() {
  moveFingers(PINKY_MAX, RING_MAX, MIDDLE_MAX, INDEX_MAX, THUMB_MAX);
}

void makeScissors() {
  moveFingers(PINKY_MAX, RING_MAX, MIDDLE_MIN, INDEX_MIN, THUMB_MAX);
}

void makePaper() {
  moveFingers(PINKY_MIN, RING_MIN, MIDDLE_MIN, INDEX_MIN, THUMB_MIN);
}

void openHand() {
  moveFingers(PINKY_MIN, RING_MIN, MIDDLE_MIN, INDEX_MIN, THUMB_MIN);
}

// Optimize edilmiş parmak hareketi fonksiyonu
void moveFingers(int pinky, int ring, int middle, int index, int thumb) {
  pwm.setPWM(PINKY, 0, pinky);
  pwm.setPWM(RING, 0, ring);
  pwm.setPWM(MIDDLE, 0, middle);
  pwm.setPWM(INDEX, 0, index);
  pwm.setPWM(THUMB, 0, thumb);
}
