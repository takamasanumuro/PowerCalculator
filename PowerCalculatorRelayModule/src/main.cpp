#include <Arduino.h>
#include "relay.hpp"
#include "command_parser.hpp"


void setup() {
	Serial.begin(9600);
	Serial.println("RELAY MODULE | POWER CALCULATOR");

	setupRelays();

	commandHandlers[0] = parseRelayCommand;

}

void loop() {
	GetSerialInput();
}

