#include <Arduino.h>

//Check platformio.ini for the correct pin numbers
int relayPins[] = {PIN_RELAY_1, PIN_RELAY_2, PIN_RELAY_3, PIN_RELAY_4};
int relayCount = sizeof(relayPins) / sizeof(relayPins[0]);

#define RELAY_OFF HIGH
#define RELAY_ON LOW

void setupRelays() {
    for (int i = 0; i < relayCount; i++) {
        pinMode(relayPins[i], OUTPUT);
        digitalWrite(relayPins[i], RELAY_OFF);
    }

    //Use the VCC pin to power the optocoupler on the relay module
    pinMode(PIN_RELAY_VCC, OUTPUT); digitalWrite(PIN_RELAY_VCC, HIGH);
}

int parseRelayCommand(char* command) {
    char buffer[256] = {0};
    strncpy(buffer, command, sizeof(buffer));

    //parse command
    char* token = strtok(buffer, ";");
    if (strcmp(token, "RELAY") != 0) {
        Serial.println("Invalid command");
        return -1;
    }

    token = strtok(NULL, ";");
    
    //use strol
    int relayNumber = strtol(token, NULL, 10);
    if (relayNumber < 1 || relayNumber > relayCount) {
        Serial.println("Invalid relay number");
        return -1;
    }

    token = strtok(NULL, ";");
    if (strcmp(token, "ON") == 0) {
        digitalWrite(relayPins[relayNumber - 1], RELAY_ON);
    } else if (strcmp(token, "OFF") == 0) {
        digitalWrite(relayPins[relayNumber - 1], RELAY_OFF);
    } else {
        Serial.println("Invalid relay state");
        return -1;
    }

    char state[16] = {0};
    strncpy(state, token, sizeof(state));
    
    sprintf(buffer, "Relay %d is %s", relayNumber, state);
    Serial.println(buffer);
    return 0;
}

