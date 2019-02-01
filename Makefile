

CLIB := HamShieldPy/clib/src/
PYLIB := HamShieldPy/

INCLUDES := -I$(CLIB)

all:
    swig -python -c++ -o $(CLIB)/HamShield.cpp $(PYLIB)/HamShield_pi_comms.cpp HamShieldPy.i $(INCLUDES) -lwiringPi -lpthread
    python setup.py install