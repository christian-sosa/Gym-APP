#include <SPI.h>
#include <MFRC522.h>

#define SS_PIN 10
#define RST_PIN 9
MFRC522 mfrc522(SS_PIN, RST_PIN);

int relayPin = 7; // pin digital conectado al IN del relay

void setup() {
  pinMode(relayPin, OUTPUT);
  digitalWrite(relayPin, HIGH); // relay apagado al inicio (activo en bajo)
  Serial.begin(9600);

  SPI.begin();
  mfrc522.PCD_Init();
}

void loop() {
  // --- 1. Leer UID del RFID ---
  if (mfrc522.PICC_IsNewCardPresent() && mfrc522.PICC_ReadCardSerial()) {
    String uid = "";
    for (byte i = 0; i < mfrc522.uid.size; i++) {
      if (i > 0) uid += "-";
      byte b = mfrc522.uid.uidByte[i];
      if (b < 0x10) uid += "0"; // padding
      uid += String(b, HEX);
    }
    uid.toUpperCase();

    Serial.println(uid); // envía UID al PC
    delay(800); // antirebote
  }

  // --- 2. Escuchar órdenes desde el PC ---
  if (Serial.available() > 0) {
    String orden = Serial.readStringUntil('\n');
    orden.trim();
    if (orden == "OPEN") {
      digitalWrite(relayPin, LOW);  // activa relay (activo en bajo)
      delay(3000);                  // mantiene abierto 3 segundos
      digitalWrite(relayPin, HIGH); // apaga relay
    }
  }
}