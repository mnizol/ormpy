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
        """ Returns name that is unique within the model. """
        return "FactTypes." + self.name

    def commit(self):
        """ Commit any side effects of adding this fact type to a model."""
        # TODO: Implement later
        # This is just a skeletal implementation
        for role in self.roles:
            role.commit()

    def rollback(self):
        """ Rollback any side effects of adding this fact type to a model."""
        # TODO: Implement later
        # This is just a skeletal implementation
        for role in self.roles:
            role.rollback()

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

        self.fact_type = None #: Fact type to which role belongs
        self.player = None #: Object type that plays the role
        self.covered_by = [] #: Constraints that cover this role

        #: True if the role is covered by an explicit mandatory constraint
        self.mandatory = False 

    @property
    def fullname(self):
        """ Returns name that is unique within the model. """
        return "FactTypes." + self.fact_type.name + ".Roles." + self.name

    def commit(self):
        """ Commit any side effects of adding this role to a model."""
        pass # TODO: Implement later

    def rollback(self):
        """ Rollback any side effects of adding this role to a model."""
        pass # TODO: Implement later

class RoleSequence(list):
    """ A sequence of roles. """

    def __init__(self):
        super(RoleSequence, self).__init__()

        self.join_path = None #: Join path for the role sequence

