##############################################################################
# Package: ormpy
# File:    ORMMinus.py
# Author:  Matthew Nizol
##############################################################################

""" Module to implement ORMMinus satisfiability and population algorithm. """

# TODO: This module does not yet implement all ORM- inequalities.
#       Specifically, it does not implement the following:
#       * Cardinality constraint inequalities
#       * Subtype inequalities
#       * Inequalities described by McGill's or Nizol's extensions to ORM-
#       * Inequality to express implicit uniqueness over a predicate.
#         (This is the 2nd to last bullet on pg 86 of Smaragdakis. Because
#          standard ORM practice is to cover all but (at most) one role with
#          an IUC, I don't think this inequality matters in practice because
#          it is implied by any IUC inequality on the predicate).

import sys
from lib.InequalitySystem \
    import InequalitySystem, Inequality, Variable, Constant, Sum, Product
from lib.Constraint \
    import FrequencyConstraint, MandatoryConstraint, ValueConstraint

class ORMMinus(object):
    """ Implements ORMMinus algorithm (Smaragdakis et al.).

        :param model: A :class:`lib.Model.Model` to instantiate
        :param ubound: Upper bound on size of model elements
    """

    def __init__(self, model=None, ubound=sys.maxint):
        self._model = model #: ORM model
        self._ubound = ubound #: Bound on model element size
        self._ineqsys = InequalitySystem() #: System of inequalities
        self._variables = {} #: Dictionary from model element to variable
        self._obj_roles = {} #: Dictionary from object type to roles
        self.ignored = [] #: List of ignored constraints

    def check(self):
        """ Checks model for satisifiability.  Returns solution if satisfiable
            and None otherwise. """

        self._create_variables()
        self._create_obj_roles_dict()
        self._create_inequalities()
        return self._ineqsys.solve()

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
            self._variables[obj_type] = Variable(obj_type.fullname,
                                                 upper=self._ubound)

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

    def _create_obj_roles_dict(self):
        """ Map each object type to the roles it plays. """
        for fact_type in self._model.fact_types:
            for role in fact_type.roles:
                obj = role.player
                self._obj_roles[obj] = self._obj_roles.get(obj, []) + [role]

    def _create_inequalities(self):
        """ Generate system of inequalities based on rules in Smaragdakis and
            McGill. """

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

        # Create inequalities for implicit disjunctive constraint
        for obj in self._model.object_types:
            role_seq = self._obj_roles.get(obj)
            if obj.independent == False and role_seq != None:
                obj_var = self._variables[obj]
                role_vars = [self._variables[role] for role in role_seq]
                self._add(Inequality(lhs=obj_var, rhs=Sum(role_vars)))

    def _create_value_inequality(self, cons):
        """ Value constraint inequality. """
        obj_var = self._variables[cons.covers[0]]
        self._add(Inequality(lhs=obj_var, rhs=Constant(cons.size)))

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

