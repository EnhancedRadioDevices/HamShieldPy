# Hamshield
# Example: CTCSS

# This is a simple example to demonstrate HamShield receive and trasmit
# and transmit functionality using CTCSS. THe HamShield will have audio
# output muted until it receives the correct sub-audible tone. It does
# this by polling a tone detection flag on the HamShield, but it's
# possible ot do this using interrupts if you onnect GPIOO from the
# Hamshield to your Arduino (code for that not provided).
#
# This code is based very strongly off of the HamShield examples
# for Arduino. Only minor modifications have been made to
# allow it to work in Python for Raspberry Pi

# Connect the HamShield to your Raspberry Pi. Screw the antenna
# into the HamShield RF jack. Plug a pair of headphones into the
# hamshield. Connect the HamShield to wall power and then to your
# computer via USB. Set the CTCSS tone that you want to use in the
# setup() function below.
#
# Run this program with:
#     python CTCSS.py
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

HAMSHIELD_RST = False
RSSI_REPORT_RATE_MS = 5000
muted = False

nCS = 0
clk = 3
dat = 2
mic = 1
# create object for radio
radio = HamShield(nCS, clk, dat, mic)
rx_dtmf_buf = ''
currently_tx = False
rssi_timeout = 0


#########################################

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

def inputPeek():
    global inputBuffer, bufferLock
    c = ''
    bufferLock.acquire()
    if len(inputBuffer) > 0:
        c = inputBuffer[0]
    bufferLock.release()
    return c

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


#########################################
# setup

def setup():
    global currently_tx, muted

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

    #set frequency
    print("changing frequency")
    radio.setSQOff()
    freq = 432100
    radio.frequency(freq)

    # set to receive
    radio.setModeReceive
    currently_tx = False
    print("config register is: ")
    print(radio.readCtlReg())
    print(radio.readRSSI())

    radio.setRfPower(0)

    # CTCSS Setup code
    ctcss_tone = 131.8
    radio.setCtcss(ctcss_tone)
    radio.enableCtcss()
    print("ctcss tone: ")
    print(radio.getCtcssFreqHz())
    # mute audio until we get a CTCSS tone
    radio.setMute()
    muted = True


#########################################
# repeating loop

def loop():
    global muted, currently_tx, rssi_timeout

    # handle CTCSS tone detection
    if not currently_tx:
        # check for CTCSS tone
        if radio.getCtcssToneDetected():
            if muted:
                muted = False
                radio.setUnmute()
                print("tone")
            elif not muted:
                muted = True
                radio.setMute()
                print("no tone")

    # handle serial commands
    if inputAvailable():
        if inputPeek() == 't' or inputPeek() == 'T':
            c = inputReadChar()
            if c == 't':
                radio.setModeReceive()
                currently_tx = False
                print('RX')
            elif c == 'T':
                radio.setModeTransmit()
                currently_tx = True
                print('TX')
        freq = inputParseInt()
        inputFlush()
        if freq != 0:
            radio.frequency(freq)
            print("set frequency: " + str(freq))

    if (not currently_tx and (wiringpi.millis() - rssi_timeout) > RSSI_REPORT_RATE_MS):
        print(radio.readRSSI())
        rssi_timeout = wiringpi.millis()




#########################################
# main and safeExit

def safeExit(signum, frame):
    radio.setModeReceive()
    wiringpi.delay(25)
    sys.exit(1)


if __name__ == '__main__':

    wiringpi.wiringPiSetupGpio()

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
            break
