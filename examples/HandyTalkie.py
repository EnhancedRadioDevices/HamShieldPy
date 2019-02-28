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

from HamShieldPy import HamShield
import wiringpi
import threading

nCS = 0
clk = 3
dat = 2
mic = 1
# create object for radio
radio = HamShield(nCS, clk, dat, mic)
rx_dtmf_buf = ''


# sketch functions


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
            c = char
            break
    bufferLock.release()
    return c

# setup

LED_PIN = 13
RSSI_REPORT_RATE_MS = 5000

PWM_PIN = A3
REST_PIN = 2
SWITCH_PIN = 2


def setup():
    print("type any character and press enter to begin...")

    while (not inputAvailable()):
        pass
    inputFlush()

    # if you're using a standard HamShield (not a Mini)
    # you have to let it out of reset
    # RESET_PIN = 21
    # wiringpi.pinMode(RESET_PIN, OUTPUT)
    # wiringpi.digitalWrite(RESET_PIN, HIGH)
    # wiringpi.delay(5) # wait for device to come up

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
    radio.dangerMode()

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

    #todo LED_PIN? is this commented out or defined elswhere
    #configure Arduino LED for
    #wiringpi.pinMode(LED_PIN, OUTPUT);
    #rssi_timeout = 0;

# repeating loop

def loop():

    if not wiringpi.digitalRead(SWITCH_PIN): #todo is switch pin defined?
        if not currently_tx:
            currently_tx = True

            #set to transmit
            radio.setModeTransmit()
            print("Tx")
            #radio.setTxSourceMic()
            #radio.setRfPower(1)
        elif currently_tx:
            radio.setModeReceive()
            currently_tx = False
            print("Rx")
    if inputAvailable():
        #todo note wrote peek myself
        if inputPeek() == 'r':
            inputReadChar()
            wiringpi.digitalWrite(RESET_PIN, LOW) #todo pins?
            wiringpi.delay(1000)
            wiringpi.digitalWrite(RESET_PIN, HIGH)
            radio.initialize() # initializes automatically for UHF 12.5kHz channel
        else:
            setTimeout(40) #todo not sure how to do timeout
            freq = inputParseInt() #todo note wrote myself
            inputFlush()
            radio.frequency(freq)
            print("set frequency: ")
            print(freq)


    if (not currently_tx and (time() - rssi_timout) > RSSI_REPORT_RATE_MS):
        print(radio.readRSSI())
        rssi_timeout = time()



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
            inputThread.join()
            break
