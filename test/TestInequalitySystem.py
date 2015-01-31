##############################################################################
# Package: ormpy
# File:    TestInequalitySystem.py
# Author:  Matthew Nizol
##############################################################################

""" This file contains unit tests for the lib.InequalitySystem module. """

from unittest import TestCase

import sys

import lib.InequalitySystem as IneqSys
from lib.InequalitySystem import _VariableStatus

class TestInequalitySystem(TestCase):
    """ Unit tests for the InequalitySystem module. """

    def setUp(self):
        pass

    def test_create_default_variable(self):
        """ Test creation of a variable with default settings. """
        var = IneqSys.Variable('x')
        self.assertEquals(var.lower, 1)
        self.assertEquals(var.upper, sys.maxint)
        self.assertEquals(var.upper, var._candidate)
        self.assertEquals(var._status, _VariableStatus.valid)

    def test_create_custom_variable(self):
    	""" Test creation of a variable with custom settings. """
        var = IneqSys.Variable('x', lower=5, upper=10)
        self.assertEquals(var.lower, 5)
        self.assertEquals(var.upper, 10)
        self.assertEquals(var.upper, var._candidate)
        self.assertEquals(var._status, _VariableStatus.valid)

    def test_constant(self):
        """ Test creation of a constant. """
        cons = IneqSys.Constant(36)
        self.assertEquals(cons.name, "36")
        self.assertEquals(cons.lower, 36)
        self.assertEquals(cons.upper, 36)
        self.assertEquals(cons.result(), 36)
        self.assertEquals(cons.tostring(), "36")

    def test_change_candidate(self):
    	""" Test change to candidate value. """
        var = IneqSys.Variable('x', lower=5, upper=10)
        var.declare_less_than(7)
        self.assertEquals(var._candidate, 7)
        var.update()
        self.assertEquals(var.upper, 7)
        self.assertEquals(var._status, _VariableStatus.valid)
        self.assertFalse(var.is_stable())
        self.assertFalse(var.is_invalid())

    def test_stable(self):
        """ Test a change to candidate value that leaves bounds unchanged. """
        var = IneqSys.Variable('x', lower=5, upper=10)
        var.declare_less_than(11)
        self.assertEquals(var._candidate, 10) # Unchanged
        var.update()
        self.assertEquals(var.upper, 10)
        self.assertEquals(var._status, _VariableStatus.stable)
        self.assertTrue(var.is_stable())

        
    def test_invalid(self):
        """ Test a change to candidate value that invalidates bounds. """
        var = IneqSys.Variable('x', lower=5, upper=10)
        var.declare_less_than(4)
        var.update()
        self.assertEquals(var.upper, 4)
        self.assertEquals(var._status, _VariableStatus.invalid)
        self.assertTrue(var.is_invalid())

    def test_sum_empty(self):
        """ Test an empty Sum class. """
        sum1 = IneqSys.Sum([])
        self.assertEquals(sum1.result(), None)
        self.assertEquals(sum1.tostring(), "")

    def test_sum(self):
        """ Test a normal Sum class. """
        x = IneqSys.Variable('x', upper=5)
        y = IneqSys.Variable('y', upper=7)
        sum1 = IneqSys.Sum([x, y])
        self.assertEquals(sum1.result(), 12)
        self.assertEquals(sum1.tostring(), "x + y")

    def test_product_empty(self):
        """ Test an empty Product class. """
        prod1 = IneqSys.Product([])
        self.assertEquals(prod1.result(), None)
        self.assertEquals(prod1.tostring(), "")

    def test_product(self):
        """ Test a normal Product class. """
        x = IneqSys.Variable('x', upper=5)
        y = IneqSys.Variable('y', upper=7)
        prod1 = IneqSys.Product([x, y])
        self.assertEquals(prod1.result(), 35)
        self.assertEquals(prod1.tostring(), "x * y")

    def test_default_inequality(self):
        """ Test an inequality with default settings. """
        x = IneqSys.Variable('x', upper=100)
        y = IneqSys.Variable('y', upper=50)
        z = IneqSys.Variable('z', upper=20)
       
        ineq = IneqSys.Inequality(lhs=x, rhs=IneqSys.Sum([y, z]))
        self.assertEquals(ineq._coeff, 1)
        self.assertEquals(ineq.tostring(), "x <= y + z")

        ineq.evaluate()
        x.update()
        self.assertEquals(x.upper, 70)
        self.assertEquals(x._status, _VariableStatus.valid)
        
     
    def test_inequality(self):
        """ Test an inequality with custom coefficient. """
        x = IneqSys.Variable('x', upper=100, lower=10)
        y = IneqSys.Variable('y', upper=50)
        z = IneqSys.Variable('z', upper=20)
       
        ineq = IneqSys.Inequality(coeff=10, lhs=x, rhs=IneqSys.Sum([y, z]))
        self.assertEquals(ineq._coeff, 10)
        self.assertEquals(ineq.tostring(), "10 * x <= y + z") 

        ineq.evaluate()
        x.update()
        self.assertEquals(x.upper, 7)
        self.assertTrue(x.is_invalid())

    def test_add_inequality(self):
        """ Test adding an inequality to the system. """
        sys = IneqSys.InequalitySystem()
        x = IneqSys.Variable('x')
        y = IneqSys.Variable('y')
        z = IneqSys.Variable('z')
        q = IneqSys.Inequality(lhs=x, rhs=IneqSys.Sum([y, z]))
        sys.add(q)
        
        self.assertItemsEqual(sys, [q])
        self.assertDictEqual(sys._variables, {'x': x, 'y': y, 'z': z})

    def test_add_inequalities_with_dupe_vars (self):
        """ Test adding two inequalities to the system with overlapping vars."""
        sys = IneqSys.InequalitySystem()
        w = IneqSys.Variable('w')
        x = IneqSys.Variable('x')
        y = IneqSys.Variable('y')
        z = IneqSys.Variable('z')
        p = IneqSys.Inequality(lhs=w, rhs=IneqSys.Sum([x, z]))
        q = IneqSys.Inequality(lhs=x, rhs=IneqSys.Sum([y, z, w]))
        sys.add(p)
        sys.add(q)
        
        self.assertItemsEqual(sys, [p, q])
        self.assertDictEqual(sys._variables, {'w': w, 'x': x, 'y': y, 'z': z})
       
    def test_simple_sat_system(self):
        """ Test a simple satisfiable system. """
        sys = IneqSys.InequalitySystem()

        a = IneqSys.Variable('a', upper=50)
        b = IneqSys.Variable('b', lower=20)
        c = IneqSys.Variable('c')

        p = IneqSys.Inequality(lhs=b, rhs=IneqSys.Sum([a]))
        q = IneqSys.Inequality(lhs=c, rhs=IneqSys.Product([a, b]))

        sys.add(p)
        sys.add(q)
        solution = sys.solve(debug=True) # Debug on to achieve coverage

        self.assertEquals(solution['a'].lower, 1)
        self.assertEquals(solution['a'].upper, 50)
        self.assertEquals(solution['b'].lower, 20)
        self.assertEquals(solution['b'].upper, 50)
        self.assertEquals(solution['c'].lower, 1)
        self.assertEquals(solution['c'].upper, 2500)

    def test_simple_sat_system2(self):
        """ Test a simple satisfiable system #2. """
        sys1 = IneqSys.InequalitySystem()

        a = IneqSys.Variable('a')
        b = IneqSys.Variable('b')

        p = IneqSys.Inequality(lhs=a, rhs=IneqSys.Sum([a, b]))

        sys1.add(p)
        solution = sys1.solve()

        self.assertEquals(solution['a'].upper, sys.maxint)
        self.assertEquals(solution['b'].upper, sys.maxint)

    def test_simple_sat_system3(self):
        """ Test a simple satisfiable system #3 (with product). """
        sys1 = IneqSys.InequalitySystem()

        a = IneqSys.Variable('a', upper=20)
        b = IneqSys.Variable('b', upper=3)
        c = IneqSys.Variable('c', upper=5)
        d = IneqSys.Variable('d', upper=2)

        p = IneqSys.Inequality(lhs=a, rhs=IneqSys.Product([b, c]))
        q = IneqSys.Inequality(coeff=6, lhs=c, rhs=IneqSys.Product([d, a]))

        sys1.add(p)
        sys1.add(q)
        solution = sys1.solve(debug=True)

        self.assertEquals(solution['a'].upper, 15)
        self.assertEquals(solution['b'].upper, 3)
        self.assertEquals(solution['c'].upper, 5)
        self.assertEquals(solution['d'].upper, 2)

    def test_simple_unsat_system(self):
        """ Test a simple unsatisfiable system. """
        sys = IneqSys.InequalitySystem()

        a = IneqSys.Variable('a')
        b = IneqSys.Variable('b')

        p = IneqSys.Inequality(coeff=2, lhs=a, rhs=IneqSys.Sum([b]))
        q = IneqSys.Inequality(lhs=b, rhs=IneqSys.Sum([a]))

        sys.add(p)
        sys.add(q)
        solution = sys.solve(debug=True) # Debug on to achieve coverage

        self.assertEquals(solution, None)
        self.assertEquals(a.upper, 0)
        self.assertEquals(a.lower, 1)
  
    def test_simple_unsat_system2(self):
        """ Test a simple unsatisfiable system #2 (with product). """
        sys1 = IneqSys.InequalitySystem()

        a = IneqSys.Variable('a', upper=20)
        b = IneqSys.Variable('b', upper=3)
        c = IneqSys.Variable('c', upper=5)
        d = IneqSys.Variable('d', upper=2)

        p = IneqSys.Inequality(lhs=a, rhs=IneqSys.Product([b, c]))
        q = IneqSys.Inequality(coeff=10, lhs=c, rhs=IneqSys.Product([d, a]))

        sys1.add(p)
        sys1.add(q)
        solution = sys1.solve()

        self.assertEquals(solution, None)

    def test_unsat_system_from_paper(self):
        """ Test an unsatisfiable system of inequalities from Smaragdakis
            (Fig 9a). """
        sys = IneqSys.InequalitySystem()

        # Two object types related by a binary fact type
        obj1 = IneqSys.Variable("obj1")
        obj2 = IneqSys.Variable("obj2")
        rol1 = IneqSys.Variable("rol1")
        rol2 = IneqSys.Variable("rol2")
        fact = IneqSys.Variable("fact")

        # Constants
        cons1 = IneqSys.Variable("con1", lower=1000000, upper=1000000)
        cons2 = IneqSys.Variable("con2", lower=2, upper=2)

        # Inequalities that represent Smaragdakis' rules

        # Cardinality: # >= 1000000 for obj1, # <= 2 for obj2
        sys.add(IneqSys.Inequality(lhs=cons1, rhs=IneqSys.Sum([obj1])))
        sys.add(IneqSys.Inequality(lhs=obj2, rhs=IneqSys.Sum([cons2])))

        # Role 1 is mandatory
        sys.add(IneqSys.Inequality(lhs=obj1, rhs=IneqSys.Sum([rol1])))

        # Simple uniqueness constraints
        sys.add(IneqSys.Inequality(lhs=fact, rhs=IneqSys.Sum([rol1])))
        sys.add(IneqSys.Inequality(lhs=fact, rhs=IneqSys.Sum([rol2])))

        # Semantics of roles        
        sys.add(IneqSys.Inequality(lhs=rol1, rhs=IneqSys.Sum([obj1])))
        sys.add(IneqSys.Inequality(lhs=rol1, rhs=IneqSys.Sum([fact])))
        sys.add(IneqSys.Inequality(lhs=rol2, rhs=IneqSys.Sum([fact])))
        sys.add(IneqSys.Inequality(lhs=rol2, rhs=IneqSys.Sum([obj2])))

        # Solve the system and assert that there is no solution
        solution = sys.solve()
        self.assertEquals(solution, None)
        self.assertEquals(cons1.lower, 1000000)
        self.assertEquals(cons1.upper, 2)

    def test_unsat_system_from_paper2(self):
        """ Test an unsatisfiable system of inequalities from Smaragdakis
            (Fig 9b). """
        sys = IneqSys.InequalitySystem()

        # Two object types related by a binary fact type
        obj1 = IneqSys.Variable("obj1", upper=50)
        obj2 = IneqSys.Variable("obj2", upper=2)
        rol1 = IneqSys.Variable("rol1", upper=50)
        rol2 = IneqSys.Variable("rol2", upper=50)
        fact = IneqSys.Variable("fact", upper=50)

        # Constant
        con3 = IneqSys.Variable("con3", lower=3, upper=3)

        # Semantics of roles        
        sys.add(IneqSys.Inequality(lhs=rol1, rhs=IneqSys.Sum([obj1])))
        sys.add(IneqSys.Inequality(lhs=rol1, rhs=IneqSys.Sum([fact])))
        sys.add(IneqSys.Inequality(lhs=rol2, rhs=IneqSys.Sum([fact])))
        sys.add(IneqSys.Inequality(lhs=rol2, rhs=IneqSys.Sum([obj2])))

        # Frequency constraint
        sys.add(IneqSys.Inequality(lhs=fact, rhs=IneqSys.Product([con3, rol1])))
        sys.add(IneqSys.Inequality(coeff=3, lhs=rol1, rhs=IneqSys.Sum([fact])))

        # Uniqueness
        sys.add(IneqSys.Inequality(lhs=fact, rhs=IneqSys.Product([rol1, rol2])))

        # Disjunctive mandatory
        sys.add(IneqSys.Inequality(lhs=obj1, rhs=IneqSys.Sum([rol1])))
        sys.add(IneqSys.Inequality(lhs=obj2, rhs=IneqSys.Sum([rol2])))
        
        # Solve the system
        solution = sys.solve()
        self.assertEquals(solution, None)
        self.assertEquals(rol1.upper, 0)

    def test_unsat_system_from_paper3(self):
        """ Test an unsatisfiable system of inequalities from Smaragdakis
            (Fig 9c). """
        sys = IneqSys.InequalitySystem()

        # Two object types related by two binary fact types
        obj1 = IneqSys.Variable("obj1", upper=20)
        obj2 = IneqSys.Variable("obj2", upper=20)
        rol11 = IneqSys.Variable("rol11", upper=20)
        rol12 = IneqSys.Variable("rol12", upper=20)
        rol21 = IneqSys.Variable("rol21", upper=20)
        rol22 = IneqSys.Variable("rol22", upper=20)
        fact1 = IneqSys.Variable("fact1", upper=20)
        fact2 = IneqSys.Variable("fact2", upper=20)

        # Constant
        con2 = IneqSys.Variable("con2", lower=2, upper=2)

        # Semantics of roles        
        sys.add(IneqSys.Inequality(lhs=rol11, rhs=IneqSys.Sum([obj1])))
        sys.add(IneqSys.Inequality(lhs=rol11, rhs=IneqSys.Sum([fact1])))
        sys.add(IneqSys.Inequality(lhs=rol21, rhs=IneqSys.Sum([fact1])))
        sys.add(IneqSys.Inequality(lhs=rol21, rhs=IneqSys.Sum([obj2])))

        sys.add(IneqSys.Inequality(lhs=rol12, rhs=IneqSys.Sum([obj1])))
        sys.add(IneqSys.Inequality(lhs=rol12, rhs=IneqSys.Sum([fact2])))
        sys.add(IneqSys.Inequality(lhs=rol22, rhs=IneqSys.Sum([fact2])))
        sys.add(IneqSys.Inequality(lhs=rol22, rhs=IneqSys.Sum([obj2])))

        # Uniqueness of fact types
        sys.add(IneqSys.Inequality(lhs=fact1, rhs=IneqSys.Product([rol11, rol21])))
        sys.add(IneqSys.Inequality(lhs=fact2, rhs=IneqSys.Product([rol12, rol22])))

        # Disjunctive mandatory
        sys.add(IneqSys.Inequality(lhs=obj1, rhs=IneqSys.Sum([rol11, rol12])))
        sys.add(IneqSys.Inequality(lhs=obj2, rhs=IneqSys.Sum([rol21, rol22])))

        # Simple uniqueness
        sys.add(IneqSys.Inequality(lhs=fact1, rhs=IneqSys.Sum([rol21])))
        sys.add(IneqSys.Inequality(lhs=fact2, rhs=IneqSys.Sum([rol12])))

        # Simple mandatory
        sys.add(IneqSys.Inequality(lhs=obj1, rhs=IneqSys.Sum([rol11])))
        sys.add(IneqSys.Inequality(lhs=obj2, rhs=IneqSys.Sum([rol22])))

        # Frequency
        sys.add(IneqSys.Inequality(lhs=fact1, rhs=IneqSys.Product([con2, rol11])))
        sys.add(IneqSys.Inequality(coeff=2, lhs=rol11, rhs=IneqSys.Sum([fact1])))

        solution = sys.solve()
        self.assertEquals(solution, None)
        self.assertEquals(rol11.upper, 0)

        
