
# Hamshield
# Example: DTMF
# This is a simple example to demonstrate how to use DTMF.
#
# This code is based very strongly off of the DTMF example
# for Arduino. Only minor modifications have been made to 
# allow it to work in Python for Raspberry Pi
#
# Connect the HamShield to your Raspberry Pi. Screw the antenna 
# into the HamShield RF jack. 
# Run this program with:
#     python DTMF.py
# 
# The program will set up the HamShield. After setup is complete, 
# type in a DTMF value (0-9, A, B, C, D, *, #) and hit enter.
# The corresponding DTMF tones will be transmitted. The sketch
# will also print any received DTMF tones to the screen.
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


###############################################
# sketch functions


def char2code(c):
    if (c == '#'):
        code = 0xF
    elif (c=='*'):
        code = 0xE
    elif (c >= '0' and c <= 'D'):
        code = int(c, 16) 
    else:
        # invalid code, skip it
        code = 255
    return code

codes = ['0', '1','2','3','4','5','6','7','8','9','A', 'B','C','D','*','#']
def code2char(code):
    if (code < len(codes)):
        c = codes[code]
    else:
        c = '?' # invalid code
    return c

    
###############################################
# StdinParser thanks to Kenkron
#             https://github.com/Kenkron
#creates an input buffer for stdin
bufferLock=threading.Lock()
inputBuffer=''

class StdinParser(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
    def run(self):
        global inputBuffer
        running = True
        while running:
            try:
                instruction=raw_input()
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
    if len(inputBuffer)>0:
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

    

                
###############################################
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
        wiringpi.delay(5) # wait for device to come up
      
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
    #radio.setSQOff()

    print("setting frequency to: ")
    freq = 432100
    radio.frequency(freq)
    print(str(radio.getFrequency()) + "kHz")
      
    # set RX volume to minimum to reduce false positives on DTMF rx
    radio.setVolume1(6)
    radio.setVolume2(0)
      
    # set to receive
    radio.setModeReceive()
      
    radio.setRfPower(0)

    # set up DTMF
    radio.enableDTMFReceive()
      
    # DTMF timing settings are optional.
    # These times are set to default values when the device is started.
    # You may want to change them if you're DTMF receiver isn't detecting
    # codes from the HamShield (or vice versa).
    radio.setDTMFDetectTime(24) # time to detect a DTMF code, units are 2.5ms
    radio.setDTMFIdleTime(50) # time between transmitted DTMF codes, units are 2.5ms
    radio.setDTMFTxTime(60) # duration of transmitted DTMF codes, units are 2.5ms

    print("ready")

###############################################
# repeating loop

def loop():
    global rx_dtmf_buf
    # look for tone
    if (radio.getDTMFSample() != 0):
        code = radio.getDTMFCode()

        rx_dtmf_buf += code2char(code)
        
        # reset after this tone
        j = 0
        while (j < 4):
            if (radio.getDTMFSample() == 0):
                j += 1
            wiringpi.delay(10)
    elif (len(rx_dtmf_buf) > 0):
        print(rx_dtmf_buf)
        rx_dtmf_buf = ''
  
    # Is it time to send tone?
    if (inputAvailable()):
        code = char2code(inputReadChar())
    
        # start transmitting
        radio.setDTMFCode(code) # set first
        radio.setTxSourceTones()
        radio.setModeTransmit()
        wiringpi.delay(300) # wait for TX to come to full power

        dtmf_to_tx = True
        while (dtmf_to_tx):
            # wait until ready
            while (radio.getDTMFTxActive() != 1):
                # wait until we're ready for a new code
                wiringpi.delay(10)
            while (radio.getDTMFTxActive() != 0):
                # wait until this code is done
                wiringpi.delay(10)

            if (inputAvailable()):
                code = char2code(inputReadChar())
                if (code == 255): code = 0xE # throw a * in there so we don't break things with an invalid code
                radio.setDTMFCode(code) # set first
            else:
                dtmf_to_tx = False
        # done with tone
        radio.setModeReceive()
        radio.setTxSourceMic()


###############################################
# main and safeExit

def safeExit(signum, frame):
    global HAMSHIELD_RST
    radio.setModeReceive()
    wiringpi.delay(25)
    if HAMSHIELD_RST:
        wiringpi.digitalWrite(RESET_PIN, wiringpi.LOW)
        wiringpi.delay(25)
    sys.exit(1)

if __name__ == '__main__':   
    wiringpi.wiringPiSetup()
 
    inputThread=StdinParser()
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
