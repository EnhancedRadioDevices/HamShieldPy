

CLIB := HamShieldPy/clib/src/
PYLIB := HamShieldPy/

INCLUDES := -I$(CLIB)

all:
	swig -python -c++ -o _HamShieldPy_module.cc $(INCLUDES) $(PYLIB)HamShieldPy.i 
	python setup.py install
