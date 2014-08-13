##############################################################################
# Package: ormpy
# File:    Constraint.py
# Author:  Matthew Nizol
##############################################################################

""" This module provides a class for ORM constraints.  
"""

from lib.ModelElement import ModelElementSet, ModelElement
from lib.FactType import RoleSequence

class ConstraintSet(ModelElementSet):
    """ Container for a set of constraints. """

    def __init__(self):
        super(ConstraintSet, self).__init__(name="Constraints")

class Constraint(ModelElement):
    """ An ORM Constraint. """

    def __init__(self, uid=None, name=None):
        super(Constraint, self).__init__(uid=uid, name=name)

        #: Roles or object types the constraint covers 
        #: (:class:`lib.FactType.RoleSequence`)
        self.covers = RoleSequence()

        #: True if constraint has alethic modality (False implies deontic)
        self.alethic = True  

    @property
    def fullname(self):
        return "Constraints." + self.name

    def cover(self, model_element):
        """ Add a model element to the list of elements covered by 
            the constraint. """
        self.covers.append(model_element)

class ValueConstraint(Constraint):
    """ A value constraint. """
    
    def __init__(self, uid=None, name=None):
        super(ValueConstraint, self).__init__(uid=uid, name=name)

        #: List of value ranges (:class:`lib.Constraint.ValueRange`)
        self.ranges = [] 

    def add_range(self, min_value, max_value, min_open=False, max_open=False):
        """ Add a range of values to the constraint. """
        value_range = ValueRange(min_value, max_value, min_open, max_open)
        self.ranges.append(value_range)
        
class ValueRange(object):
    """ A range of values. """
    
    def __init__(self, min_value, max_value, min_open=False, max_open=False):
        self.min_value = min_value #: Minimum value of the range
        self.max_value = max_value #: Maximum value of the range
        self.min_open = min_open   #: True if minimum value excluded from range
        self.max_open = max_open   #: True if maximum value excluded from range

class SubtypeConstraint(Constraint):
    """ A subtype constraint. """

    def __init__(self, uid=None, name=None):
        super(SubtypeConstraint, self).__init__(uid=uid, name=name)
        
        self.subtype = None #: Subtype object type
        self.supertype = None #: Supertype object type

        #: True if subtype constraint is on path to preferred id.  This is 
        #: relevant if the subtype inherits one of its supertypes' reference
        #: schemes, and the supertype graph is not a simple path.
        self.preferred_id = None

class MandatoryConstraint(Constraint):
    """ A mandatory constraint. """

    def __init__(self, uid=None, name=None):
        super(MandatoryConstraint, self).__init__(uid=uid, name=name) 

        self.simple = False #: True for simple mandatory constraints

class SubsetConstraint(Constraint):
    """ A subset constraint. """

    def __init__(self, uid=None, name=None):
        super(SubsetConstraint, self).__init__(uid=uid, name=name)

        #: Sequence of subset roles (:class:`lib.FactType.RoleSequence`)
        self.subset = RoleSequence()

        #: Sequence of superset roles (:class:`lib.FactType.RoleSequence`)
        self.superset = RoleSequence() 

    def cover_subset(self, role):
        """ Add a role to the list of subset roles covered by this
            constraint."""
        self.subset.append(role)
        self.cover(role) # Add to full list of covered roles

    def cover_superset(self, role):
        """ Add a role to the list of superset roles covered by
            this constraint. """
        self.superset.append(role)
        self.cover(role) # Add to full list of covered roles

class UniquenessConstraint(Constraint):
    """ A uniqueness constraint. """

    def __init__(self, uid=None, name=None):
        super(UniquenessConstraint, self).__init__(uid=uid, name=name) 
        
        #: True if constraint covers roles in one fact type
        self.internal = False 

        #: Object type this constraint identifies
        self.identifier_for = None 

class FrequencyConstraint(Constraint):
    """ A frequency constraint. """

    def __init__(self, uid=None, name=None):
        super(FrequencyConstraint, self).__init__(uid=uid, name=name)

        self.min_freq = None #: Minimum frequency
        self.max_freq = None #: Maximum frequency

class ExclusionConstraint(Constraint):
    """ An exclusion constraint. """

    def __init__(self, uid=None, name=None):
        super(ExclusionConstraint, self).__init__(uid=uid, name=name)




