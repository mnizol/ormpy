##############################################################################
# Package: ormpy
# File:    Transformation.py
# Author:  Matthew Nizol
##############################################################################
""" The Transformation.py module provides classes that transform a 
    :class:`lib.Model.Model` in various ways.  

    .. warning:: The transformations in this module modify the source Model
       in place.  There is currently no means to reverse a Transformation.
"""

from lib.Model import Model
from lib.Constraint import ValueConstraint
from lib.FactType import Role
from lib.Domain import EnumeratedDomain

class Transformation(object):
    """ A transformation of an ORM Model. """

    def __init__(self, model=None, *args, **kwargs):
        super(Transformation, self).__init__(*args, **kwargs)

        self.model = model #: ORM model to transform

        self.removed = [] #: List of elements removed by this transformation
        self.modified = [] #: List of elements modified by this transformation
        self.added = [] #: List of elements added by this transformation

    def execute(self):
        """ Execute the transformation. """
        raise NotImplementedError()

    def _add(self, element):
        """ Add an element to the model. """
        self.added.append(element)
        self.model.add(element)

    def _remove(self, element):
        """ Remove an element from the model. """
        self.removed.append(element)
        self.model.remove(element)

    def _modified(self, element):
        """ Tag an element as modified. The actual modification must be 
            performed external to this method.  """
        self.modified.append(element)

class ValueConstraintTransformation(Transformation):
    """ A transformation of an ORM model that moves, removes, and modifies
        value constraints to be consistent with ORM- rules.  Specifically, this 
        transformation affects role value constraints and subtype value
        constraints as discussed in the below subsections.

        **Role value constraints:**

        ORM- does not support role value constraints, only value
        constraints on types.  However, if the value constraint covers a 
        role for an object type that plays no other roles and either:

        1) The type is not independent (so the role is implicitly mandatory) 
        2) The role is covered by an explicit mandatory constraint

        Then the value constraint can be treated as an object type value
        constraint.  Role value constraints that meet this criteria are thus
        moved to the object type.  If the object type that meets this test is 
        *already* covered by a value constraint, then we cover that object type 
        with the intersection of the two constraints.  All other role value
        constraints are removed from the model.

        **Subtype value constraints:**

        ORM- supports at most one value constraint on a non-primitive type 
        within the same subtype graph.  Thus, this transformation updates each 
        subtype graph, retaining the value constraint (if any) on the root 
        type and retaining at most one value constraint on any subtype of the 
        root.  All other value constraints on subtypes of that root are 
        removed.  Then, the remaining subtype value constraint is updated to 
        remove any elements not in the root value constraint's domain, and the
        root value constraint is re-ordered so that the subtype value
        constraint's elements are listed first.  This latter reordering is
        necessary to ensure that the ORM- algorithm populates each subtype
        using only elements from its root type's population.
    """

    def __init__(self, subtype_graph=None, *args, **kwargs):
        super(ValueConstraintTransformation, self).__init__(*args, **kwargs)
    
        #: A :class:`lib.SubtypeGraph.SubtypeGraph` corresponding to 
        #: :attr:`self.model`.
        self.subtype_graph = subtype_graph

    def execute(self):
        """ Execute the transformation. """
        for cons in self.model.constraints.of_type(ValueConstraint):
            element = cons.covers[0]
            if isinstance(element, Role):
                self._transform_role_value_constraint(cons, element)
            elif not element.primitive:
                self._transform_subtype_value_constraint(cons, element)

    def _transform_role_value_constraint(self, cons, role):
        obj = role.player 
        vc = lambda x: isinstance(x, ValueConstraint)

        if len(obj.roles) == 1 and (role.mandatory or not obj.independent):
            self._modified(cons) # Mark as modified
            cons.rollback() # Undo side effects -- e.g. uncover role
            cons.covers = [obj] # Move constraint to object type

            # Intersect cons with any existing value constraint on object type.
            # Leave the (now extra) value constraints on the model---the domain
            # of the object type will consist of the intersection after commit()
            for cons2 in filter(vc, obj.covered_by):
                cons.domain &= cons2.domain
            
            cons.commit() # Commit side effects
        else: # Remove all other role value constraints
            self._remove(cons)

    def _transform_subtype_value_constraint(self, cons, subtype):
        graph_has_subtype_vc = {} 

        root = self.subtype_graph.root_of[subtype]
         
        if graph_has_subtype_vc.get(root): # Only one subtype VC permitted!
            self._remove(cons)
        elif not isinstance(root.domain, EnumeratedDomain):
            # NOTE: Requiring that the root.domain is an EnumeratedDomain is 
            # more restrictive than theoretically necessary.  However, it 
            # would be a bit of a challege to implement the necessary set 
            # intersection and set difference (see else clause below) if 
            # root.domain is of infinite size like IntegerDomain.
            self._remove(cons)
        else:
            graph_has_subtype_vc[root] = True

            # Lazily mark these as modified, even though it's possible the below 
            # set operations will have no effect.
            self._modified(cons)
            self._modified(root.domain)

            # Limit the subtype value constraint to those elements also in root.
            cons.rollback()
            cons.domain &= root.domain  
            cons.commit() 

            # Force the root domain to begin with the subtype domain's elements.
            root_only = sorted(set(root.domain) - set(cons.domain))
            root.domain = cons.domain + root_only        
