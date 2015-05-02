##############################################################################
# Package: ormpy
# File:    ORMMinusModel.py
# Author:  Matthew Nizol
##############################################################################

""" Module to implement an ORM- model, which is a restricted form of an ORM
    model that can be checked for satisfiability and populated in 
    polynomial time. """

import sys
import logging

from lib.InequalitySystem \
    import InequalitySystem, Inequality, Variable, Constant, Sum, Product
from lib.Constraint \
    import FrequencyConstraint, MandatoryConstraint, ValueConstraint, \
           CardinalityConstraint, SubtypeConstraint
from lib.ObjectType import ObjectType, ObjectifiedType
from lib.FactType import Role
from lib.SubtypeGraph import SubtypeGraph
from lib.Transformation import ValueConstraintTransformation, \
                               AbsorptionTransformation

class ORMMinusModel(object):
    """ An ORM- model along with its solution.  The solution is computed using
        the ORM- satisfiability algorithm (Smaragdakis et al.).

        :param model: The corresponding :class:`lib.Model.Model`
        :param ubound: Upper bound on the size of model elements in the solution

        .. warning:: Generating an ORMMinusModel makes irreversible semantic
           changes to the underlying :class:`lib.Model.Model`.            
    """

    DEFAULT_SIZE = 15 #: Default upper bound on model element cardinalities.

    def __init__(self, model=None, ubound=DEFAULT_SIZE):
        # Initialize public attributes
        self.object_types = model.object_types #: Object types
        self.fact_types = model.fact_types #: Fact types
        self.constraints = model.constraints #: Constraints
        self.ignored = [] #: List of ignored constraints
        
        # Initialize private attributes
        self._model = model #: Underlying ORM Model
        self._ubound = ubound #: Bound on model element size
        self._ineqsys = InequalitySystem() #: System of inequalities
        self._variables = {} #: Dictionary from model element to variable

        # A dictionary of the roles and role sequences associated with each
        # fact type.  If a set of roles are covered by an internal frequency
        # constraint, they are grouped rather than considered separately.
        self._fact_type_parts = {}

        # Generate subtype graph.  
        # IMPORTANT: Any subsequent changes to the subtypes will NOT be 
        # reflected in this graph!
        self.subtype_graph = SubtypeGraph(model) #: Subtype graph of the model

        # Transform the model
        trans = ValueConstraintTransformation(model=self._model, 
                                              subtype_graph=self.subtype_graph)
        trans.execute()
        self.ignored += trans.removed

        AbsorptionTransformation(model).execute()

        # Initialize _fact_type_parts here; _create_variables will update.
        for fact_type in self.fact_types:
            self._fact_type_parts[fact_type] = list(fact_type.roles)

        # Create variables and inequalities
        self._create_variables()
        self._create_inequalities()

        # Compute solution
        self.solution = self._ineqsys.solve()

        # Log any ignored constraints
        logger = logging.getLogger(__name__)
        size = len(self.ignored)
        if size > 0:
            text = "constraints were" if size > 1 else "constraint was"
            logger.warning("%d %s ignored while checking the model.",
                           size, text)
            for cons in self.ignored:
                logger.info("Ignored %s named %s.", 
                            type(cons).__name__, cons.name)

    def get_parts(self, fact_type):
        """ Get the non-overlapping roles and internal frequency constraints
            that comprise a fact type. """
        return self._fact_type_parts.get(fact_type, None)

    def _ignore(self, cons):
        """ Ignore a constraint. """
        self.ignored.append(cons)

    def _add(self, ineq):
        """ Simplify code to add inequalities to system. """
        self._ineqsys.add(ineq)

    def _create_variables(self):
        """ Create set of variables to be used in system of inequalities. """

        # Create one variable for each object type
        for obj_type in self.object_types:
            upper = min(self._ubound, obj_type.domain.max_size)
            self._variables[obj_type] = Variable(obj_type.fullname, upper=upper)

        # Create one variable for each fact type and role
        for fact_type in self.fact_types:
            self._variables[fact_type] = Variable(fact_type.fullname,
                                                  upper=self._ubound)

            for role in fact_type.roles:
                self._variables[role] = Variable(role.fullname,
                                                 upper=self._ubound)

        already_covered = set() # Roles covered by a frequency constraint

        # Create one variable for each internal frequency constraint
        for cons in self.constraints.of_type(FrequencyConstraint):
            if len(set(cons.covers) & already_covered) > 0: # Ignore overlapping
                self._ignore(cons)
            elif cons.internal == False: # Ignore external freq constraints
                self._ignore(cons)
            else:
                already_covered.update(cons.covers)

                self._variables[cons] = Variable(cons.fullname, 
                                                 upper=self._ubound)

                # Update the fact type parts dictionary for this constraint. 
                # Set difference and union would be cleaner here, BUT I want 
                # to preserve an ordering of the parts based on the original
                # role ordering.  
                first_role = cons.covers[0]             
                fact_type = first_role.fact_type # constraint is internal                
                parts = self._fact_type_parts[fact_type]

                # Insert the internal frequency constraint at the correct 
                # position in the parts list and then remove the covered roles
                parts.insert(parts.index(first_role), cons)
                parts = [x for x in parts if x not in cons.covers]

                self._fact_type_parts[fact_type] = parts

    def _create_inequalities(self):
        """ Generate system of inequalities based on rules in Smaragdakis and
            McGill. """

        # Upper bound on object types (needed to ensure that each object type
        # appears as the LHS of at least one inequality).
        for object_type in self.object_types:
            obj_var = self._variables[object_type]
            self._add(Inequality(lhs=obj_var, rhs=Constant(obj_var.upper)))

            # Add inequalities to enforce objectifications
            if isinstance(object_type, ObjectifiedType):
                fact_var = self._variables[object_type.nested_fact_type]
                self._add(Inequality(lhs=obj_var, rhs=fact_var))
                self._add(Inequality(lhs=fact_var, rhs=obj_var))

        # Create inequalities to represent role semantics
        for fact_type in self.fact_types:
            for role in fact_type.roles:
                role_var = self._variables[role]
                fact_var = self._variables[fact_type]
                obj_var = self._variables[role.player]

                self._add(Inequality(lhs=role_var, rhs=fact_var))
                self._add(Inequality(lhs=role_var, rhs=obj_var))

        # Create inequalities for each constraint type
        for cons in self.constraints:
            if isinstance(cons, ValueConstraint):
                self._create_value_inequality(cons)
            elif isinstance(cons, MandatoryConstraint):
                self._create_mandatory_inequality(cons)
            elif isinstance(cons, FrequencyConstraint):
                self._create_frequency_inequality(cons)
            elif isinstance(cons, CardinalityConstraint):
                self._create_cardinality_inequality(cons)
            elif isinstance(cons, SubtypeConstraint):
                self._create_subtype_inequality(cons)
            else: # Catch-all so that we can report ignored constraints.
                self._ignore(cons)

        # Create inequality for implicit predicate uniqueness
        for fact_type in self.fact_types:
            fact_var = self._variables[fact_type]
            parts = self.get_parts(fact_type)
            part_vars = [self._variables[part] for part in parts]
            self._add(Inequality(lhs=fact_var, rhs=Product(part_vars)))

        # Create inequalities for implicit disjunctive constraint
        for obj in self.object_types:
            if obj.independent == False and len(obj.roles) > 0:
                obj_var = self._variables[obj]
                role_vars = [self._variables[role] for role in obj.roles]
                self._add(Inequality(lhs=obj_var, rhs=Sum(role_vars)))

    def _create_value_inequality(self, cons):
        """ Value constraint inequality.  

            IMPORTANT: This code assumes that a ValueConstraintTransformation 
            has already been executed to remove unsupported value constraints.
        """        
        if isinstance(cons.covers[0], ObjectType):
            obj_var = self._variables[cons.covers[0]]
            self._add(Inequality(lhs=obj_var, rhs=Constant(cons.size)))
        else: 
            # If this executes, there is a bug in ValueConstraintTransformation
            msg = "Model contains unexpected role value constraints"
            raise RuntimeError(msg)

    def _create_mandatory_inequality(self, cons):
        """ Simple mandatory constraint inequality. """
        role = cons.covers[0]
        role_var = self._variables[role]
        obj_var = self._variables[role.player]

        if cons.simple:
            self._add(Inequality(lhs=obj_var, rhs=role_var))
        else: # Ignore disjunctive mandatory constraints
            self._ignore(cons)

    def _create_frequency_inequality(self, cons):
        """ Internal frequency constraint inequality. """

        # External and overlapping constraints should already be ignored 
        # during variable creation.
        if cons in self.ignored: return

        # Get variables that will be used in the inequalities
        role_seq = cons.covers
        role_vars = [self._variables[role] for role in role_seq]

        min_var = Constant(1.0 / cons.min_freq)

        # If max_freq > _ubound, set to _ubound.  This fixes an overflow bug
        # for unbounded constraints (i.e. max_freq == float('inf')).  Setting it
        # to _ubound is safe because no object can be repeated more times than
        # the number of tuples in the predicate, whose upper bound is _ubound.
        max_var = Constant(min(self._ubound, cons.max_freq))

        fact_var = self._variables[role_seq[0].fact_type]
        freq_var = self._variables[cons]

        # Generate the four types of inequalities required by Smaragdakis
        self._add(Inequality(lhs=fact_var, rhs=Product([max_var, freq_var])))
        self._add(Inequality(lhs=freq_var, rhs=Product([min_var, fact_var])))
        self._add(Inequality(lhs=freq_var, rhs=Product(role_vars)))

        for role in role_seq:
            role_var = self._variables[role]
            self._add(Inequality(lhs=role_var, rhs=freq_var))

    def _create_cardinality_inequality(self, cons):
        """ Cardinality constraint inequality. """

        # Only support cardinality constraints with a single range covering a 
        # single model element.
        if len(cons.ranges) != 1 or len(cons.covers) != 1:
            self._ignore(cons)
        else:
            var = self._variables[cons.covers[0]]
            lower = cons.ranges[0].lower
            upper = cons.ranges[0].upper

            self._add(Inequality(lhs=Constant(lower), rhs=var))

            if upper != None:
                self._add(Inequality(lhs=var, rhs=Constant(upper)))

    def _create_subtype_inequality(self, cons):
        """ Subtype constraint inequality. """
        subtype_var = self._variables[cons.covers[0]]
        supertype_var = self._variables[cons.covers[1]]
        self._add(Inequality(lhs=subtype_var, rhs=supertype_var))
