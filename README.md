

# Overview

Raspberry Pi Software Library for HamShield. This library implements all of the basic functionality.

The library works by including the Arduino HamShield library as a git submodule, and then compiling Python bindings for it using SWIG. Whenever you rebuild HamShieldPy (after doing a git pull), you should have all of the most recent updates to the Arduino library as well.

Note that AFSK, APRS, and KISS for the Arduino depend upon some AVR specific timers. We're working on updating that functionality so that you can use it with your Raspberry Pi as well, but that's not done yet (ETA is TBD).

This software is released under the MIT license. See the accompanying
LICENSE.txt for more details.

# Pre-Requisites

* wiringPi
    http://wiringpi.com/
* wiringPi python
    pip install wiringpi2
* SWIG (this should be installed with your default Raspbian image)

# Setup


On your Raspberry Pi, run the following after connecting it to the internet:

    mkdir ~/src
    cd ~/src
    git clone https://github.com/EnhancedRadioDevices/HamShieldPy.git
    git submodule update --init
    cd HamShieldPy
    sudo python setup.py install

# Examples

At the moment we just have the DTMF example. We'll be slowly porting more examples over the next few months.

You can find all the examples in the Examples directory. They all assume that you're using a HamShieldMini, which doesn't require a reset pin to control it. 

# Default pinout for HamShield Mini

    HamShieldMini <-> Raspberry Pi
    Vin               pin 1 (3.3V)
    GND               pin 6 (GND)
    nCS               pin 11(wiringPi0)
    DAT               pin 13(wiringPi2)
    CLK               pin 15(wiringPi3)
    MIC               pin 12(wiringPi1, PWM0)
    
If you're using a HamShield, you'll also want to connect the HamShield's reset line. The examples all have some commented out code in the setup function that will bring the HamShield out of reset.

    RST               pin 29(wiringPi21)
