##############################################################################
# Package: ormpy
# File:    ObjectType.py
# Author:  Matthew Nizol
##############################################################################

""" ObjectType.py provides classes for the various object types in ORM:
entity type, value type, and objectified type.
"""

from lib.ModelElement import ModelElementSet, ModelElement

class ObjectTypeSet(ModelElementSet):
    """ Container for a set of object types. """

    def __init__(self):
        super(ObjectTypeSet, self).__init__(name="Object Types")


class ObjectType(ModelElement):
    """ Abstract class inherited by all object types. """

    def __init__(self, uid=None, name=None):
        super(ObjectType, self).__init__(uid=uid, name=name)
        self.independent = False #: True for independent object types
        self.implicit = False    #: True for implicit object types

    #@property
    #def fullname(self):
    #    return "ObjectTypes." + self.name

class EntityType(ObjectType):
    """ An entity type is an object type that requires identification. """

    def __init__(self, uid=None, name=None):
        super(EntityType, self).__init__(uid=uid, name=name)

        #: Reference to the uniqueness constraint that provides the preferred
        #: identification scheme for this entity type.
        self.identifying_constraint = None

class ValueType(ObjectType):
    """ A value type is a self-identifying object type. """

    def __init__(self, uid=None, name=None):
        super(ValueType, self).__init__(uid=uid, name=name)

        #: Python data type (mapped from the conceptual data type selected
        #: by the modeler)
        self.data_type = None
        self.data_type_scale = None  #: Scale facet for data_type
        self.data_type_length = None #: Length facet for data_type

class ObjectifiedType(ObjectType):
    """ An objectified type is an object type that objectifies a fact type. """

    def __init__(self, uid=None, name=None):
        super(ObjectifiedType, self).__init__(uid=uid, name=name)

        #: Reference to the uniqueness constraint that provides the preferred
        #: identification scheme for this object type.
        self.identifying_constraint = None

        #: Reference to the fact type that this object type objectifies.
        self.nested_fact_type = None



