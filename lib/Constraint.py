##############################################################################
# Package: ormpy
# File:    Constraint.py
# Author:  Matthew Nizol
##############################################################################

""" This module provides a class for ORM constraints.
"""

from lib.ModelElement import ModelElementSet, ModelElement
from lib.FactType import RoleSequence, Role
from lib.ObjectType import ObjectType
from lib.Domain import Domain, EnumeratedDomain, StringDomain

class ConstraintSet(ModelElementSet):
    """ Container for a set of constraints. """

    def __init__(self, name="Constraints", *args, **kwargs):
        super(ConstraintSet, self).__init__(name=name, *args, **kwargs)

    def of_type(self, cons_type):
        """ Return a list of constraints limited to a given type. """
        return [cons for cons in self if isinstance(cons, cons_type)]

class Constraint(ModelElement):
    """ An ORM Constraint. """

    def __init__(self, covers=None, alethic=True, *args, **kwargs):
        super(Constraint, self).__init__(*args, **kwargs)

        #: List of model element(s) that the constraint covers.  If the 
        #: constraint covers a sequence of roles, use a FactType.RoleSequence.  
        self.covers = covers

        #: True if constraint has alethic modality (False implies deontic)
        self.alethic = alethic

    @property
    def fullname(self):
        """ Returns name that is unique within the model. """
        return "Constraints." + self.name

    def commit(self):
        """ Commit side effects of this constraint in the model. """
        for element in self.covers or []:
            element.covered_by.append(self)

    def rollback(self):
        """ Rollback side effects of this constraint in the model. """
        for element in self.covers or []:
            try: element.covered_by.remove(self)
            except ValueError: pass

class CardinalityConstraint(Constraint):
    """ A cardinality constraint on an object type or role. """

    def __init__(self, ranges=None, *args, **kwargs):
        super(CardinalityConstraint, self).__init__(*args, **kwargs)
        self.ranges = ranges #: A list of CardinalityRange objects

class CardinalityRange(object):
    """ A range for a cardinality constraint. """

    def __init__(self, lower=0, upper=None):
        self.lower = lower
        self.upper = upper

