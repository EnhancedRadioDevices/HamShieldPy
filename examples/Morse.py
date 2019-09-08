# Hamshield
# Example: Morse Code Transceiver
#
# Serial to Morse transceiver. Sends characters from the Serial
# port over the air, and vice versa.
#
# Note: Only upper case letters, numbers, and a few symbols
# are supported.
# Supported symbols: &/+(=:?";@`-._),!$
#
# If you're having trouble accurately deconding, you may want to
# tweak the min/max . and - times. You can also uncomment
# the print debug statements that can tell you when tones
# are being detected, how long they're detected for, and whether
# the tones are decoded as a . or -.
#
# This code is based very strongly off of the HandyTalkie example
# for Arduino. Only minor modifications have been made to
# allow it to work in Python for Raspberry Pi
#
# Connect the HamShield to your Raspberry Pi. Screw the antenna
# into the HamShield RF jack.
# Run this program with:
#     python Morse.py
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

currently_tx = False
rssi_timeout = 0

MORSE_FREQ = 600
MORSE_DOT = 150 # ms
# Note that all timing is defined in terms of MORSE_DOT relative durations
# You may wantto tweak those timings below

SYMBOL_END_TIME = 5 # ms
CHAR_END_TIME = MORSE_DOT*2.7
MESSAGE_END_TIME = MORSE_DOT*8

MIN_DOT_TIME = MORSE_DOT*0.7
MAX_DOT_TIME = MORSE_DOT*1.3
MIN_DASH_TIME = MORSE_DOT*2.7
MAX_DASH_TIME = MORSE_DOT*3.3

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


def inputPeek():
    global inputBuffer, bufferLock
    c = ''
    bufferLock.acquire()
    if len(inputBuffer) > 0:
        c = inputBuffer[0]
    bufferLock.release()
    return c


def inputParseInt():
    global inputBuffer, bufferLock
    c = ''
    bufferLock.acquire()
    for char in inputBuffer:
        if char.isdigit():
            c += char
        else:
            break
    bufferLock.release()
    if len(c) > 0:
        return int(c)
    else:
        return 0


#################################
# setup

RSSI_REPORT_RATE_MS = 5000
tone_in_progress = 0
rx_morse_bit = 0
rx_morse_char = 0


def setup():
    global rx_morse_bit, rx_morse_char, space_in_progress, tone_in_progress

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

    print("setting Radio configuration")

    radio.setRfPower(0)

    # Set the morse code characteristics
    radio.setMorseFreq(MORSE_FREQ)
    radio.setMorseDotMillis(MORSE_DOT)

    radio.lookForTone(MORSE_FREQ)

    # Configure the HamShield to operate on 438.000MHz
    radio.frequency(432100)
    radio.setModeReceive()
    print("Radio configured")
    last_tone_check = wiringpi.millis()
    space_in_progress = 0
    tone_in_progress = 0
    rx_morse_bit = 1
    bits_to_process = False

    radio.bypassPreDeEmph()



##########################################
# repeating loop

def loop():
    rx_char = radio.morseRxLoop()
    if (rx_char != '\0'):
        print(rx_char)

    # should we send anything
    if inputAvailable():
        print("checking channel")
        # We'll wait up to 30 seconds for a clear channel,
        # requiring that the channel is clear for 2 seconds before we transmit
        if radio.waitForChannel(30000, 2000, -5):
            # If we get here, the channel is clear.

            # Start transmitting by putting the radio into transmit mode.
            radio.setModeTransmit()
            MORSE_BUF_SIZE = 128
            morse_buf = " " # start with space to let PA come up
            while inputAvailable() and len(morse_buf) < MORSE_BUF_SIZE:
                morse_buf = morse_buf + inputReadChar()
            morse_buf = morse_buf + '\0'

            # Send a message out in morse code
            radio.morseOut(morse_buf)

            # We're done sending the message, set the radio back into recieve mode.
            radio.setModeReceive()
            radio.lookForTone(MORSE_FREQ)
            print("sent")
        else:
            # If we get here, the channel is busy. Let's also print out the RSSI.
            print("The channel was busy. RSSI: ")
            print(radio.readRSSI())

def handleTone(tone_time):
    #print(tone_time)
    if tone_time > MIN_DOT_TIME and tone_time < MAX_DOT_TIME:
        # add a dot
        #print(".")
        bits_to_process = True
        # nothing to do for this bit position, since . = 0
    if tone_time > MIN_DASH_TIME and tone_time < MAX_DASH_TIME:
        # add a dash
        # print("-")
        bits_to_process = True
        rx_morse_char += rx_morse_bit

    #prep for the next bit
    rx_morse_bit = rx_morse_bit <<1

def parseMorse():
    # if morse_char is a valid morse character, return the character
    # if morse_char is an invalid (incomplete) morse character, return 0

    # if (rx_morse_bit != 1) print(rx_morse_char, BIN)
    rx_morse_char += rx_morse_bit #add the terminator bit
    # if we got a char, then print it
    c = radio.morseReverseLookup(rx_morse_char)
    rx_morse_char = 0
    rx_morse_bit = 1
    return c

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
