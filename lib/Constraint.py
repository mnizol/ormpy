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
    """ A value constraint.  This implementation supports only a limited
        form of value constraint: specifically, enumerations (i.e. min
        value == max value), bounded integer ranges, or a combination
        of the two.  For example:
 
        *Supported:*

        * {'Dog', 'Cat', 'Monkey'}
        * {1..25, 20..30}
        * {1.54, 1.78, 1.99}
        * {2001/12/31, 2002/02/13}
        * {'Dog', 1..25, 'Cat', 1.45, 20..30}

        *Not supported:*

        * Range of text values: {'Dog'..'Donna'}
        * Unbounded integer range: {>1}
        * Invalid range: {3..2}
        * Range of float values: {3.6..3.7}
        """
    
    MAX_SIZE = 1000 #: Arbitrary, for performance.

    def __init__(self, uid=None, name=None):
        super(ValueConstraint, self).__init__(uid=uid, name=name)

        #: set of valid values
        self.domain = set() 

    @property
    def size(self):
        """ The number of items in the domain defined by the constraint. """
        return len(self.domain)

    def add_range(self, min_value, max_value=None, min_open=False, max_open=False):
        """ Add a range of values to the constraint. """
        if max_value is None: # Easier specification of enumerations
            max_value = min_value

        if min_value == max_value and not(min_open) and not(max_open):
            self.domain.add(min_value)  # Single element of any data type.
        else: # Possible range of integers
            try:
                min_int = int(min_value) + (min_open == True)
                max_int = int(max_value) - (max_open == True)
            except (ValueError, OverflowError):
                msg = "Value constraints only support integer ranges"
                raise ValueConstraintError(msg)

            # If we reach this point, we are working with a range of integers.
            if min_int > max_int:
                msg = "The range of the value constraint is invalid"
                raise ValueConstraintError(msg)
            if (max_int - min_int + 1 + self.size) > ValueConstraint.MAX_SIZE:
                msg = "The range of the value constraint is too large"
                raise ValueConstraintError(msg)
            else:
                self.domain.update(range(min_int, max_int+1))

class ValueConstraintError(Exception):
    """ An exception raised by an invalid value constraint. """
    pass
        
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




