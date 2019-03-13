# Hamshield
# Example: HandyTalkie
# This is a simple example to demonstrate HamShield receive
# and transmit functionality.
# Connect the Hamshield to your Arduino. Screw the Antenna
# into the HamShield RF jack. Plug a pair of headphones into
# the HamShield. Connect the Arduino to wall power and then
# to your computer via USB. After uploading this program to
# your Arduino, open the Serial Monitor. Press the button on
# the HamShield to begin setup. After setup is complete, type
# your desired Tx/Rx frequency, in hertz, into the bar at the
# top of the Serial Monitor and click the "Send" button.
# To test with another HandyTalkie (HT), key up on your HT
# and make sure you can hear it through the headphones
# attached to the HamShield. Key up on the HamShield by
# holding the button.
#
# This code is based very strongly off of the HandyTalkie example
# for Arduino. Only minor modifications have been made to
# allow it to work in Python for Raspberry Pi
#
# Connect the HamShield to your Raspberry Pi. Screw the antenna
# into the HamShield RF jack.
# Run this program with:
#     python HandieTalkie.py
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
    if len(inputBuffer)>0:
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
        # if you're using a standard HamShield (not a Mini)
        # you have to let it out of reset
        wiringpi.digitalWrite(RESET_PIN, wiringpi.HIGH)
        wiringpi.delay(5) # wait for device to come up

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
    currently_tx = False
    print("config register is: ")
    print(radio.readCtlReg())
    print(radio.readRSSI())


    """
    set to transmit
    
    radio.setModeTransmit()
    maybe set PA bias voltage
    print("configured for transmit")
    radio.setTxSourceMic()
    """

    radio.setRfPower(0)

    print("ready")

    rssi_timeout = 0;

##########################################
# repeating loop

def loop():
    global rssi_timeout, currently_tx

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
            radio.setModeRecieve() # just in case we had an Exception while in TX, don't get stuck there
            wiringpi.delay(25)
            if HAMSHIELD_RST:
                wiringpi.digitalWrite(RESET_PIN, wiringpi.LOW)
                wiringpi.delay(25)
            break
