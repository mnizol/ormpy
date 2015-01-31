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

    def check(self):
        """ Checks model for satisifiability.  Returns solution if satisfiable
            and None otherwise. """

        self._create_variables()
        self._create_obj_roles_dict()
        self._create_inequalities()
        return self._ineqsys.solve()

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

        # Create one variable for each frequency constraint
        for cons in self._model.constraints.of_type(FrequencyConstraint):
            self._variables[cons] = Variable(cons.fullname, upper=self._ubound)

            # Confirm constraints are not overlapping
            if len(set(cons.covers) & already_covered) > 0:
                raise Exception("Cannot run ORM- algorithm: " + cons.name +
                    " overlaps with another frequency constraint.")
            else:
                already_covered.update(cons.covers)

    def _create_obj_roles_dict(self):
        """ Map each object type to the roles it plays. """
        for fact_type in self._model.fact_types:
            for role in fact_type.roles:
                obj = role.player
                self._obj_roles[obj] = self._obj_roles.get(obj, []) + [role]

    def _create_inequalities(self):
        """ Generate system of inequalities based on rules in Smaragdakis and
            McGill. """

        add = self._ineqsys.add # Simplify code to add inequalities to system

        # Create inequalities to represent role semantics
        for fact_type in self._model.fact_types:
            for role in fact_type.roles:
                role_var = self._variables[role]
                fact_var = self._variables[fact_type]
                obj_var = self._variables[role.player]

                add(Inequality(lhs=role_var, rhs=fact_var))
                add(Inequality(lhs=role_var, rhs=obj_var))

        # Create inequalities for value constraints
        for cons in self._model.constraints.of_type(ValueConstraint):
            obj_var = self._variables[cons.covers[0]]
            add(Inequality(lhs=obj_var, rhs=Constant(cons.size)))

        # Create inequalities for mandatory constraints
        for cons in self._model.constraints.of_type(MandatoryConstraint):
            role = cons.covers[0]
            role_var = self._variables[role]
            obj_var = self._variables[role.player]
            add(Inequality(lhs=obj_var, rhs=role_var))

            # Raise exception for disjunctive mandatory constraints
            if cons.simple == False:
                raise Exception("Cannot run ORM- algorithm: " + cons.name +
                    " is a non-simple mandatory constraint.")

        # Create inequalities for internal frequency constraints
        for cons in self._model.constraints.of_type(FrequencyConstraint):
            # Get variables that will be used in the inequalities
            role_seq = cons.covers
            role_vars = [self._variables[role] for role in role_seq]

            min_var = Constant(1.0 / cons.min_freq)
            max_var = Constant(cons.max_freq)

            fact_var = self._variables[role_seq[0].fact_type]
            freq_var = self._variables[cons]

            # Generate the four types of inequalities required by Smaragdakis
            add(Inequality(lhs=fact_var, rhs=Product([max_var, freq_var])))
            add(Inequality(lhs=freq_var, rhs=Product([min_var, fact_var])))
            add(Inequality(lhs=freq_var, rhs=Product(role_vars)))

            for role in role_seq:
                role_var = self._variables[role]
                add(Inequality(lhs=role_var, rhs=freq_var))

        # Create inequalities for implicit disjunctive constraint
        for obj in self._model.object_types:
            role_seq = self._obj_roles.get(obj)
            if obj.independent == False and role_seq != None:
                obj_var = self._variables[obj]
                role_vars = [self._variables[role] for role in role_seq]
                add(Inequality(lhs=obj_var, rhs=Sum(role_vars)))


