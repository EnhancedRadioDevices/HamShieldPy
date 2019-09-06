# Hamshield
# Example: SSTV
# This program will transmit a test pattern. You will need
# SSTV equipment to test the output.
#
# This program will transmit a test pattern. You will need
# SSTV equipment to test the output.
# Connect the HamShield to your Arduino. Screw the antenna
# into  the HamShield RF jack. Connect the Arduino to wall
# power and then to your computer via USB. After uploading
# this program to your Arduino, open the Serial Monitor to
# view the status of the program. Tune your SSTV to 446 MHz
# to receive the image output.
#
# This code is based very strongly off of the HandyTalkie example
# for Arduino. Only minor modifications have been made to
# allow it to work in Python for Raspberry Pi
#
# Connect the HamShield to your Raspberry Pi. Screw the antenna
# into the HamShield RF jack.
# Run this program with:
#     python SSTV.py
#
# Default Pinout for HamShieldMini
# HamShieldMini <-> Raspberry Pi
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

from HamShieldPy import HamShield, MARTIN1
import wiringpi
import threading
import sys, signal

nCS = 0
clk = 3
dat = 2
mic = 1
# create object for radio
radio = HamShield(nCS, clk, dat, mic)

currently_tx = False
rssi_timeout = 0

# sketch functions


# no sketch functions for this example

#########################
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

def inputFlush():
    global inputBuffer, bufferLock
    bufferLock.acquire()
    inputBuffer = ''
    bufferLock.release()




#################################
# setup

RSSI_REPORT_RATE_MS = 5000


def setup():
    # if not using PWM out, it should be held low to avoid tx output

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

    # verify connection --- this does the part of "initialize serial communication"
    print("Testing device connections...")
    if (radio.testConnection()):
        print("HamShield connection successful")
    else:
        print("HamShield connection failed")

    print("setting default Radio configuration")

    # set frequency
    print("changing frequency")

    radio.setSQOff()
    freq = 446000
    radio.frequency(freq)

    # set to receive

    radio.setModeReceive()


##########################################
# repeating loop

def loop():
    if radio.waitForChannel(1000,2000,-90): # Wait forever for calling frequency to open, then wait 2 seconds for breakers
        radio.setModeTransmit() # Turn on the transmitter
        wiringpi.delay(250)
        radio.SSTVTestPattern(MARTIN1) # send a MARTIN1 test pattern
        wiringpi.delay(250)
        wiringpi.setModeReceive() # Turn off the transmitter
    else:
        wiringpi.delay(30000) # someone broke in fast after prior transmission, was it an emergency? wait 30 secs.

    wiringpi.delay(60000) # Wait a minute


#########################################
# main and exit

def safeExit(signum, frame):
    radio.setModeReceive()
    wiringpi.delay(25)
    if HAMSHIELD_RST:
        wiringpi.digitalWrite(RESET_PIN, wiringpi.LOW)
        wiringpi.delay(25)
    sys.exit(1)


if __name__ == '__main__':

    wiringpi.wiringPiSetup()

    signal.signal(signal.SIGINT, safeExit)

    inputThread = StdinParser()
    inputThread.daemon = True
    inputThread.start()

    setup()

    while True:
        try:
            loop()
        except Exception as e:
            print("loop error: " + str(e))
            bufferLock.acquire()
            inputBuffer = False
            bufferLock.release()
            print("setting to rx")
            radio.setModeReceive()  # just in case we had an Exception while in TX, don't get stuck there
            wiringpi.delay(25)
            if HAMSHIELD_RST:
                wiringpi.digitalWrite(RESET_PIN, wiringpi.LOW)
                wiringpi.delay(25)
            break
