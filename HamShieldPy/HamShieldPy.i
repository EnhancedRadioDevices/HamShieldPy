%module HamShieldPy

%{
#include "HamShield.h"
%}

%include "HamShield.h"

/* uintXX_t mapping: Python -> C */
%typemap(in) uint8_t {
	$1 = (uint8_t) PyInt_AsLong($input);
}
%typemap(in) uint16_t {
	$1 = (uint16_t) PyInt_AsLong($input);
}
%typemap(in) uint32_t {
	$1 = (uint32_t) PyInt_AsLong($input);
}

/* uintXX_t mapping: C -> Python */
%typemap(out) uint8_t {
	$result = PyInt_FromLong((long) $1);
}
%typemap(out) uint16_t {
	$result = PyInt_FromLong((long) $1);
}
%typemap(out) uint32_t {
	$result = PyInt_FromLong((long) $1);
}
