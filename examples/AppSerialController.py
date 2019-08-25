# Hamshield
# Example: SerialController
# This application is used in conjunction with a computer to provide full serial controll of HamShield.
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

    radio.setRfPower(0)
    radio.frequency(146520)
    radio.setModeReceive()


##########################################


def tx_on():
    radio.setModeTransmit()
    print("Transmitting")

def tx_off():
    radio.setModeReceive()
    print("Transmit off")

def pl_tone_tx():
    print("TX PL tone")
    while True:
        if inputAvailable():
            input = inputReadChar()
            if input == 'X':
                return
            elif input == '!':
                program_pl_tx()
                return
            #else get the next character

def program_pl_tx():
    print("programming TX PL to ")
    pl_tx_str = ''
    input = inputReadChar()
    while inputAvailable() and input.isdigit():
        pl_tx_str +=input
        input = inputReadChar()
    pl_tx = float(pl_tx_str)
    print(pl_tx, DEC)
    radio.setCtcss(pl_tx)

def pl_tone_rx():
    print("RX PL tone")
    while True:
        if inputAvailable():
            input = inputReadChar()
            if input == 'X':
                return
            elif input == '!':
                program_pl_rx()
                return

def program_pl_rx():
    print("programming RX PL to ")
    pl_rx_str = ''
    input = inputReadChar()
    while inputAvailable() and input.isdigit():
        pl_rx_str +=input
        input = inputReadChar()
    pl_rx = float(pl_rx_str)
    print("pl_rx", DEC)
    radio.setCtcss(pl_rx)

def tune_freq():
    print("program frequency mode")
    while True:
        if inputAvailable():
            input = inputReadChar()
            if input == 'X':
                return
            elif input == '!':
                program_frequency()
                return
            elif input == '.':
                continue
            else:
                return

def program_frequency():

    print("programming frequency to ")
    freq_str = ''
    input = inputReadChar()
    while inputAvailable() and input.isdigit():
        freq_str +=input
        input = inputReadChar()
    freq = float(freq_str)
    print(freq_str, DEC)
    radio.frequency(freq)

def amplifier():
    while True:
        if inputAvailable():
            input = inputReadChar()
            if input == 'X':
                return
            elif input != '!':
                radio.setRfPower(input)
                return
            elif input == '!':
                return

def predeemph():
    pass

# repeating loop

def loop():

    if inputAvailable():
        input = inputPeek()
        if input == 'X': # absorb reset command because we are already reset
            return
        elif input == 'F': #frequency configuration command
            tune_freq()
            return
        elif input == 'P': # TX PL Tone configuration command
            pl_tone_tx()
            return
        elif input == 'R': # RX PL Tone configuration command
            pl_tone_rx()
            return
        elif input == 'T': # Turn on transmitter command
            tx_on()
            return
        elif input == 'O': # Turn off transmitter command
            tx_off()
            return
        elif input == 'A': # configure amplifier
            amplifier()
            return
        elif input == 'D': # configure predeemph
            preemph()
            return
        else:
            return





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