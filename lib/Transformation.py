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
from lib.Constraint import ValueConstraint, UniquenessConstraint, \
                           FrequencyConstraint, MandatoryConstraint
from lib.FactType import Role, FactType
from lib.ObjectType import ObjectifiedType
from lib.SubtypeGraph import SubtypeGraph

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

    @property
    def model_changed(self):
        """ True iff model is changed by this transformation. """
        return len(self.removed + self.modified + self.added) > 0

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


###############################################################################
# Value Constraint Transformation
###############################################################################
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
        self.subtype_graph = subtype_graph or SubtypeGraph(self.model)

        # Dictionary to keep track of whether we've already found a value 
        # constraint for a non-primitive type in the same subtype graph
        self._graph_has_subtype_vc = {}

    def execute(self):
        """ Execute the transformation. """
        for cons in self.model.constraints.of_type(ValueConstraint):
            element = cons.covers[0]
            if isinstance(element, Role):
                self._transform_role_value_constraint(cons, element)
            elif not element.primitive:
                self._transform_subtype_value_constraint(cons, element)

        return self.model_changed

    def _transform_role_value_constraint(self, cons, role):
        obj = role.player         

        if len(obj.roles) == 1 and (role.mandatory or not obj.independent):
            self._modified(cons) # Mark as modified
            cons.rollback() # Undo side effects -- e.g. uncover role
            cons.covers = [obj] # Move constraint to object type

            # Intersect cons with any existing value constraint on object type.
            # Leave the (now extra) value constraints on the model---the domain
            # of the object type will consist of the intersection after commit()
            for cons2 in self._value_constraints(obj):
                cons.domain &= cons2.domain
            
            cons.commit() # Commit side effects
        else: # Remove all other role value constraints
            self._remove(cons)

    def _transform_subtype_value_constraint(self, cons, subtype):
        root = self.subtype_graph.root_of[subtype]
        root_value_constraints = self._value_constraints(root)
 
        if self._graph_has_subtype_vc.get(root): # Only one subtype VC permitted
            self._remove(cons)
        elif len(root_value_constraints) == 0:
            # NOTE: Requiring that the root has a value constraint if a subtype 
            # does is more restrictive than theoretically necessary.  However,  
            # it would be a bit of a challege to implement the necessary set 
            # intersection and set difference (see else clause below) if 
            # root.domain is of infinite size like IntegerDomain.
            self._remove(cons)
        else:
            assert len(root_value_constraints) == 1

            self._graph_has_subtype_vc[root] = True
            root_cons = root_value_constraints[0]

            # Lazily mark these as modified, even though it's possible the below 
            # set operations will have no effect.
            self._modified(cons)
            self._modified(root_cons)

            # Limit the subtype value constraint to those elements also in root.
            cons.rollback()
            cons.domain &= root_cons.domain  
            cons.commit() 

            # Force the root domain to begin with the subtype domain's elements.
            root_cons.rollback()
            root_only = root_cons.domain - cons.domain
            root_cons.domain = cons.domain + root_only 
            root_cons.commit()   

    @staticmethod
    def _value_constraints(object_type):
        """ Return the value constraints (if any) covering an object type. """
        vc = lambda x: isinstance(x, ValueConstraint)
        return filter(vc, object_type.covered_by)

