##############################################################################
# Package: ormpy
# File:    FactType.py
# Author:  Matthew Nizol
##############################################################################

""" This module provides a class for ORM fact types.
"""

import re
from lib.ModelElement import ModelElementSet, ModelElement

class FactTypeSet(ModelElementSet):
    """ Container for a set of fact types. """

    def __init__(self, name="Fact Types", *args, **kwargs):
        super(FactTypeSet, self).__init__(name=name, *args, **kwargs)


class FactType(ModelElement):
    """ An ORM Fact Type. """

    def __init__(self, *args, **kwargs):
        super(FactType, self).__init__(*args, **kwargs)

        self.roles = [] #: List of roles in the fact type

    @property
    def fullname(self):
        """ Returns name that is unique within the model. """
        return "FactTypes." + self.name

    def commit(self):
        """ Commit any side effects of adding this fact type to a model."""
        for role in self.roles:
            role.commit()

    def rollback(self):
        """ Rollback any side effects of adding this fact type to a model."""
        # I haven't decided what rollback() should do here.  Obviously, at least
        # it should call rollback() for each of its role.  But, if we rollback
        # a fact type, should we also rollback (or delete) associated
        # constraints, join paths, etc?  What if this is objectified, etc?
        raise NotImplementedError()

    def add_role(self, player, name=None, uid=None):
        """ Add a role played by *player* to the fact type.  If *name* is None
            or if *name* is already used by a role in the fact type, then 
            this method generates a name for the role based upon player's name. 
        """

        # Generate name for role if necessary
        names = [role.name for role in self.roles] # Existing pool of names

        if name is None or name == "" or name in names:            
            suffix, i = '', 1
            while player.name + suffix in names:
                i += 1
                suffix = str(i)
            name = player.name + suffix

        role = Role(fact_type=self, player=player, name=name, uid=uid)
        self.roles.append(role)
        return role

    def arity(self):
        """ Returns the arity of the fact type. """
        return len(self.roles)

class Role(ModelElement):
    """ A role in a fact type. """

    def __init__(self, fact_type=None, player=None, *args, **kwargs):
        super(Role, self).__init__(*args, **kwargs)

        self.fact_type = fact_type #: Fact type to which the role belongs.  
        self.player = player  #: Object type that plays the role
        self.covered_by = []  #: Constraints that cover this role
                              #: Populated when a constraint is committed.

        #: True if the role is covered by an explicit mandatory constraint
        self.mandatory = False # Populated when a mandatory cons is committed.

        #: True if the role is covered by simple internal uniqueness constraint
        self.unique = False # Populated when the IUC is committed.

    @property
    def fullname(self):
        """ Returns name that is unique within the model. """
        return "FactTypes." + self.fact_type.name + ".Roles." + self.name

    @property
    def data_type(self):
        """ Raw conceptual data type of the role's player. """
        return self.player.data_type

    def commit(self):
        """ Commit any side effects of adding this role to a model."""
        self.player.roles.append(self) # Add to roles played by object type

    def rollback(self):
        """ Rollback any side effects of adding this role to a model."""
        # I haven't decided what to do here.  At minimum, I need to remove
        # the role from self.player.roles.  However, should I also rollback
        # constraints in self.covered_by?  Should I rollback the containing
        # fact type?  What about join paths through this role?  Etc.
        raise NotImplementedError()

class RoleSequence(list):
    """ A sequence of roles. """

    def __init__(self, roles=None, join_path=None, *args, **kwargs):
        super(RoleSequence, self).__init__(*args, **kwargs)

        if roles: self.extend(roles)

        self.join_path = join_path #: Join path for the role sequence

