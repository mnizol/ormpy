##############################################################################
# Package: ormpy
# File:    ObjectType.py
# Author:  Matthew Nizol
##############################################################################

""" This module provides classes for the various object types in ORM: 
entity type, value type, and objectified type.  
"""

class ObjectType(object):
    """ Abstract class inherited by all object types. """

    def __init__(self):
        self._id = ""
        self.name = ""
        self.independent = False
        
    def display_string(self):
        """ String containing object type information. """
        return self.name

class EntityType(ObjectType):
    """ An entity type is an object type that requires identification. """

    def __init__(self):
        ObjectType.__init__(self)
        self.identifier = None

class ValueType(ObjectType):
    """ A value type is a self-identifying object type. """

    def __init__(self):
        ObjectType.__init__(self)
        self.data_type = None

class ObjectifiedType(ObjectType):
    """ An objectified type is an object type that objectifies a fact type. """

    def __init__(self):
        ObjectType.__init__(self)
        self.identifier = None
        self.nested_fact_type = None


    
