##############################################################################
# Package: ormpy
# File:    InequalitySystem.py
# Author:  Matthew Nizol
##############################################################################

""" Module for creating and solving systems of inequalities of the simple
    form permitted by ORM--.  Specifically, all inequalities are of one of
    two forms:

    * c * x <= y_1 + y_2 + ... + y_n
    * c * x <= y_1 * y_2 * ... * y_n
"""

import operator, sys

class Expression(list):
    """ A restricted expression over a list of variables.  The
        expression is restricted in the sense that it permits
        only one type of operator --- e.g. x + y + z, or
        x * y * x.  This is an abstract class and should not
        be instantiated directly.  Subclasses modify the
        self._op and self._sym attributes to define the expression
        type.

        :param var_list: list of :class:`lib.InequalitySystem.Variable`"""

    def __init__(self, var_list):
        super(Expression, self).__init__(var_list)
        self._op = None  #: Set to an operator.xx method
        self._sym = None #: Set to an appropriate symbol for _op

    def result(self):
        """ Evaluates the operator on the list of variables. """
        if len(self) > 0:
            expression = [var.upper for var in self]
            return reduce(self._op, expression)
        else:
            return None

    def tostring(self):
        """ Returns the expression as a string for display. """
        expression = sorted([var.name for var in self])
        return self._sym.join(expression)


class _VariableStatus(object):
    """ Enumeration of variable statuses. """
    stable = 0 #: Variable's bounds did not change during an update.
    valid = 1 #: Variable is in valid state, but not yet stable.
    invalid = 2 #: Bounds have crossed: lower bound > upper bound

class Variable(Expression):
    """ Represents a variable with an upper and lower bound. """

    def __init__(self, name, lower=1, upper=sys.maxint):
        super(Variable, self).__init__([])
        self.name = name    #: Variable name
        self.lower = lower  #: Lower bound for the variable
        self.upper = upper  #: Upper bound for the variable

	    #: Lowest upper bound observed while evaluating inequalities
        self._candidate = upper
        self._status = _VariableStatus.valid #: Status of the variable

    def result(self):
        """ Override Expression.result. """
        return self.upper

    def tostring(self):
        """ Return variable upper bound as a string. """
        return str(self.name)

    def declare_less_than(self, value):
        """ Update candidate if it is greater than value. Called whenever a
            variable's upper bound is potentially changed by evaluating an
            inequality. """
        self._candidate = min(value, self._candidate)

    def update(self):
        """ Update upper bound and status based on candidate value.
            Called for each variable in the system after a complete iteration
            of evaluating the inequalities in the system.  """

        if self._candidate < self.lower:
            self.upper = self._candidate
            self._status = _VariableStatus.invalid
        elif self._candidate < self.upper:
            self.upper = self._candidate
            self._status = _VariableStatus.valid
        else:
            self._status = _VariableStatus.stable

    def is_stable(self):
        """ Returns true if variable is in a stable state. """
        return self._status == _VariableStatus.stable

    def is_invalid(self):
        """ Returns true if variable bounds are invalid. """
        return self._status == _VariableStatus.invalid


class Constant(Variable):
    """ Represents a constant. """
    def __init__(self, value):
        super(Constant, self).__init__(str(value), lower=value, upper=value)

class Sum(Expression):
    """ Represents a sum of variables. """

    def __init__(self, thelist):
        super(Sum, self).__init__(thelist)
        self._op = operator.add
        self._sym = ' + '

class Product(Expression):
    """ Represents a product of variables. """

    def __init__(self, thelist):
        super(Product, self).__init__(thelist)
        self._op = operator.mul
        self._sym = ' * '

    def tostring(self):
        """ Returns the expression as a string for display. """
        is_unity = lambda x: isinstance(x, Constant) and x.upper == 1
        expression = sorted([var.name for var in self if not is_unity(var)])
        return self._sym.join(expression)

class Inequality(object):
    """ An inequality of the form:

        coeff * lhs <= rhs

        where rhs is one of the following forms:

        * y_1 + y_2 + ... + y_n [i.e. a :class:`lib.InequalitySystem.Sum`]
        * y_1 * y_2 * ... * y_n [i.e. a :class:`lib.InequalitySystem.Product`]

        :param lhs: Left-hand side.  A :class:`lib.InequalitySystem.Variable`
        :param rhs: Right-hand side.  A :class:`lib.InequalitySystem.Expression`
        :param coeff: Coefficient on left-hand side of inequality.
    """

    def __init__(self, lhs, rhs, coeff=1):
        #: Coefficient on left-hand side of inequality.
        self._coeff = coeff

        #: Left hand side of the inequality.  A variable.
        self._lhs = lhs

        #: Right hand side of the inequality.  A Sum or Product.
        self._rhs = rhs

    def variables(self):
        """ Returns the list of :class:`lib.InequalitySystem.Variable`
            in the inequality. """
        return list([self._lhs]) + self._rhs # list is supertype of RHS

    def evaluate(self):
        """ Evaluates right-hand side of inequality and updates candidate
            value of left-hand side. """
        candidate = int(self._rhs.result() / self._coeff)
        self._lhs.declare_less_than(candidate)

    def tostring(self):
        """ Returns inequality as a string for display or debugging. """
        lhs = self._lhs.name

        if self._coeff != 1:
            lhs = str(self._coeff) + " * " + lhs

        return lhs + " <= " + self._rhs.tostring()

    def __eq__(self, other):
        """ Return True iff inequalities have the same string representation. """
        return self.tostring() == other.tostring()

class InequalitySystem(list):
    """ A system of :class:`lib.InequalitySystem.Inequality` inequalities. """

    def __init__(self):
        super(InequalitySystem, self).__init__([])

        self._variables = {}  #: Dictionary of variables in the system
        self._stable = False  #: Is the system stable?
        self._valid = True    #: Is the system satisfiable?

    def add(self, inequality):
        """ Add an inequality to the system.

            :param inequality: A :class:`lib.InequalitySystem.Inequality` """
        if inequality not in self:
            self.append(inequality)

        # Add variables in the expression to the variables dictionary
        for var in inequality.variables():
            self._variables[var.name] = var

    def solve(self, debug=False):
        """ Solve the system.  If there is a solution, returns a dictionary
            whose keys are the names of the variables in the system and
            whose values are the corresponding values in the solution.
            If there is no solution, returns None."""

        iteration = 0

        # Loop until either the system is not valid (it is unsatisfiable) or
        # the system is stable (we have a solution).
        while self._valid and not self._stable:
            iteration += 1
            if debug:
                print "Iteration: ", iteration

            # Evaluate each inequality in the system
            for ineq in self:
                ineq.evaluate()

            num_stable = 0 # Number of stable variables in the system

            # Update the upper bounds of all variables in the system based
            # on the evaluated inequalities, and then check the resulting
            # status of each variable.
            for var in self._variables.itervalues():
                var.update()

                if debug:
                    print var.name, ": ", var.upper

                if var.is_stable():
                    num_stable += 1
                if var.is_invalid():
                    self._valid = False
                    break # One invalid variable implies an unsatisfiable sys.

            # If every variable in the system is stable, we have a solution
            if num_stable == len(self._variables):
                self._stable = True

        if self._valid:
            if debug:
                print "Found solution."
            return {k: v.upper for k, v in self._variables.iteritems()}
        else:
            if debug:
                print "System has no solution."
            return None


