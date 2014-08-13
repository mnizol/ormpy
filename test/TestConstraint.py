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

    def test_add_ranges_default_open(self):
        """ Test the addition of value ranges to a value constraint 
            with default inclusion values. """
        cons = Constraint.ValueConstraint(uid="1", name="VC1")
        cons.add_range("1", "2")
        self.assertEquals(cons.ranges[0].min_value, "1")
        self.assertEquals(cons.ranges[0].max_value, "2")
        self.assertFalse(cons.ranges[0].min_open)
        self.assertFalse(cons.ranges[0].max_open)

    def test_add_ranges_explicit_open(self):
        """ Test the addition of value ranges to a value constraint 
            with explicit inclusion values. """
        cons = Constraint.ValueConstraint(uid="1", name="VC1")
        cons.add_range("1", "2", min_open=True)
        cons.add_range("5", "10", max_open=True)

        self.assertEquals(cons.ranges[0].min_value, "1")
        self.assertEquals(cons.ranges[0].max_value, "2")
        self.assertTrue(cons.ranges[0].min_open)
        self.assertFalse(cons.ranges[0].max_open)

        self.assertEquals(cons.ranges[1].min_value, "5")
        self.assertEquals(cons.ranges[1].max_value, "10")
        self.assertFalse(cons.ranges[1].min_open)
        self.assertTrue(cons.ranges[1].max_open)

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


