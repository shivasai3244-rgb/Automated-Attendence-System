void setup() {

  Serial.begin(115200);
  delay(1000);

  Serial.println("ESP READY");

}

void loop() {

  if (Serial.available()) {

    String name = Serial.readStringUntil('\n');

    Serial.println("-------------------");
    Serial.print("ATTENDANCE MARKED: ");
    Serial.println(name);
    Serial.println("-------------------");

  }

}