#include <Arduino.h>

extern int relayPins[];
extern int relayCount;

#define RELAY_OFF HIGH
#define RELAY_ON LOW

void setupRelays();

/*Expected command format: RELAY;{relay number};{ON/OFF}
RELAY;1;ON
RELAY;1;OFF
RELAY;2;ON
RELAY;2;OFF
*/
int parseRelayCommand(char* command);