# Hamshield
# Example: Serial Transceiver
# SerialTransceiver is TTL Serial port "glue" to allow
# desktop or laptop control of the HamShield.
#
# Connect the Hamshield to your Arduino. Screw the Antenna
# into the HamSHield RF jack. Plug a pair of headphones into
# the HamShield. COnnect the Arduino to wall power and then
# to your computer via USB. After uploading this program to
# your Arduino, open the Serial Monitor. Press the button on
# the HamShield to begin setup. After setup is complete, open
# the Serial Monitor. Use the bar at the top of the serial
# monitor to enter commands as seen below.
#
# EXAMPLE: to change the repeater offset to 144.425MHz,
# enable offset, then key in, use the following commands:
# T144425
# R1
# [Just a space]
#
#
#
# Commands:
#
# Mode          ASCII       Description
# ------------- ----------- ----------------------------------------------------------------------------------------------
# Transmit      space       Space must be received at least every 500 ms
# Receive       no space    If space is not received and/or 500 ms timeout of space occurs, unit will go into receive mode
# Bandwith      E<mode>;    for 12.5KHz mode is 0, for 25KHz, mode is 1
# Frequency     F<freq>;    Set the receive frequency in KHz, if offset is disabled, this is the transmit frequency
# Morse Out     M<text>;    A small buffer for morse code (32 chars)
# Power Level   P<level>;   Set the power amp level, 0 = lowest, 15 = highest
# Enable Offset R<state>    1 turns on repeater offset mode, 0 turns off repeater offset mode
# Squelch       S<level>;   Set the squelch level
# TX Offset     T<freq>;    The absolute frequency of the repeater offset to transmit on in KHz
# RSSI          ?;          Respond with the current receive level in - dBm (no sign provided on numerical response)
# Voice Level   ^;          Respond with the current voice level (VSSI)
#
#
# Responses:
#
# Condition     ASCII       Description
# ------------- ----------- ---------------------------------------------------------------
# Startup       *<code>;    Startup and shield connection status
# Success       !;          Generic success message for command that returns no value
# Error         X<code>     Indicates an eror code. The numerical value is the type of error
# Value         :<value>;   In response to a query
# Status        #<value>;   Unsolicited status message
# Debug Msg     @<text>;    32 character debug message
#
#
#
#
#
# This code is based very strongly off of the SerialTransceiver example
# for Arduino. Only minor modifications have been made to
# allow it to work in Python for Raspberry Pi
#
# Connect the HamShield to your Raspberry Pi. Screw the antenna
# into the HamShield RF jack.
# Run this program with:
#     python SerialTransceiver.py
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
    freq = 144390
    radio.frequency(freq)

    radio.setVolume1(0xF)
    radio.setVolume2(0xF)
    radio.setModeReceive()
    radio.setTxSourceMic()
    radio.setRfPower(0)
    radio.setSQLoThresh(80)
    radio.setSqOn()


##########################################
# repeating loop

def loop():
    timer = 0
    cmdbuff = [None]*32
    repeater = 0
    ctcssin = 0
    cdcssin = 0
    cdcssout = 0

    if inputAvailable():
        text = inputReadChar()

        if state == 10:
            if text == 32:
                timer = wiringpi.millis()
                return
        elif state == 0:

            if text == 32: # space - transmit
                if repeater == 1:
                    radio.frequency(tx)
                    radio.setModeTransmit()
                    state = 10
                    print("#TX, ON;")
                    timer = wiringpi.millis()
                    return

            elif text == 63: # ? - RSSI
                print(":")
                print(radio.readRSSI(), DEC)
                print(";")
                return

            elif text == 65: # A - CTCSS In
                getValue()
                ctcssin =float(cmdbuff)
                radio.setCtcss(ctcssin)
                return

            elif text == 66: # B - CTCSS Out
                return

            elif text == 67: # C - CTCSS Enable
                return

            elif text == 68: # D - CTCSS Enable
                return

            elif text == 70: # F - frequency
                getValue()
                freq = float(cmdbuff)
                if radio.frequency(freq): #todo in original this was == True, not sure if same
                    print("@")
                    print(freq, DEC)
                    print(";!;")
                else:
                    print("X1;")
                return

            elif text == 'M':
                getValue()
                radio.setModeTransmit()
                wiringpi.delay(300)
                radio.morseOut(cmdbuff)
                state = 10
                return

            elif text == 80: # P - power level
                getValue()
                temp = float(cmdbuff)
                radio.setRfPower(temp)
                return

            elif text == 82: # R - repeater offset mode
                getValue()
                temp = float(cmdbuff)
                if temp == 0:
                    repeater = 0
                if temp == 1:
                    repeater = 1
                return

            elif state == 83: # S - squelch
                getValue()
                temp = float(cmdbuff)
                radio.setSQLoThresh(temp)
                return

            elif state == 84: # T - transmit offset
                getValue()
                tx = float(cmdbuff)
                return

            elif state == 94: # ^ - VSSI (voice) level
                print(":")
                print(radio.readVSSI(), DEC)
                print(";")
            else:
                return

    if state == 10:
        if wiringpi.millis() > (timer + 500):
            print("#TX,OFF;")
            radio.setModeReceive()
            if repeater == 1:
                radio.frequency(freq)
                state = 0
                txcount = 0


def getValue():
    p = 0
    if inputAvailable():
        temp = inputReadChar()
        if temp == 59:
            cmdbuff[p] = 0
            print("@")
            for i in range(32):
                print(cdmbuff[i])
                print()
            return
        cmdbuff[p] = temp
        p++
        if p == 32:
            print("@")
            for i in range(32):
                print(cmdbuff[i])
            cmdbuff[0] = 0
        print("X0;")
        # some sort of alignment issue? lets not feed junk into whatever takes this string in

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
            radio.setModeRecieve()  # just in case we had an Exception while in TX, don't get stuck there
            wiringpi.delay(25)
            if HAMSHIELD_RST:
                wiringpi.digitalWrite(RESET_PIN, wiringpi.LOW)
                wiringpi.delay(25)
            break