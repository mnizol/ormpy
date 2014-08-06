##############################################################################
# Package: ormpy
# File:    Constraint.py
# Author:  Matthew Nizol
##############################################################################

""" This module provides a class for ORM constraints.  
"""

from lib.ModelElement import ModelElementSet, ModelElement

class ConstraintSet(ModelElementSet):
    """ Container for a set of constraints. """

    def __init__(self):
        super(ConstraintSet, self).__init__(name="Constraints")

class Constraint(ModelElement):
    """ An ORM Constraint. """

    def __init__(self, uid=None, name=None):
        super(Constraint, self).__init__(uid=uid, name=name)

        #: List of roles or object types the constraint covers
        self.covers = [] 

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
        
        subtype = None #: Subtype object type
        supertype = None #: Supertype object type

        #: True if subtype constraint is on path to preferred id.  This is 
        #: relevant if the subtype inherits one of its supertypes' reference
        #: schemes, and the supertype graph is not a simple path.
        preferred_id = None

class MandatoryConstraint(Constraint):
    """ A mandatory constraint. """

    def __init__(self, uid=None, name=None):
        super(MandatoryConstraint, self).__init__(uid=uid, name=name) 

