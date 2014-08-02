##############################################################################
# Package: ormpy
# File:    Model.py
# Author:  Matthew Nizol
##############################################################################

""" This module provides a :class:`Model` class to store a simplified ORM model 
    consisting of a set of object types, a set of fact types, and a set of 
    constraints.  
"""

from lib.ObjectType import ObjectType
from lib.FactType import FactType
from lib.Constraint import Constraint

class Model(object):
    """ Simplified representation of an ORM model. """

    def __init__(self):
        self._object_types = {}
        self._fact_types = {}
        self._constraints = {}

    def add(self, element):
        """ Add an element to the model. """
        if isinstance(element, ObjectType):
            self._object_types[element.name] = element
        elif isinstance(element, FactType):
            self._fact_types[element.name] = element
        elif isinstance(element, Constraint):
            self._constraints[element.name] = element

    def get_object_type(self, name):
        """ Returns an object type with a given *name* """
        try:
            return self._object_types[name]
        except KeyError:
            return None 

    def get_fact_type(self, name):
        """ Returns a fact type with a given *name* """
        try:
            return self._fact_types[name]
        except KeyError:
            return None 

    def get_constraint(self, name):
        """ Returns a constraint with a given *name* """
        try:
            return self._constraints[name]
        except KeyError:
            return None           

    def num_object_types(self):
        """ Returns the number of object types in the model. """
        return len(self._object_types)

    def num_fact_types(self):
        """ Returns the number of fact types in the model. """
        return len(self._fact_types)

    def num_constraints(self):
        """ Returns the number of constraints in the model. """
        return len(self._constraints)

    def display(self):
        """ Prints the model to stdout. """
        print "Object Types: "
        for obj in self._object_types.itervalues():
            print " "*4, obj.display_string()


