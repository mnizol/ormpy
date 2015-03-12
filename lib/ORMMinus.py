##############################################################################
# Package: ormpy
# File:    ORMMinus.py
# Author:  Matthew Nizol
##############################################################################

""" Module to implement ORMMinus satisfiability and population algorithm. """

import sys
from lib.InequalitySystem \
    import InequalitySystem, Inequality, Variable, Constant, Sum, Product
from lib.Constraint \
    import FrequencyConstraint, MandatoryConstraint, ValueConstraint
from lib.ObjectType import ObjectType

class ORMMinus(object):
    """ Implements ORMMinus algorithm (Smaragdakis et al.).

        :param model: A :class:`lib.Model.Model` to instantiate
        :param ubound: Upper bound on size of model elements
    """

    def __init__(self, model=None, ubound=sys.maxsize):
        # Initialize attributes
        self._model = model #: ORM model
        self._ubound = ubound #: Bound on model element size
        self._ineqsys = InequalitySystem() #: System of inequalities
        self._variables = {} #: Dictionary from model element to variable
        self.ignored = [] #: List of ignored constraints

        # A dictionary of the roles and role sequences associated with each
        # fact type.  If a set of roles are covered by an internal frequency
        # constraint, they are grouped rather than considered separately.
        self._fact_type_parts = {}

        # Initialize _fact_type_parts here; _create_variables will update.
        for fact_type in self._model.fact_types:
            self._fact_type_parts[fact_type] = list(fact_type.roles)

        # Create variables and inequalities
        self._create_variables()
        self._create_inequalities()

    def check(self):
        """ Checks model for satisifiability.  Returns solution if satisfiable
            and None otherwise. """
        return self._ineqsys.solve()

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
        for obj_type in self._model.object_types:
            upper = min(self._ubound, obj_type.domain.max_size)
            self._variables[obj_type] = Variable(obj_type.fullname, upper=upper)

        # Create one variable for each fact type and role
        for fact_type in self._model.fact_types:
            self._variables[fact_type] = Variable(fact_type.fullname,
                                                  upper=self._ubound)

            for role in fact_type.roles:
                self._variables[role] = Variable(role.fullname,
                                                 upper=self._ubound)

        already_covered = set() # Roles covered by a frequency constraint

        # Create one variable for each internal frequency constraint
        for cons in self._model.constraints.of_type(FrequencyConstraint):
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
        for object_type in self._model.object_types:
            obj_var = self._variables[object_type]
            self._add(Inequality(lhs=obj_var, rhs=Constant(obj_var.upper)))

        # Create inequalities to represent role semantics
        for fact_type in self._model.fact_types:
            for role in fact_type.roles:
                role_var = self._variables[role]
                fact_var = self._variables[fact_type]
                obj_var = self._variables[role.player]

                self._add(Inequality(lhs=role_var, rhs=fact_var))
                self._add(Inequality(lhs=role_var, rhs=obj_var))

        # Create inequalities for each constraint type
        for cons in self._model.constraints:
            if isinstance(cons, ValueConstraint):
                self._create_value_inequality(cons)
            elif isinstance(cons, MandatoryConstraint):
                self._create_mandatory_inequality(cons)
            elif isinstance(cons, FrequencyConstraint):
                self._create_frequency_inequality(cons)
            else: # Catch-all so that we can report ignored constraints.
                self._ignore(cons)

        # Create inequality for implicit predicate uniqueness
        for fact_type in self._model.fact_types:
            fact_var = self._variables[fact_type]
            parts = self.get_parts(fact_type)
            part_vars = [self._variables[part] for part in parts]
            self._add(Inequality(lhs=fact_var, rhs=Product(part_vars)))

        # Create inequalities for implicit disjunctive constraint
        for obj in self._model.object_types:
            if obj.independent == False and len(obj.roles) > 0:
                obj_var = self._variables[obj]
                role_vars = [self._variables[role] for role in obj.roles]
                self._add(Inequality(lhs=obj_var, rhs=Sum(role_vars)))

    def _create_value_inequality(self, cons):
        """ Value constraint inequality. """

        # Per McGill, we cannot support value constraints on roles, only on
        # types.  See _load_value_restriction in NormaLoader, which moves
        # certain value constraints on roles to the type so that they can be
        # included in the ORMMinus solution.
        
        if isinstance(cons.covers[0], ObjectType):
            obj_var = self._variables[cons.covers[0]]
            self._add(Inequality(lhs=obj_var, rhs=Constant(cons.size)))
        else:
            self._ignore(cons)

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
        max_var = Constant(cons.max_freq)

        fact_var = self._variables[role_seq[0].fact_type]
        freq_var = self._variables[cons]

        # Generate the four types of inequalities required by Smaragdakis
        self._add(Inequality(lhs=fact_var, rhs=Product([max_var, freq_var])))
        self._add(Inequality(lhs=freq_var, rhs=Product([min_var, fact_var])))
        self._add(Inequality(lhs=freq_var, rhs=Product(role_vars)))

        for role in role_seq:
            role_var = self._variables[role]
            self._add(Inequality(lhs=role_var, rhs=freq_var))

