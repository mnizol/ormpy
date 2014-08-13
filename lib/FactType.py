##############################################################################
# Package: ormpy
# File:    FactType.py
# Author:  Matthew Nizol
##############################################################################

""" This module provides a class for ORM fact types.  
"""

from lib.ModelElement import ModelElementSet, ModelElement

class FactTypeSet(ModelElementSet):
    """ Container for a set of fact types. """

    def __init__(self):
        super(FactTypeSet, self).__init__(name="Fact Types")


class FactType(ModelElement):
    """ An ORM Fact Type. """

    def __init__(self, uid=None, name=None):
        super(FactType, self).__init__(uid=uid, name=name)

        self.roles = [] #: List of roles in the fact type

    @property
    def fullname(self):
        return "FactTypes." + self.name

    def add(self, role):
        """ Add *role* to the fact type. """
        self.roles.append(role)

    def arity(self):
        """ Returns the arity of the fact type. """
        return len(self.roles)

class Role(ModelElement):
    """ A role in a fact type. """

    def __init__(self, uid=None, name=None):
        super(Role, self).__init__(uid=uid, name=name)
        
        fact_type = None #: Fact type to which role belongs
        player = None #: Object type that plays the role

    @property
    def fullname(self):
        return "FactTypes." + self.fact_type.name + ".Roles." + self.name

class SubtypeRole(Role):
    """ A subtype role. """

    def __init__(self, uid=None, name=None):
        super(SubtypeRole, self).__init__(uid=uid, name=name)

class RoleSequence(list):
    """ A sequence of roles. """

    def __init__(self):
        super(RoleSequence, self).__init__()

        self.join_path = None #: Join path for the role sequence

