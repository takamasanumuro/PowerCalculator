#include <Arduino.h>

// Command handlers
typedef int (*CommandHandler)(char*);
CommandHandler commandHandlers[32] = {0};
int commandHandlerCount = sizeof(commandHandlers) / sizeof(commandHandlers[0]);

void CheckCommands(CommandHandler* handlers, int handlerCount, char* command) {
    for (int i = 0; i < handlerCount; i++) {
        if (handlers[i] == NULL) {
            continue;
        }

        int result = handlers[i](command);
        if (result == 0) {
            return;
        }
    }
}

void GetSerialInput() {
    constexpr int inputBufferLength = 256;
    static char inputBuffer[inputBufferLength];
    static int bufferIndex = 0;
    
	if (!Serial.available()) {
		return;
	}

	char input = Serial.read();
	if (input == '\r') return;

	if (input == '\n') {
		inputBuffer[bufferIndex] = '\0';
		bufferIndex = 0;
        CheckCommands(commandHandlers, commandHandlerCount, inputBuffer);

	} else {
		inputBuffer[bufferIndex++] = input;
		if (bufferIndex >= inputBufferLength) {
			bufferIndex = 0;
		}
	}  
}

