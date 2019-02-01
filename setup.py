# setup.py
from setuptools import setup

#from distutils.core import setup, Extension
from distutils.core import Extension

extension_mod = Extension("_HamShieldPy", ["_HamShieldPy_module.cc", "HamShieldPy/clib/src/HamShield.cpp", "HamShieldPy/HamShield_pi_comms.cpp"])

#TODO: may want to run make from here

setup(name="HamShieldPy",
      version="0.0",
      description="Raspberry Pi HamShield library",
      url="https://github.com/EnhancedRadioDevices/HamShieldPy",
      author="Morgan Redfield",
      author_email="morgan@enhancedradio.com",
      packages=["HamShieldPy"],
      ext_modules=[extension_mod]
      scripts=[]
      )
