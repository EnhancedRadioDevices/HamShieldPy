# Hamshield
# Example: Arduino Like Example
# This is a simple example to demonstrate how to use HamShield
# in an Arduino like way.
#
# This code is based very strongly off of the HamShield examples
# for Arduino. Only minor modifications have been made to
# allow it to work in Python for Raspberry Pi
#
# Connect the HamShield to your Raspberry Pi. Screw the antenna
# into the HamShield RF jack.
# Run this program with:
#     python ArduinoLikeExample.py
#
# Default Pinout for HamShieldMini
# HamShieldMini <-> Raspberry Pi Header Pin Number (not wiringpi #)
# Vin               pin 1 (3.3V)
# GND               pin 6 (GND)
# nCS               pin 11
# DAT               pin 13
# CLK               pin 15
# MIC               pin 12

# if you're using a HamShield (not Mini), also connect the rst line
# RST               pin 16
# Set HAMSHIELD_RST to true to use a reset pin with HamShield (not Mini)
HAMSHIELD_RST = False
RESET_PIN = 4

from HamShieldPy import HamShield
import wiringpi
import threading
import sys, signal

nCS = 0
clk = 3
dat = 2
mic = 1
# create object for radio
radio = HamShield(nCS, clk, dat, mic)
rx_dtmf_buf = ''


#########################################
# sketch functions


# add any sketch specific functions there


#########################################
# setup

def setup():
    if HAMSHIELD_RST:
        wiringpi.pinMode(RESET_PIN, wiringpi.OUTPUT)
        wiringpi.digitalWrite(RESET_PIN, wiringpi.LOW)

    print("type any character and press enter to begin...")

    while (not inputAvailable()):
        pass
    inputFlush()

    if HAMSHIELD_RST:
        # if you're using a standard HamShield (not a Mini)
        # you have to let it out of reset
        wiringpi.digitalWrite(RESET_PIN, wiringpi.HIGH)
        wiringpi.delay(5)  # wait for device to come up

    print("beginning radio setup")
    # initialize device
    radio.initialize()

    # verify connection
    print("Testing device connections...")
    if (radio.testConnection()):
        print("HamShield connection successful")
    else:
        print("HamShield connection failed")

    print("setting default Radio configuration")

    print("setting squelch")
    radio.setSQHiThresh(-10)
    radio.setSQLoThresh(-30)
    print("sq hi: " + str(radio.getSQHiThresh()))
    print("sq lo: " + str(radio.getSQLoThresh()))
    radio.setSQOn()
    # radio.setSQOff()

    print("setting frequency to: ")
    freq = 420000
    radio.frequency(freq)
    print(str(radio.getFrequency()) + "kHz")

    # set RX volume to minimum to reduce false positives on DTMF rx
    radio.setVolume1(6)
    radio.setVolume2(0)

    # set to receive
    radio.setModeReceive()

    radio.setRfPower(0)

    print("ready")


#########################################
# repeating loop

def loop():
    global rx_dtmf_buf
    print("looping, but no action to perform")
    delay(5000);


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


#########################################
# main and safeExit

def safeExit(signum, frame):
    radio.setModeReceive()
    wiringpi.delay(25)
    if HAMSHIELD_RST:
        wiringpi.digitalWrite(RESET_PIN, wiringpi.LOW)
        wiringpi.delay(25)
    sys.exit(1)


if __name__ == '__main__':

    wiringpi.wiringPiSetup()

    inputThread = StdinParser()
    inputThread.daemon = True
    inputThread.start()

    signal.signal(signal.SIGINT, safeExit)

    setup()

    while True:
        try:
            loop()
        except Exception as e:
            print(e)
            bufferLock.acquire()
            inputBuffer = False
            bufferLock.release()
            radio.setModeReceive()
            wiringpi.delay(25)
            if HAMSHIELD_RST:
                wiringpi.digitalWrite(RESET_PIN, wiringpi.LOW)
                wiringpi.delay(25)
            break