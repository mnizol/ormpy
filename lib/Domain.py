##############################################################################
# Package: ormpy
# File:    Domain.py
# Author:  Matthew Nizol
##############################################################################

""" The Domain.py module implements the domains that underly value types. """

import sys

from lib.Constraint import ValueConstraint

class Domain(object):
    """ A domain, which is essentially a data type that permits you to 
        enumerate the valid values via a call to the next() function. """
    
    def __init__(self, constraint=None):
        """ Initialize the domain. """
        self._constraint, self.size = self._parse_constraint(constraint)
 
        # Start at last value so first call to next() returns first value
        self._range_index = len(self._constraint.ranges) - 1
        self._value = self._range.max_value # A value from the domain  
     
    def _parse_constraint(self, constraint):
        """ Return a tuple containing the parsed value constraint
            for the domain and the size of the domain. """
        raise NotImplementedError()

    def next(self):
        """ Returns next element from the domain, respecting any value
            constraints.  If there is no next element, returns first 
            element from the domain. """
        raise NotImplementedError()

    @property
    def _range(self):
        """ Returns the current value range. """
        return self._constraint.ranges[self._range_index]

    def _next_range(self):
        """ Increment index to point to next range. """
        self._range_index = self._range_index + 1
        if self._range_index >= len(self._constraint.ranges):
            self._range_index = 0

    def _next_min(self):
        """ Increment to next range and return min value. """
        self._next_range()            
        self._value = self._range.min_value
        return self._value

class NumericDomain(Domain):
    """ A numeric domain. By default, acts an integer domain, but can 
        be inherited by other types (e.g. float) to create other domains. """
    
    def __init__(self, constraint=None, precision=0, cast=int):
        """ Initialize. """
        self._add = cast(1) / 10**precision # Add to _value to get next value
        self._cast = cast # Intended data type, e.g. int, float
        self._precision = precision # Number of decimal places for rounding

        if constraint is None:
            constraint = ValueConstraint()
            constraint.add_range(0, sys.maxsize)

        super(NumericDomain, self).__init__(constraint=constraint)

    
    def _parse_constraint(self, constraint):
        """ Return a tuple containing the parsed value constraint
            for the domain and the size of the domain. """
        
        parsed = ValueConstraint()
        size = 0

        for rng in constraint.ranges:
            try:
                min_value = rng.min_value + (rng.min_open * self._add)
                max_value = rng.max_value - (rng.max_open * self._add)
                min_value = self._cast(min_value)
                max_value = self._cast(max_value)
            except TypeError: # Ignore this range
                continue
    
            if min_value > max_value: # Ignore this range
                continue

            parsed.add_range(min_value, max_value)
            size += round((max_value - min_value + 1) / self._add)

        return parsed, size 

    def next(self):
        """ Returns next element from the domain, respecting any value
            constraints.  If there is no next element, returns first 
            element from the domain. """
        self._value = round(self._value + self._add, self._precision)
        self._value = self._cast(self._value)
        limit = self._cast(round(self._range.max_value, self._precision))
        
        if self._value > limit:
            return self._next_min()
        else:
            return self._value

class FloatDomain(NumericDomain):
    """ A domain for floating point numbers.  Only generates numbers
        in increments of 0.1, so the size of the domain is limited to
        0 to sys.maxsize * 10. """

    def __init__(self, constraint=None):
        """ Initialize. """
        super(FloatDomain, self).__init__(constraint=constraint, 
            precision=1, cast=float)
    
class BoolDomain(Domain):
    """ A domain for boolean (True/False) values. """

    def __init__(self, constraint=None):
        """ Initialize. """
        if constraint is None:
            constraint = ValueConstraint()
            constraint.add_range(False, True)

        super(BoolDomain, self).__init__(constraint=constraint)

    def _parse_constraint(self, constraint):
        """ Return a tuple containing the parsed value constraint
            for the domain and the size of the domain. """
        
        hastrue = False
        hasfalse = False

        for rng in constraint.ranges:
            if bool(rng.min_value) or bool(rng.max_value):
                hastrue = True
            if not(bool(rng.min_value) and bool(rng.max_value)):
                hasfalse = True

        parsed = ValueConstraint()
        parsed.add_range(not(hasfalse), hastrue)

        return parsed, hastrue + hasfalse 

    def next(self):
        """ Returns next element from the domain, respecting any value
            constraints.  If there is no next element, returns first 
            element from the domain. """
        if self._value == self._range.min_value:
            self._value = self._range.max_value
        else:
            self._value = self._range.min_value

        return self._value

    
