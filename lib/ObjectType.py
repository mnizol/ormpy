##############################################################################
# Package: ormpy
# File:    ObjectType.py
# Author:  Matthew Nizol
##############################################################################

""" ObjectType.py provides classes for the various object types in ORM:
entity type, value type, and objectified type.
"""

from lib.ModelElement import ModelElementSet, ModelElement
from lib.Domain import StringDomain

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
        self.roles = [] #: Roles played by this object type

        # Prefix for domain values     
        prefix = name or '' # Empty string if name is None
        if prefix and prefix[-1].isdigit(): 
            prefix += "_"
        
        #: The domain for the object type, which defaults to a 
        #: :class:`lib.Domain.StringDomain` prefixed by the type's name.
        self.domain = StringDomain(prefix=prefix) 

    @property
    def fullname(self):
        """ Returns name that is unique within the model. """
        return "ObjectTypes." + self.name

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

class ObjectifiedType(ObjectType):
    """ An objectified type is an object type that objectifies a fact type. """

    def __init__(self, uid=None, name=None):
        super(ObjectifiedType, self).__init__(uid=uid, name=name)

        #: Reference to the uniqueness constraint that provides the preferred
        #: identification scheme for this object type.
        self.identifying_constraint = None

        #: Reference to the fact type that this object type objectifies.
        self.nested_fact_type = None