class ValueConstraint(Constraint):
    """ A value constraint.  This implementation supports only a limited
        form of value constraint: specifically, enumerations, bounded integer 
        ranges, or a combination of the two.  For example:

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

    def __init__(self, domain=None, *args, **kwargs):
        super(ValueConstraint, self).__init__(*args, **kwargs)

        #: A ValueDomain containing the set of valid values
        self.domain = domain or ValueDomain()

    @property
    def size(self):
        """ The number of items in the domain defined by the constraint. """
        return self.domain.size

    def commit(self):
        """ Commit side effects of this constraint in the model. """
        element = self.covers[0]
        if isinstance(element, ObjectType):
            element.domain = self.domain
        Constraint.commit(self)

    def rollback(self):
        """ Rollback side effects of this constraint in the model. """
        element = self.covers[0]
        if isinstance(element, ObjectType):
            element.domain = element.data_type
        Constraint.rollback(self)

class ValueDomain(EnumeratedDomain):
    """ The domain of a value constraint. """

    MAX_SIZE = 10000 #: Arbitrary, for performance.

    def __init__(self, *args, **kwargs):
        super(ValueDomain, self).__init__(*args, **kwargs)        

    def add_range(self, min_value, max_value=None, min_open=False, 
                  max_open=False, data_type=None):
        """ Add a range of values to the domain. """
        if max_value is None: # Easier specification of enumerations
            max_value = min_value

        data_type = data_type or Domain() # Generic Domain will not cast

        if min_value == max_value and not min_open and not max_open:
            # Single element, which we'll try to cast to the provided data type
            try:
                self.add(data_type.cast(min_value))
            except (ValueError, NotImplementedError):
                self.add(min_value)  
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
            if (max_int - min_int + 1 + self.size) > ValueDomain.MAX_SIZE:
                msg = "The range of the value constraint is too large"
                raise ValueConstraintError(msg)
            else:
                self.add(range(min_int, max_int+1))

class ValueConstraintError(Exception):
    """ An exception raised by an invalid value constraint. """
    pass

class SubtypeConstraint(Constraint):
    """ A subtype constraint. """

    def __init__(self, subtype=None, supertype=None, idpath=True,
                 *args, **kwargs):
        super(SubtypeConstraint, self).__init__(*args, **kwargs)

        self.subtype = subtype #: Subtype object type
        self.supertype = supertype #: Supertype object type

        self.covers = [subtype, supertype]

        #: True if subtype constraint is on path to preferred id.  This is
        #: relevant if the subtype inherits one of its supertypes' reference
        #: schemes, and the supertype graph is not a simple path.
        self.idpath = idpath

    def commit(self):
        """ Commit side effects of this constraint in the model. """
        self.supertype.direct_subtypes.append(self.subtype)
        self.subtype.direct_supertypes.append(self.supertype)
        Constraint.commit(self)

    def rollback(self):
        """ Rollback side effects of this constraint in the model. """

        # The code commented out below the raise statement undoes what's done
        # in commit().  However, I am concerned that if you rollback a subtype
        # constraint, any SubtypeGraph that exists is now invalid, as are any
        # IOR/XOR constraints that cover the subtype.  THUS, since I can't 
        # think of why you'd need to rollback a subtype, I'm just going to 
        # raise an exception for now.
        raise NotImplementedError()

        #self.supertype.direct_subtypes.remove(self.subtype)
        #self.subtype.direct_supertypes.remove(self.supertype)
        #Constraint.rollback(self)

class MandatoryConstraint(Constraint):
    """ A mandatory constraint. """

    def __init__(self, *args, **kwargs):
        super(MandatoryConstraint, self).__init__(*args, **kwargs)

    @property
    def simple(self):
        """ True if mandatory constraint is simple. """
        return len(self.covers) == 1

    def commit(self):
        """ Commit side effects of this constraint in the model. """
        if self.simple:
            role = self.covers[0]
            role.mandatory = True
        Constraint.commit(self)

    def rollback(self):
        """ Rollback side effects of this constraint in the model. """
        if self.simple:
            role = self.covers[0]
            role.mandatory = False
        Constraint.rollback(self)


class SubsetConstraint(Constraint):
    """ A subset constraint. """

    def __init__(self, subset=None, superset=None, *args, **kwargs):
        super(SubsetConstraint, self).__init__(*args, **kwargs)

        #: Sequence of subset roles (:class:`lib.FactType.RoleSequence`)
        self.subset = subset 

        #: Sequence of superset roles (:class:`lib.FactType.RoleSequence`)
        self.superset = superset

    @property
    def covers(self):
        """ List of covered roles (combines self.subset and self.superset). """
        if self.subset and self.superset:
            return self.subset + self.superset
        else:
            return None

    @covers.setter
    def covers(self, value):
        pass # Ignore any attempt to directly set covers on a subset constraint

class EqualityConstraint(SubsetConstraint):
    """ An equality constraint.  This is a subtype of SubsetConstraint because
        of how they are handled by the instantiation algorithm (i.e. an
        EqualityConstraint is equivalent to a SubsetConstraint whose role
        sequences have the same cardinality). """
    
    def __init__(self, *args, **kwargs):
        super(EqualityConstraint, self).__init__(*args, **kwargs)

class FrequencyConstraint(Constraint):
    """ A frequency constraint. """

    def __init__(self, min_freq=0, max_freq=float('inf'), *args, **kwargs):
        super(FrequencyConstraint, self).__init__(*args, **kwargs)

        self.min_freq = min_freq #: Minimum frequency
        self.max_freq = max_freq #: Maximum frequency

        # Detect whether frequency constraint is internal
        fact_types = set()
        for role in self.covers or []:
            fact_types.add(role.fact_type)
        self.internal = (len(fact_types) == 1)

class UniquenessConstraint(FrequencyConstraint):
    """ A uniqueness constraint (a special case of Frequency Constraint). """

    def __init__(self, identifier_for=None, *args, **kwargs):
        super(UniquenessConstraint, self).__init__(*args, **kwargs)

        #: A uniqueness constraint is a special case of a frequency constraint
        #: in which the min and max frequencies are both 1
        self.min_freq = 1
        self.max_freq = 1

        #: Object type this constraint identifies
        self.identifier_for = identifier_for

    def commit(self):
        """ Commit side effects of this constraint in the model. """
        if self.simple:
            self.covers[0].unique = True

        if self.identifier_for is not None:
            obj = self.identifier_for
            obj.identifying_constraint = self

            # Set the reference roles for the identified object type
            obj.ref_roles = []
            for fact_type in {role.fact_type for role in self.covers}:
                obj.ref_roles += [r for r in fact_type.roles if r.player == obj]                                 

        Constraint.commit(self)

    def rollback(self):
        """ Rollback side effects of this constraint in the model. """
        if self.simple:
            simple = lambda x: isinstance(x, UniquenessConstraint) and x.simple
            if len(filter(simple, self.covers[0].covered_by)) == 1:
                self.covers[0].unique = False

        if self.identifier_for is not None:
            self.identifier_for.identifying_constraint = None
            self.identifier_for.ref_roles = []
        Constraint.rollback(self)

    @property
    def simple(self):
        """ True iff constraint is internal and covers only one role. """
        return len(self.covers) == 1 and self.internal

