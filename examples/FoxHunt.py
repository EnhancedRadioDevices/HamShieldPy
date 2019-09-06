# Hamshield
# Example: FoxHunt
#
# Plays a one minute tone, then IDs at 10-13 minute intervals. Script
# will check to see if the channel is clear before it will transmit.
#
# todo: Arduino -> Raspberry
# Connect the HamShield to your Arduino. Screw the antenna
# into the HamShield RF jack. Connect the Arduino to wall
# power and then to your computer via USB. After uploading
# this program to your Arduino, open the Serial Monitor to
# monitor the status of the beacon. To test, set a HandyTalkie
# to 438MHz. You should hear a one-minute tone followed by
# a callsign every 10-13 minutes.

# This code is based very strongly off of the HamShield examples
# for Arduino. Only minor modifications have been made to
# allow it to work in Python for Raspberry Pi
#
# Connect the HamShield to your Raspberry Pi. Screw the antenna
# into the HamShield RF jack.
#
# To test, set a HandyTalkie to 432.4 MHz. You should hear a one minute
# tone followed by a callsign every 10-13 minutes.
#
# Run this program with:
#     python FoxHunt.py
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
import random

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

    # set the transmit power level (0-8)
    radio.setRfPower(0)

    # set the morse code characteristics
    radio.setMorseFreq(600)
    radio.setMorseDotMillis(100)

    # Configure the HamShield to operate on 438.000Mhz
    radio.frequency(432400)

    print("Radio configured.")


#########################################
# repeating loop

def waitMinute(period):
    print("Waiting for " + str(period) + " minutes.")
    wiringpi.delay(period * 60 * 1000)

def loop():
    # In milliseconds
    TRANSMITLENGTH = 600
    # In minutes
    INTERVAL = 10
    RANDOMCHANCE = 3

    # We'll wait up to 30 seconds for a a clear channel,
    # requiring that the channel is clear for 2 seconds before we transmit
    if radio.waitForChannel(30000,2000,-90):
        # If we get here, the channel is clear. Let's print the RSSI as well
        print("Signal is clear, RSSI: ", radio.readRSSI())

        # Set the HamShield to TX
        print("Transmitting...")
        radio.setModeTransmit()


        # Generate a 600Hz tone for TRANSMITLENGTH time
        radio.HStone(mic, 700)
        wiringpi.delay(TRANSMITLENGTH)
        radio.HSnoTone(mic)

        # Identify the transmitter
        radio.morseOut(" CALLSIGN FOXHUNT")

        # Set the HamShield back to RX
        radio.setModeReceive()
        print("Done.")

        # Wait for INTERVAL + some random minutes before transmitting again
        waitMinute(INTERVAL + random.randint(0, RANDOMCHANCE + 1))

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