###############################################################################
# Absorption
###############################################################################
class AbsorptionTransformation(Transformation):
    """ An absorption transformation as described by McGill et al. (2011).
        Replaces compound refererence schemes with absorption fact types. """

    def __init__(self, *args, **kwargs):
        super(AbsorptionTransformation, self).__init__(*args, **kwargs)

        # Get list of objectified fact types
        self.nested_fact_types = {obj.nested_fact_type for obj in 
            self.model.object_types if isinstance(obj, ObjectifiedType)}

    def execute(self):
        """ Execute the transformation. """
        candidates = self.model.constraints.of_type(UniquenessConstraint)

        for euc in filter(self._pattern, candidates): 
            # Get root player
            root_player = self._other_role(euc.covers[0]).player

            # Build absorption fact type
            fact_type = AbsorptionFactType(root_player, name=euc.name)

            # Cover the root role with an IUC and a mandatory constraint
            self._add(UniquenessConstraint(covers=[fact_type.root_role]))
            self._add(MandatoryConstraint(covers=[fact_type.root_role]))

            # Loop over covered roles, move to absorption fact type
            new_roles = []

            for old_role in euc.covers:
                new_role = fact_type.add_role(old_role.player)
                new_roles.append(new_role)

                old_fact_type_name = old_role.fact_type.fullname
                fact_type.fact_type_names[new_role.name] = old_fact_type_name

                if old_role.mandatory:
                    self._add(MandatoryConstraint(covers=[new_role]))

                # Remove original fact type from the model. Can't call 
                # self._remove here because fact_type.rollback is unimplemented
                self._remove_fact_type(old_role.fact_type) 

            self._add(UniquenessConstraint(covers=new_roles, 
                                           identifier_for = euc.identifier_for))
            self._add(fact_type)
            #self._remove(euc) # Removed when we remove first fact type.

        return self.model_changed

    def _pattern(self, euc):
        """ Check if euc matches absorption pattern. """

        if euc.internal:
            return False

        obj_type = None

        for role in euc.covers:
            # Covered fact type must be binary
            if role.fact_type.arity() != 2:
                return False

            # Covered roles may only be *also* covered by a mandatory constraint
            for cons in role.covered_by:
                if cons != euc and not self._simple_mandatory(cons):
                    return False

            # All other roles must be played by the same object type.
            role2 = self._other_role(role)
            obj_type = obj_type or role2.player # First player among other roles
            
            if role2.player != obj_type:
                return False

            # Other role must be covered only by simple IUC and simple mandatory
            if len(role2.covered_by) != 2:
                return False
 
            if any(filter(self._simple_iuc, role2.covered_by)) == False:
                return False

            if any(filter(self._simple_mandatory, role2.covered_by)) == False:
                return False

            # Fact type cannot be objectified
            if role.fact_type in self.nested_fact_types:
                return False                

        return True

    def _remove_fact_type(self, fact_type):
        """ Remove fact_type from self.model.

            IMPORTANT: This is implemented here rather than via a remove 
                       method of fact_type because I haven't decided how to 
                       handle fact type rollback/removal in the general case.
                       
                       Specifically, this method does not consider join paths or
                       objectifications that may be on the fact type, but since
                       (a) _pattern() forbids objectification and (b) absorption
                       assumes there are no join paths, this is OK.
        """
        for role in fact_type.roles:
            # To remove constraints, I first need to make a copy of covered_by
            map(self._remove, [cons for cons in role.covered_by])
            role.player.roles.remove(role)

        self.model.fact_types.remove(fact_type)
        self.removed.append(fact_type)

    def _simple_iuc(self, cons):
        """ Returns True if cons is a simple internal uniqueness constraint. """
        return isinstance(cons, UniquenessConstraint) and len(cons.covers) == 1

    def _simple_mandatory(self, cons):
        """ Returns True if cons is a simple mandatory constraint. """
        return isinstance(cons, MandatoryConstraint) and cons.simple

    def _other_role(self, role):
        """ Returns the other role in a binary fact type. """
        return (set(role.fact_type.roles) - set([role])).pop() 

class AbsorptionFactType(FactType):
    """ The fact type created by an absorption transformation. """

    def __init__(self, root_player=None, *args, **kwargs):
        super(AbsorptionFactType, self).__init__(*args, **kwargs)  

        #: Role played by the identified object type
        self.root_role = FactType.add_role(self, root_player)       

        #: Original fact type name for each role
        self.fact_type_names = {}  

###############################################################################
# Disjunctive Reference Transformation
###############################################################################
class DisjunctiveRefTransformation(Transformation):
    """ Sets all ref roles in a disjunctive reference scheme to mandatory,
        and removes any inclusive-or constraints on those roles.  """

    def __init__(self, *args, **kwargs):
        super(DisjunctiveRefTransformation, self).__init__(*args, **kwargs)

    def execute(self):
        """ Execute the transformation. """
        ior = lambda x: isinstance(x, MandatoryConstraint) and not x.simple

        for obj in self.model.object_types:
            for role in obj.ref_roles:
                if not role.mandatory:
                    self._add(MandatoryConstraint(covers=[role]))

                map(self._remove, filter(ior, role.covered_by))

        return self.model_changed
