# Hamshield
# Example: DDS
# This is a simple example to demonstrate how to use transmit arbitray
# tones. In this case, the sketh alternates between 1200 Hz
# and 2200Hz at 1s intervals.
#
# This code is based very strongly off of the DDS example
# for Arduino. Only minor modifications have been made to
# allow it to work in Python for Raspberry Pi
#
# Connect the HamShield to your Raspberry Pi. Screw the antenna
# into the HamShield RF jack.
# Run this program with:
#     python DDS.py
#
# Default Pinout for HamShieldMini
# HamShieldMini <-> Raspberry Pi
# Vin               pin 1 (3.3V)
# GND               pin 6 (GND)
# nCS               pin 11
# DAT               pin 13
# CLK               pin 15
# MIC               pin 12

from HamShieldPy import HamShield
import wiringpi
import threading
import sys, signal
import dds # todo???

nCS = 0
clk = 3
dat = 2
mic = 1
# create object for radio
radio = HamShield(nCS, clk, dat, mic)
rx_dtmf_buf = ''


###############################################
# sketch functions

# no sketch functions for this example

###############################################
# StdinParser thanks to Kenkron
#             https://github.com/Kenkron
# creates an input buffer for stdin
bufferLock = threading.Lock()
inputBuffer = ''


class StdinParser(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)

    def run(self):
        global inputBuffer
        running = True
        while running:
            try:
                instruction = raw_input()
                bufferLock.acquire()
                if inputBuffer == False:
                    running = False
                    break
                else:
                    inputBuffer += instruction
                bufferLock.release()
            except EOFError, KeyboardInterrupt:
                running = False
                break

def inputAvailable():
    global inputBuffer, bufferLock
    ret = False
    bufferLock.acquire()
    if len(inputBuffer) > 0:
        ret = True
    bufferLock.release()
    return ret


def inputReadChar():
    global inputBuffer, bufferLock
    c = ''
    bufferLock.acquire()
    if len(inputBuffer) > 0:
        c = inputBuffer[0]
        inputBuffer = inputBuffer[1:]
    bufferLock.release()
    return c


def inputFlush():
    global inputBuffer, bufferLock
    bufferLock.acquire()
    inputBuffer = ''
    bufferLock.release()



###############################################
# setup

def setup():
    global rssi_timeout, currently_tx

    if HAMSHIELD_RST:
        wiringpi.pinMode(RESET_PIN, wiringpi.OUTPUT)
        wiringpi.digitalWrite(RESET_PIN, wiringpi.LOW)


    print("type any character and press enter to begin...")

    while (not inputAvailable()):
        pass
    inputFlush()

    if HAMSHIELD_RST:
        #If you're using a standard HamShield (not a Mini)
        # you have to let it out of reset
        wiringpi.digitalWrite(RESET_PIN, wiringpi.HIGH)
        wiringpi.delay(5) # wait for device to come up

    print("beginning radio setup")
    # initialize device
    radio.initialize()
    radio.setRfPower(0)
    radio.frequency(438000)
    radio.setModeTransmit()
    dds.start()
    dds.startPhaseAccumulator(DDS_USE_ONLY_TIMER2)
    dds.playWait(600,3000)
    dds.on()
    #dds.setAmplitude(31)


###############################################
# repeating loop

def loop():
    dds.setFrequency(2200)
    wiringpi.delay(1000)
    dds.setFrequency(1200)
    wiringpi.delay(1000)

###############################################
# main and safeExit

def safeExit(signum, frame):
    radio.setModeRecieve()
    wiringpi.delay(25)
    sys.exit(1)


if __name__ == '__main__':

    wiringpi.wiringPiSetupGpio()

    inputThread = StdinParser()
    inputThread.daemon = True
    inputThread.start()

    setup()

    while True:
        try:
            loop()
        except Exception as e:
            print(e)
            bufferLock.acquire()
            inputBuffer = False
            bufferLock.release()
            radio.setModeRecive()
            wiringpi.delay(25)
            break
