


#ifndef _HAMSHIELD_COMMS_H_
#define _HAMSHIELD_COMMS_H_


#if defined(ARDUINO)
#include "Arduino.h"

#define nSEN A1 //15 //
#define CLK A5 //19 //
#define DAT A4 //18 //
#define HAMSHIELD_PWM_PIN 3
#else // assume Raspberry Pi
#include "stdint.h"
#include <wiringPi.h>
#include <softTone.h>

#define nSEN 17 //
#define CLK 22 //
#define DAT 27 //
#define HAMSHIELD_PWM_PIN 18
#endif


void HSsetPins(uint8_t ncs, uint8_t clk, uint8_t dat);

int8_t HSreadBitW(uint8_t devAddr, uint8_t regAddr, uint8_t bitNum, uint16_t *data);
int8_t HSreadBitsW(uint8_t devAddr, uint8_t regAddr, uint8_t bitStart, uint8_t length, uint16_t *data);
int8_t HSreadWord(uint8_t devAddr, uint8_t regAddr, uint16_t *data);

bool HSwriteBitW(uint8_t devAddr, uint8_t regAddr, uint8_t bitNum, uint16_t data);
bool HSwriteBitsW(uint8_t devAddr, uint8_t regAddr, uint8_t bitStart, uint8_t length, uint16_t data);
bool HSwriteWord(uint8_t devAddr, uint8_t regAddr, uint16_t data);


// hardware abstraction layer

unsigned long HSmillis();
void HSdelay(unsigned long ms);
void HSdelayMicroseconds(unsigned int us);

void HStone(uint8_t pin, unsigned int frequency);
void HStone(uint8_t pin, unsigned int frequency, unsigned long duration);
void HSnoTone(uint8_t pin);


#endif /* _HAMSHIELD_COMMS_H_ */