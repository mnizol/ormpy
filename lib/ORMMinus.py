##############################################################################
# Package: ormpy
# File:    ORMMinus.py
# Author:  Matthew Nizol
##############################################################################

""" Module for creating and solving systems of inequalities of the simple
    form permitted by ORM--.  Specifically, all inequalities are of one of
    two forms:

    * c * x <= y_1 + y_2 + ... + y_n 
    * c * x <= y_1 * y_2 * ... * y_n
"""

import operator
import sys
from datetime import datetime, date, time

import lib.ObjectType as ObjectType
import lib.FactType as FactType
import lib.Constraint as Constraint

class Variable(object):
    """ A variable in a system of inequalities. """

    def __init__(self, element, ubound=None):
        """ Initialize a variable from a model element. """

        self.element = element #: Model element this variable represents
        self.name = element.fullname #: Variable name

        #: Variable upper bound
        if ubound is not None:
            self.ubound = ubound
        elif isinstance(element, ObjectType.ValueType):
            #self.ubound = element.data_type.size 
            self.ubound = float('inf')
        else:
            self.ubound = float('inf') # Theoretically unbounded
        
    def result(self):
        """ Returns upper bound when variable is treated as expression. """
        return self.ubound

    def tostring(self):
        """ Returns a string representation of the variable's value. """
        return str(self.ubound)

class Product(list):
    """ Represents a product of variables. """

    def __init__(self, coeff=1):
        """ Initialize. """
        self.coeff = coeff

    def result(self):
        """ Computes the product of the variables. """
        expression = [self.coeff] + [var.ubound for var in self]
        return reduce(operator.mul, expression)
    
    def tostring(self):
        """ Returns the expression as a string for display. """
        expression = [str(self.coeff)] + [var.name for var in self]
        return " * ".join(expression)           

class Sum(list):
    """ Represents a sum of variables. """

    def result(self):
        """ Computes the sum of the variables. """
        return sum([var.ubound for var in self])
    
    def tostring(self):
        """ Returns the expression as a string for display. """
        return " + ".join([var.name for var in self])
        
class Inequality(object):
    """ An inequality. """

    def __init__(self, lhs=None, rhs=None):
        #: Left hand side of the inequality.  A variable.
        self.lhs = lhs

        #: Right hand side of the inequality.  A Sum or Product.
        self.rhs = rhs 

    def result(self):
        return self.rhs.result()

    def display(self):
        print self.lhs.name, "<=", self.rhs.tostring()


class InequalitySystem(list):
    """ A system of inequalities. """
     
    def __init__(self):
        self.variables = {} #: Dictionary of variable by model element id

    def add(self, inequality):
        """ Add an inequality to the system. """
        self.append(inequality)
        self.variables[inequality.lhs.element] = inequality.lhs

    def update(self):
        """ Update all variables in the system. """
        for ineq in self:
            result = ineq.result()
            ineq.lhs.ubound = min(ineq.lhs.ubound, result)

    def display(self):
        for ineq in self:
            ineq.display()

    def showvars(self):
        varset = set([ineq.lhs for ineq in self])
        for var in varset:
            print var.name, "<=", var.ubound

def main():
    from lib.NormaLoader import NormaLoader
    model = NormaLoader("test/data/canonical_example.orm").model

    sys = InequalitySystem()
    maxvar = Variable(ObjectType.ValueType(name="MAX"), ubound=50)

    for object_type in model.object_types:
        var = Variable(object_type)
        sys.add(Inequality(lhs = var, rhs = maxvar))

    for fact_type in model.fact_types:
        fact_var = Variable(fact_type)
        sys.add(Inequality(lhs = var, rhs = maxvar))

        for role in fact_type.roles:
            var = Variable(role)
            sys.add(Inequality(lhs = var, rhs = maxvar))
            sys.add(Inequality(lhs = var, rhs = fact_var))
            sys.add(Inequality(lhs = var, rhs = sys.variables[role.player]))

    sys.display()
    print "="*50
    sys.showvars()

    sys.update()
    print "="*50
    print "After Update:"
    sys.showvars()

if __name__ == "__main__":
    main()

 
