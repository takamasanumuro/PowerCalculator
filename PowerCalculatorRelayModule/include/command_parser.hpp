#include <Arduino.h>

// Command handlers
typedef int (*CommandHandler)(char*);
extern CommandHandler commandHandlers[32];
extern int commandHandlerCount;

// Function declarations
void CheckCommands(CommandHandler* handlers, int handlerCount, char* command);
void GetSerialInput();