##############################################################################
# Package: ormpy
# File:    TestConstraint.py
# Author:  Matthew Nizol
##############################################################################

""" This file contains unit tests for the lib.TestConstraint class """

from unittest import TestCase

import lib.Constraint as Constraint
from lib.ObjectType import ObjectType
from lib.FactType import Role

class TestConstraint(TestCase):
    """ Unit tests for the Constraint module. """

    def setUp(self):
        pass

    def test_add_object_type(self):
        """ Test the addition of an object type to a constraint. """
        cons = Constraint.Constraint(uid="1", name="C1")
        cons.cover(ObjectType(uid="2", name="O1"))
        self.assertEquals(cons.covers[0].name, "O1")

    def test_remove_object_type(self):
        """ Test the removal of an object type from a constraint. """
        cons = Constraint.Constraint(uid="1", name="C1")
        obj = ObjectType(uid="2", name="O1")
        cons.cover(obj)
        self.assertEquals(cons.covers[0], obj)

        # Unsuccessful uncover
        cons.uncover("Dummy")
        self.assertEquals(cons.covers[0], obj)

        # Successful uncover
        cons.uncover(obj)
        self.assertItemsEqual(cons.covers, [])

    def test_vc_add_enum(self):
        """ Test the addition of enumerated items to a value constraint."""
        cons = Constraint.ValueConstraint(uid="1", name="VC1")
        cons.add_range("Dog", "Dog")
        cons.add_range("Cat")
        cons.add_range(1.35)
        cons.add_range(9)
        self.assertItemsEqual(cons.domain.draw(4), ["Dog","Cat", 1.35,9])
        self.assertEquals(cons.size, 4)

    def test_vc_bad_enum(self):
        """ Test invalid enumerations in value constraint. """
        cons = Constraint.ValueConstraint()
        with self.assertRaises(Constraint.ValueConstraintError) as ex:
            cons.add_range("Dog", max_open=True)
        self.assertEquals(ex.exception.message, 
            "Value constraints only support integer ranges")

        with self.assertRaises(Constraint.ValueConstraintError) as ex:
            cons.add_range("Dog", min_open=True)
        self.assertEquals(ex.exception.message, 
            "Value constraints only support integer ranges")

    def test_vc_bad_ranges(self):
        """ Test a value constraint with a range of non-integers. """
        cons = Constraint.ValueConstraint()
        with self.assertRaises(Constraint.ValueConstraintError) as ex:
            cons.add_range("1.45", "5.6")
        self.assertEquals(ex.exception.message,
            "Value constraints only support integer ranges")

    def test_vc_int_ranges(self):
        """ Test the addition of value ranges to a value constraint 
            with default inclusion values. """
        cons = Constraint.ValueConstraint(uid="1", name="VC1")
        cons.add_range("1", "4")
        self.assertItemsEqual(cons.domain.draw(10), [1,2,3,4])
        self.assertEquals(cons.size, 4)
        cons.add_range("3", "5")
        self.assertItemsEqual(cons.domain.draw(10), [1,2,3,4,5])

    def test_vc_int_ranges_open(self):
        """ Test the addition of value ranges to a value constraint 
            with explicit inclusion values. """
        cons = Constraint.ValueConstraint(uid="1", name="VC1")
        cons.add_range("1", "2", min_open=True)
        cons.add_range("5", "10", max_open=True)
        cons.add_range("11", "13", min_open=True, max_open=True)
        self.assertItemsEqual(cons.domain.draw(10), [2,5,6,7,8,9,12])
        self.assertEquals(cons.size, 7)

    def test_vc_invalid_range(self):
        """ Test a value constraint with an invalid integer range. """
        cons = Constraint.ValueConstraint()
        with self.assertRaises(Constraint.ValueConstraintError) as ex:
            cons.add_range("12", "13", min_open=True, max_open=True)
        self.assertEquals(ex.exception.message,
            "The range of the value constraint is invalid")

        with self.assertRaises(Constraint.ValueConstraintError) as ex:
            cons.add_range("3", "2")
        self.assertEquals(ex.exception.message,
            "The range of the value constraint is invalid")

    def test_vc_too_large(self):
        """ Test a value constraint range that is too large. """
        cons = Constraint.ValueConstraint()
        with self.assertRaises(Constraint.ValueConstraintError) as ex:
            cons.add_range(0, Constraint.ValueConstraint.MAX_SIZE)
        self.assertEquals(ex.exception.message,
            "The range of the value constraint is too large")

        cons = Constraint.ValueConstraint()
        with self.assertRaises(Constraint.ValueConstraintError) as ex:
            cons.add_range(75, float('inf'))
        self.assertEquals(ex.exception.message,
            "Value constraints only support integer ranges")       

    def test_add_subset_roles(self):
        """ Test adding subset roles to subset constraint. """
        cons = Constraint.SubsetConstraint(uid="1", name="S1")
        role = Role(uid="R1", name="R1")
        cons.cover_subset(role)
        self.assertIs(cons.covers[0], role)
        self.assertIs(cons.subset[0], role)

    def test_add_superset_roles(self):
        """ Test adding superset roles to subset constraint. """
        cons = Constraint.SubsetConstraint(uid="1", name="S1")
        role = Role(uid="R1", name="R1")
        cons.cover_superset(role)
        self.assertIs(cons.covers[0], role)
        self.assertIs(cons.superset[0], role)

    def test_of_type_with_hit(self):
        """ Test of_type method with non-empty result. """
        cons_set = Constraint.ConstraintSet()
        cons1 = Constraint.SubsetConstraint(uid="1", name="S1")
        cons2 = Constraint.ValueConstraint(uid="2", name="V1")
        cons3 = Constraint.SubsetConstraint(uid="3", name="S2")

        cons_set.add(cons1)
        cons_set.add(cons2)
        cons_set.add(cons3)
        
        actual = cons_set.of_type(Constraint.SubsetConstraint)
        expect = [cons1, cons3]
        self.assertItemsEqual(actual, expect)
        
    def test_of_type_without_hit(self):
        """ Test of_type method with empty result. """
        cons_set = Constraint.ConstraintSet()
        cons1 = Constraint.SubsetConstraint(uid="1", name="S1")
        cons2 = Constraint.ValueConstraint(uid="2", name="V1")
        cons3 = Constraint.SubsetConstraint(uid="3", name="S2")

        cons_set.add(cons1)
        cons_set.add(cons2)
        cons_set.add(cons3)
        
        actual = cons_set.of_type(Constraint.MandatoryConstraint)
        expect = []
        self.assertItemsEqual(actual, expect)

